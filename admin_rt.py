from flask import Blueprint, render_template, request, redirect, flash, url_for, session, send_file
import io, os, tempfile
from db import db
from models import User, Admin, AdminLog
from utils import role_required, hash_password, check_password, data_validation, process_image, generate_otp, send_otp_email

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
from flask import Blueprint, render_template, redirect, url_for, session
from db import users_col, admins_col

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin/login")
def admin_login():
    return render_template("admin_login.html")


@admin_bp.route("/admin/dashboard")
def admin_dashboard():
    if "admin_id" not in session:
        return redirect(url_for("admin.admin_login"))

    pending_users = users_col.find({"approved": False})
    return render_template("admin_dashboard.html", users=pending_users)


@admin_bp.route("/admin/approve/<user_id>")
def approve_user(user_id):
    users_col.update_one({"_id": user_id}, {"$set": {"approved": True}})
    return redirect(url_for("admin.admin_dashboard"))



@admin_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out", "info")
    return redirect(url_for("admin.admin_logon"))
