from flask import Blueprint, render_template, request, redirect, flash, url_for, session, send_file
import io, os, tempfile
from db import db
from models import User, Admin, AdminLog
from utils import role_required, hash_password, check_password, data_validation, process_image, generate_otp, send_otp_email

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route("/login", methods=["GET", "POST"])
def admin_logon():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        admin = Admin.query.filter_by(email=email).first()
        if admin and check_password(admin.password, password):
            if not admin.is_approved:
                flash("Account pending approval", "warning")
                return render_template("admin_login.html")

            session.update({
                "user_id": admin.id,
                "email": admin.email,
                "role": "admin"
            })
            db.session.add(AdminLog(email=email, action="Logged in"))
            db.session.commit()
            return redirect(url_for("admin.admin_dashboard"))

        flash("Invalid credentials", "danger")
    return render_template("admin_login.html")


@admin_bp.route("/dashboard")
@role_required("admin")
def admin_dashboard():
    user_count = User.query.count()
    return render_template("admin_dashboard.html", user_count=user_count)


@admin_bp.route("/passport/<int:admin_id>")
def admin_passport(admin_id):
    admin = Admin.query.get_or_404(admin_id)
    if admin.passport:
        return send_file(io.BytesIO(admin.passport), mimetype="image/jpeg")
    return "", 404


@admin_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out", "info")
    return redirect(url_for("admin.admin_logon"))
