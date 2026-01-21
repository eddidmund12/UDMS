# app.py
import os
from flask import Flask, session, flash, redirect, url_for, render_template
from flask_mail import Mail
from utils import init_db, init_logs_db,create_default_superadmin

app = Flask(__name__)

# 🔐 Security (Render Environment Variables)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

# 📧 Flask-Mail configuration (Render-safe)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get("MAIL_USERNAME")

mail = Mail(app)

# 🔗 Import blueprints AFTER mail init
from users_rt import user_bp
from admin_rt import admin_bp
from superadmin_rt import superadmin_bp

app.register_blueprint(user_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(superadmin_bp)

# Shared routes
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out!", "info")
    return redirect(url_for("user.user_logon"))

@app.route('/welcome')
def welcome():
    return render_template("welcome.html")

@app.route('/data')
def data():
    return render_template("data.html")

@app.route('/dashboard')
def dashboard():
    return render_template("dashboard.html")

# ✅ INIT DATABASES (Render-safe)
init_db()
init_logs_db()
create_default_superadmin()