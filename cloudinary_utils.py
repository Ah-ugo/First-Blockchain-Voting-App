from cloudinary import config, uploader
import os
from fastapi import HTTPException

config(
    cloud_name=os.getenv("CLOUD_NAME"),
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET")
)
def upload_image_to_cloudinary(file: bytes, folder: str):
    """Uploads an image to Cloudinary and returns the URL."""
    try:
        response = uploader.upload(
            file,
            folder=folder,
            resource_type="image"
        )
        return response["secure_url"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")
