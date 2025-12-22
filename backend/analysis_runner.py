"""
Analysis runner module that integrates the CNN analysis pipeline with Cloudinary storage.
This can be called from the API to run analysis on entry videos.
"""
import sys
import os
import json
import tempfile
import shutil

# Add paths for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import pandas as pd
import numpy as np

from src.calibration import compute_pixel_to_cm_scale
from src.preprocess import read_video_frames
from src.segmentation import StreamSegmenter
from src.tracking import StreamTracker
from src.flow_estimation import FlowEstimator
from src.visualize import Visualizer
from src.utils import generate_clinical_report_plot
from src.ensemble import EnsembleAggregator
from cloudinary_service import upload_video, upload_image, upload_raw


def download_video(url: str, local_path: str) -> bool:
    """Download video from URL to local path."""
    import requests
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"Error downloading video: {e}")
        return False


def convert_to_browser_compatible(input_path: str, output_path: str) -> bool:
    """
    Convert video to browser-compatible format using FFmpeg.
    Uses H.264 codec which is universally supported by browsers.
    """
    import subprocess
    
    try:
        # Try to get FFmpeg from imageio-ffmpeg (bundled)
        try:
            import imageio_ffmpeg
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            ffmpeg_path = 'ffmpeg'  # Fallback to system FFmpeg
        
        # FFmpeg command to convert to H.264
        # -y: overwrite output
        # -i: input file
        # -c:v libx264: H.264 video codec
        # -preset fast: encoding speed/quality tradeoff
        # -crf 23: quality (lower = better, 23 is default)
        # -pix_fmt yuv420p: Required for browser compatibility
        # -movflags +faststart: optimize for web streaming
        # -an: No audio (original video has no audio)
        cmd = [
            ffmpeg_path, '-y',
            '-i', input_path,
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            '-movflags', '+faststart',
            '-an',
            output_path
        ]
        
        print(f"Converting video to browser format: {input_path} -> {output_path}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print(f"FFmpeg error: {result.stderr}")
            return False
            
        print(f"Video conversion successful: {output_path}")
        return True
        
    except subprocess.TimeoutExpired:
        print("FFmpeg conversion timed out")
        return False
    except FileNotFoundError:
        print("FFmpeg not found. Please install FFmpeg or imageio-ffmpeg.")
        return False
    except Exception as e:
        print(f"Video conversion error: {e}")
        return False


def process_single_video(video_path, output_dir, view_name="top", fps_override=None):
    """
    Runs the CV pipeline on a single video.
    Returns: dict with df, metrics, px_to_cm
    """
    if not video_path or not os.path.exists(video_path):
        print(f"[{view_name.upper()}] Video not found: {video_path}")
        return None
        
    print(f"[{view_name.upper()}] Starting Analysis: {video_path}")
    
    # Default calibration (no calibration image needed, use fallback)
    px_to_cm = 0.052  # Default fallback
        
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps_override: 
        fps = fps_override
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    
    if fps <= 0: 
        fps = 30
    
    # Resizing
    scale_factor = 1.0
    target_width = 640
    if width > target_width:
        scale_factor = width / target_width
        width = target_width
        height = int(height / scale_factor)
        px_to_cm *= scale_factor
        
    segmenter = StreamSegmenter()
    tracker = StreamTracker(px_to_cm)
    estimator = FlowEstimator()
    
    # Intermediate visualization
    out_vid_name = f"annotated_{view_name}.mp4"
    out_vid_path = os.path.join(output_dir, out_vid_name)
    visualizer = Visualizer(out_vid_path, fps, (width, height))
    
    frame_gen = read_video_frames(video_path, resize_shape=(width, height))
    
    for frame_idx, frame in frame_gen:
        mask = segmenter.process_frame(frame)
        contour = segmenter.get_stream_contour(mask)
        stats = tracker.process(frame, mask, contour, fps)
        
        timestamp = frame_idx / fps
        flow_val = estimator.update(stats['area_cm2'], stats['velocity_cm_s'], timestamp, frame_idx)
        
        visualizer.process_frame(frame, contour, flow_val, stats['velocity_cm_s'], stats['area_cm2'], frame_idx, None)
        
        if frame_idx % 60 == 0:
            print(f"[{view_name.upper()}] Frame {frame_idx}: {flow_val:.2f} ml/s")
            
    visualizer.release()
    
    # Get results
    df, metrics = estimator.get_results()
    
    return {'df': df, 'metrics': metrics, 'px_to_cm': px_to_cm, 'annotated_video': out_vid_path}


def run_analysis_for_entry(
    top_view_url: str = None,
    bottom_view_url: str = None,
    volume: float = None,
    entry_id: int = None
) -> dict:
    """
    Run analysis on entry videos and upload results to Cloudinary.
    
    Args:
        top_view_url: URL to top view video
        bottom_view_url: URL to bottom/side view video  
        volume: Manual voided volume in ml (optional)
        entry_id: Entry ID for organizing uploads
    
    Returns:
        dict with URLs for all generated files
    """
    result = {
        "annotated_video_url": None,
        "clinical_report_url": None,
        "flow_timeseries_url": None,
        "qmax_report_json": None,
        "success": False,
        "error": None
    }
    
    if not top_view_url and not bottom_view_url:
        result["error"] = "No video URLs provided"
        return result
    
    # Create temp directory for processing
    temp_dir = tempfile.mkdtemp(prefix=f"analysis_{entry_id}_")
    
    try:
        # Download videos
        top_video_path = None
        bottom_video_path = None
        
        if top_view_url:
            top_video_path = os.path.join(temp_dir, "top_video.mp4")
            if not download_video(top_view_url, top_video_path):
                top_video_path = None
                
        if bottom_view_url:
            bottom_video_path = os.path.join(temp_dir, "bottom_video.mp4")
            if not download_video(bottom_view_url, bottom_video_path):
                bottom_video_path = None
        
        if not top_video_path and not bottom_video_path:
            result["error"] = "Failed to download any videos"
            return result
        
        # Process videos
        top_result = None
        if top_video_path:
            top_result = process_single_video(top_video_path, temp_dir, "top")
            
        bottom_result = None
        if bottom_video_path:
            bottom_result = process_single_video(bottom_video_path, temp_dir, "bottom")
        
        # Ensemble aggregation
        print(">>> Running Ensemble Aggregation")
        aggregator = EnsembleAggregator()
        final_df, final_metrics = aggregator.process(top_result, bottom_result, volume)
        
        # Generate outputs
        csv_path = os.path.join(temp_dir, "flow_timeseries.csv")
        final_df.to_csv(csv_path, index=False)
        
        report_path = os.path.join(temp_dir, "qmax_report.json")
        final_metrics['inputs'] = {
            'top': top_view_url,
            'bottom': bottom_view_url,
            'volume_manual': volume
        }
        
        # Convert numpy types
        for k, v in final_metrics.items():
            if isinstance(v, (np.integer, np.floating)):
                final_metrics[k] = float(v)
                
        with open(report_path, 'w') as f:
            json.dump(final_metrics, f, indent=4)
        
        # Generate clinical report plot
        plot_path = os.path.join(temp_dir, "clinical_report.png")
        generate_clinical_report_plot(final_df, final_metrics, plot_path)
        
        # Upload to Cloudinary
        folder = f"dockothon/entries/{entry_id}" if entry_id else "dockothon/analysis"
        
        # Upload annotated video (use top if available, else bottom)
        annotated_video = None
        if top_result and 'annotated_video' in top_result:
            annotated_video = top_result['annotated_video']
        elif bottom_result and 'annotated_video' in bottom_result:
            annotated_video = bottom_result['annotated_video']
            
        if annotated_video and os.path.exists(annotated_video):
            # Convert to browser-compatible format (H.264)
            converted_video = os.path.join(temp_dir, "annotated_browser.mp4")
            if convert_to_browser_compatible(annotated_video, converted_video):
                # Upload the converted video
                upload_result = upload_video(converted_video, folder=f"{folder}/videos")
                result["annotated_video_url"] = upload_result.get("url")
            else:
                # Fallback: try uploading original (may not play in browser)
                print("Warning: Uploading original video (may not be browser-compatible)")
                upload_result = upload_video(annotated_video, folder=f"{folder}/videos")
                result["annotated_video_url"] = upload_result.get("url")
        
        # Upload clinical report image
        if os.path.exists(plot_path):
            upload_result = upload_image(plot_path, folder=f"{folder}/reports")
            result["clinical_report_url"] = upload_result.get("url")
        
        # Upload flow timeseries CSV
        if os.path.exists(csv_path):
            upload_result = upload_raw(csv_path, folder=f"{folder}/data")
            result["flow_timeseries_url"] = upload_result.get("url")
        
        # Store JSON directly (as string)
        result["qmax_report_json"] = json.dumps(final_metrics)
        result["success"] = True
        
        print(f"\n=== Analysis Complete ===")
        print(f"Final Qmax: {final_metrics.get('Qmax', 0):.2f} ml/s")
        print(f"Voided Volume: {final_metrics.get('Voided_Volume', 0):.2f} ml")
        
    except Exception as e:
        result["error"] = str(e)
        print(f"Analysis error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup temp directory
        try:
            shutil.rmtree(temp_dir)
        except:
            pass
    
    return result
