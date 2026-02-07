from flask import Blueprint, render_template, request, redirect, flash, url_for, session
from db import db
from models import User, Admin, SuperAdmin, UserLog, AdminLog
from utils import role_required, data_validation, hash_password, check_password

superadmin_bp = Blueprint('superadmin', __name__, url_prefix='/superadmin')

@superadmin_bp.route("/login", methods=["GET", "POST"])
def superadmin_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        superadmin = SuperAdmin.query.filter_by(email=email).first()
        if superadmin and check_password(superadmin.password, password):
            session["user_id"] = superadmin.id
            session["email"] = superadmin.email
            session["role"] = "superadmin"
            flash("Login successful!", "success")
            return redirect(url_for("superadmin.superadmin_dashboard"))

        flash("Invalid email or password", "danger")
    return render_template("superadmin_login.html")


@superadmin_bp.route("/dashboard")
@role_required("superadmin")
def superadmin_dashboard():
    users = User.query.all()
    approved_admins = Admin.query.filter_by(is_approved=True).all()
    pending_admins = Admin.query.filter_by(is_approved=False).all()
    superadmins = SuperAdmin.query.all()
    return render_template(
        "superadmin_dashboard.html",
        users=users,
        daily_users=0,
        approved_admins=approved_admins,
        pending_admins=pending_admins,
        superadmins=superadmins
    )


@superadmin_bp.route("/approve_admin/<int:admin_id>", methods=["GET", "POST"])
@role_required("superadmin")
def superadmin_approve_admin(admin_id):
    admin = Admin.query.get_or_404(admin_id)

    if request.method == "POST":
        action = request.form["action"]
        if action == "approve":
            admin.is_approved = True
            flash(f"Admin {admin.email} approved!", "success")
        else:
            db.session.delete(admin)
            flash("Admin rejected and deleted!", "success")
        db.session.commit()
        return redirect(url_for("superadmin.superadmin_dashboard"))

    return render_template("approve_admin.html", admin=admin)


@superadmin_bp.route("/delete_user/<int:user_id>")
@role_required("superadmin")
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully", "success")
    return redirect(url_for("superadmin.superadmin_dashboard"))


@superadmin_bp.route("/delete_admin/<int:admin_id>")
@role_required("superadmin")
def delete_admin(admin_id):
    admin = Admin.query.get_or_404(admin_id)
    db.session.delete(admin)
    db.session.commit()
    flash("Admin deleted successfully", "success")
    return redirect(url_for("superadmin.superadmin_dashboard"))


@superadmin_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "info")
    return redirect(url_for("superadmin.superadmin_login"))
