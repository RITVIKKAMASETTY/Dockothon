"""
Cloudinary upload service for storing analysis outputs.
"""
import os
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

# Cloudinary configuration
CLOUDINARY_ENABLED = os.getenv("CLOUDINARY_ENABLED", "false").lower() == "true"
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")

if CLOUDINARY_ENABLED and CLOUDINARY_CLOUD_NAME:
    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
        secure=True
    )


def upload_file(file_path: str, folder: str = "dockothon", resource_type: str = "auto") -> dict:
    """
    Upload a file to Cloudinary.
    
    Args:
        file_path: Local path to the file
        folder: Cloudinary folder to store in
        resource_type: "auto", "image", "video", or "raw"
    
    Returns:
        dict with 'url' and 'public_id' or empty dict if failed
    """
    if not CLOUDINARY_ENABLED:
        print("Cloudinary is disabled, returning local path")
        return {"url": file_path, "public_id": None}
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return {}
    
    try:
        # Get filename without extension for public_id
        filename = os.path.basename(file_path)
        
        result = cloudinary.uploader.upload(
            file_path,
            folder=folder,
            resource_type=resource_type,
            public_id=filename.rsplit('.', 1)[0] if '.' in filename else filename,
            overwrite=True
        )
        
        print(f"Uploaded to Cloudinary: {result.get('secure_url')}")
        return {
            "url": result.get("secure_url"),
            "public_id": result.get("public_id")
        }
    except Exception as e:
        print(f"Cloudinary upload error: {e}")
        return {}


def upload_video(file_path: str, folder: str = "dockothon/videos") -> dict:
    """Upload video file to Cloudinary."""
    return upload_file(file_path, folder=folder, resource_type="video")


def upload_image(file_path: str, folder: str = "dockothon/images") -> dict:
    """Upload image file to Cloudinary."""
    return upload_file(file_path, folder=folder, resource_type="image")


def upload_raw(file_path: str, folder: str = "dockothon/files") -> dict:
    """Upload raw file (CSV, JSON, etc) to Cloudinary."""
    return upload_file(file_path, folder=folder, resource_type="raw")
