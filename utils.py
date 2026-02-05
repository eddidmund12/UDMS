from flask import session, flash, redirect, url_for
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from PIL import Image
import io
import random
import string
from flask_mail import Message
from app import db

# =======================
# DATABASE MODELS
# =======================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    middle_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100), nullable=False)
    sex = db.Column(db.String(10), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    passport = db.Column(db.LargeBinary, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="admin")
    is_approved = db.Column(db.Boolean, default=False)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    middle_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100), nullable=False)
    sex = db.Column(db.String(10), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    passport = db.Column(db.LargeBinary, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="admin")
    is_approved = db.Column(db.Boolean, default=False)

class SuperAdmin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    middle_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100), nullable=False)
    sex = db.Column(db.String(10), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    passport = db.Column(db.LargeBinary)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="superadmin")

class UserLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    email = db.Column(db.String(150))
    action = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=db.func.now())

class AdminLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer)
    email = db.Column(db.String(150))
    action = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=db.func.now())

# =======================
# HELPERS
# =======================

def hash_password(password):
    return generate_password_hash(password)

def check_password(stored_password, provided_password):
    return check_password_hash(stored_password, provided_password)

def calculate_age(dob):
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

def data_validation(first_name, last_name, sex, dob, passport, email, password, confirm_password):
    if not all([first_name, last_name, sex, dob, email, password, confirm_password]):
        return "All fields are required"
    if "@" not in email:
        return "Invalid email format"
    if len(password) < 6:
        return "Password must not be less than 6 characters"
    if password != confirm_password:
        return "Passwords do not match"
    dob = datetime.strptime(dob, "%Y-%m-%d").date()
    if calculate_age(dob) < 18:
        return "You must be at least 18 years old"
    return None

def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                flash("Login required", "warning")
                return redirect(url_for("user.user_logon"))
            if session.get("role") != required_role:
                flash("Access denied", "danger")
                return redirect(url_for("dashboard"))
            return f(*args, **kwargs)
        return wrapper
    return decorator

def process_image(file):
    if not file or file.filename == '':
        raise ValueError("No image selected")
    image_data = file.read()
    img = Image.open(io.BytesIO(image_data))
    img.verify()
    return image_data

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(email, otp, mail):
    msg = Message("Your OTP Code", recipients=[email])
    msg.body = f"Your OTP code is {otp}"
    mail.send(msg)

def log_user_activity(user_id, email, action):
    db.session.add(UserLog(user_id=user_id, email=email, action=action))
    db.session.commit()

def log_admin_activity(admin_id, email, action):
    db.session.add(AdminLog(admin_id=admin_id, email=email, action=action))
    db.session.commit()

def create_default_superadmin():
    if not SuperAdmin.query.first():
        sa = SuperAdmin(
            first_name="Edmund",
            middle_name="Eniola",
            last_name="Adeyi",
            sex="Male",
            dob=date(2007, 6, 26),
            email="eddiedmund123@gmail.com",
            password=generate_password_hash("Administrator")
        )
        db.session.add(sa)
        db.session.commit()
