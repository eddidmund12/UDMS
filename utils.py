import sqlite3
from PIL import Image
from flask import session, flash, redirect, url_for
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import io
from datetime import datetime,date
from flask_mail import Mail
import random
import string
from flask_mail import Message
def init_db():
    # Initialize users.db
    conn_users = sqlite3.connect("users.db")
    cursor_users = conn_users.cursor()
    cursor_users.execute('''CREATE TABLE IF NOT EXISTS users(
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            first_name TEXT NOT NULL,
                            middle_name TEXT,
                            last_name TEXT NOT NULL,
                            sex TEXT NOT NULL,
                            dob TEXT NOT NULL,
                            email TEXT NOT NULL UNIQUE,
                            passport BLOB NOT NULL,
                            password TEXT NOT NULL,
                            role TEXT NOT NULL DEFAULT 'admin', 
                            is_approved INTEGER NOT NULL DEFAULT 0)''')
    conn_users.commit()
    conn_users.close()

    # Initialize admins.db with is_approved column
    conn_admins = sqlite3.connect("admins.db")
    cursor_admins = conn_admins.cursor()
    cursor_admins.execute('''CREATE TABLE IF NOT EXISTS admins(
                             id INTEGER PRIMARY KEY AUTOINCREMENT,
                             first_name TEXT NOT NULL,
                             middle_name TEXT,
                             last_name TEXT NOT NULL,
                             sex TEXT NOT NULL,
                             dob TEXT NOT NULL,
                             email TEXT NOT NULL UNIQUE,
                             passport BLOB NOT NULL,
                             password TEXT NOT NULL,
                             role TEXT NOT NULL DEFAULT 'admin',
                             is_approved INTEGER NOT NULL DEFAULT 0)''')
    conn_admins.commit()
    conn_admins.close()

    # Initialize superadmins.db
    conn_superadmins = sqlite3.connect("superadmins.db")
    cursor_superadmins = conn_superadmins.cursor()
    cursor_superadmins.execute('''CREATE TABLE IF NOT EXISTS superadmins(
                                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                                  first_name TEXT NOT NULL,
                                  middle_name TEXT,
                                  last_name TEXT NOT NULL,
                                  sex TEXT NOT NULL,
                                  dob TEXT NOT NULL,
                                  email TEXT NOT NULL UNIQUE,
                                  passport BLOB NOT NULL  ,
                                  password TEXT NOT NULL,
                                  role TEXT NOT NULL DEFAULT 'superadmin')''')
    conn_superadmins.commit()
    conn_superadmins.close()

#form inputs validation
def data_validation(first_name, last_name, sex, dob, passport, email, password, confirm_password):
    if not all([first_name, last_name, sex, dob, email, password, confirm_password]):
        return "All fields are required"
    if "@" not in email or ".com" not in email:
        return "Invalid email format"
    if not(email.endswith('@gmail.com') or email.endswith('@yahoo.com') or email.endswith('@outlook.com') or email.endswith('@hotmail.com') or email.endswith('@icloud.com')):
        return "Invalid email address"
    if len(password) < 6:
        return "Password must not be less than 6 characters"
    if password != confirm_password:
        return "Passwords do not match"

    # dob_str = dob
    if not dob:
        return "Date of birth is required"
    try:
        dob = datetime.strptime(dob, "%Y-%m-%d").date()
    except ValueError:
        return "Invalid date format"

    if calculate_age(dob) < 18:
        return "You must be at least 18 years of age to register"
        
    
    return None
   
    
#roles assingment
def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                if role_required == "superadmin":
                    return redirect(url_for("superadmin.superadmin_login"))
                flash("Please log in first", "warning")
                if role_required == "admin":
                    return redirect(url_for("admin.admin_logon"))
                else:
                    return redirect(url_for("user.user_logon"))
                
            if session.get("role") != required_role:
                flash("You do not have permission to access this page", "danger")
                if session.get("role") == "superadmin":
                    return redirect(url_for("superadmin.superadmin_dashboard"))
                elif session.get("role") == "admin":
                    return redirect(url_for("admin.admin_dashboard"))
                else:
                    return redirect(url_for("user.home", user_id=session["user_id"]))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def hash_password(password):
    return generate_password_hash(password)

def check_password(stored_password, provided_password):
    return check_password_hash(stored_password, provided_password)


#image upload handler
def process_image(file):
    if not file or file.filename =='':
        raise ValueError('No image selected')
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    if not '.' in file.filename or file.filename.rsplit('.',1)[1].lower() not in allowed_extensions:
        raise ValueError('Invalid image format')
    image_data = file.read()
    if not image_data:
        raise ValueError('Empty image file')
    max_size= 5*1024*1024
    if len(image_data) > max_size:
        raise ValueError('File size too large. Max 5MB.')
    try:
        img= Image.open(io.BytesIO(image_data))
        img.verify()
    except Exception:
        raise ValueError('Invalid image file')
    return image_data

    #Age calculator
def calculate_age(dob):
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

# Generate OTP 
def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

# Send OTP email
def send_otp_email(email, otp, mail):
    msg = Message('Your OTP Code', recipients=[email])
    msg.body = f'Your OTP code is {otp}. It expires in 10 minutes.'
    mail.send(msg)

# Initialize logs.db
def init_logs_db():
    conn = sqlite3.connect("logs.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_logs(
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      email TEXT,
                      action TEXT,
                      timestamp TEXT DEFAULT CURRENT_TIMESTAMP)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS admin_logs(
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      admin_id INTEGER,
                      email TEXT,
                      action TEXT,
                      timestamp TEXT DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

# Log user activity
def log_user_activity(user_id, email, action):
    conn = sqlite3.connect("logs.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user_logs (user_id, email, action) VALUES (?, ?, ?)", (user_id, email, action))
    conn.commit()
    conn.close()

# Log admin activity
def log_admin_activity(admin_id, email, action):
    conn = sqlite3.connect("logs.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO admin_logs (admin_id, email, action) VALUES (?, ?, ?)", (admin_id, email, action))
    conn.commit()
    conn.close()



    
            