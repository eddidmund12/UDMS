import os
from pymongo import MongoClient
import cloudinary
import cloudinary.uploader

client = MongoClient(os.getenv("MONGO_URI"))
db = client.udms

users_col = db.users
admins_col = db.admins
superadmins_col = db.superadmins
otp_logs_col = db.otp_logs

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)
