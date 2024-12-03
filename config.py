import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URL")

# Cloudinary configuration
CLOUDINARY_NAME = os.getenv("CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("API_KEY")
CLOUDINARY_API_SECRET = os.getenv("API_SECRET")

# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
