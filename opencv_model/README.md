# Uroflow Computer Vision Analysis System

A computer vision-based uroflow analysis system that uses advanced stream segmentation techniques to measure urinary flow rates from video recordings.

## Features

### Advanced Stream Segmentation
- **ROI Locking**: Automatically locks onto the urine stream position and tracks it throughout the video
- **Width-Based Gating**: Removes thick objects (hands, body parts) while preserving the thin stream
- **Geometric Filtering**: Uses aspect ratio analysis to distinguish stream from background artifacts
- **Vertical Dilation**: Connects broken stream fragments for continuous detection

### Flow Analysis
- **Qmax Calculation**: Peak flow rate measurement
- **Clinical Metrics**: Hesitancy, Flow Time, Voiding Time, Average Flow Rate, Time to Qmax
- **Volume Normalization**: Adjusts flow curve to match manually measured voided volume
- **Temporal Smoothing**: Reduces noise while preserving flow dynamics

### Multi-View Support
- **Dual-View Ensemble**: Combines top and side camera views
- **Confidence Weighting**: Automatically weights each view based on detection quality
- **Synchronized Fusion**: Aligns and merges signals from multiple perspectives

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Analysis (Single View)

```bash
python scripts/run_analysis.py \
    --top-video data/top.mp4 \
    --calibration-image data/top.png \
    --output-dir outputs/ \
    --volume 369
```

### Dual-View Ensemble Analysis

```bash
python scripts/run_analysis.py \
    --top-video data/top.mp4 \
    --side-video data/side.mp4 \
    --calibration-image data/top.png \
    --output-dir outputs_ensemble/ \
    --volume 369
```

## Outputs

Generated files in the output directory:
- **annotated_top.mp4** / **annotated_side.mp4**: Visualization videos with stream overlay
- **clinical_report.png**: Clinical-grade dual-panel report
- **flow_timeseries.csv**: Frame-by-frame flow data
- **qmax_report.json**: Summary metrics in JSON format

## How It Works

### Segmentation Pipeline

```
Frame Input
    ↓
Background Subtraction (MOG2)
    ↓
ROI Filtering (if locked)
    ↓
Width-Based Gating (remove thick objects)
    ↓
Morphological Cleanup
    ↓
Vertical Dilation (connect fragments)
    ↓
Geometric Filtering (aspect ratio)
    ↓
Stream Contour Output
```

### Key Parameters

- **MOG2 varThreshold**: 10 (high sensitivity)
- **ROI Width**: 120px (narrow focus)
- **Thick Object Kernel**: 40×40px (hand removal)
- **Vertical Dilation Kernel**: 5×25px (gap filling)
- **Aspect Ratio Threshold**: 1.2 (locked) / 2.0 (unlocked)

## Project Structure

```
opencv model/
├── data/                   # Input videos and calibration
│   ├── top.mp4
│   ├── side.mp4
│   └── top.png            # Calibration image
├── scripts/
│   └── run_analysis.py    # Main analysis script
├── src/
│   ├── calibration.py     # Calibration detection
│   ├── segmentation.py    # Stream segmentation (ROI + Width gating)
│   ├── tracking.py        # Velocity tracking
│   ├── flow_estimation.py # Flow calculation
│   ├── volume.py          # Volume normalization
│   ├── visualize.py       # Video annotation
│   └── ensemble/          # Multi-view fusion
└── outputs/               # Analysis results
```

## Calibration

The system auto-detects a physical reference (blue line = 26cm) in `top.png` to establish pixel-to-cm scale. If calibration image is not found, it uses a fallback scale.

## License

MIT License

