from flask import Blueprint, render_template, request, redirect, flash, url_for, session, send_file, jsonify
import io, os, tempfile, time
from db import db
from models import User, UserLog
from utils import data_validation, role_required, hash_password, check_password, process_image, generate_otp, send_otp_email

user_bp = Blueprint('user', __name__)

@user_bp.route('/')
def homePage():
    return render_template("welcome.html")


@user_bp.route('/login', methods=["GET", "POST"])
def user_logon():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()
        if user and check_password(user.password, password):
            session.update({
                "user_id": user.id,
                "email": user.email,
                "role": "user"
            })
            db.session.add(UserLog(email=email, action="Logged in"))
            db.session.commit()
            return redirect(url_for("user.home", user_id=user.id))

        flash("Invalid credentials", "danger")
    return render_template("login.html")


@user_bp.route("/home/<int:user_id>")
@role_required("user")
def home(user_id):
    user = User.query.get_or_404(user_id)
    return render_template("home.html", user=user)


@user_bp.route('/passport/<int:user_id>')
def user_passport(user_id):
    user = User.query.get_or_404(user_id)
    if user.passport:
        return send_file(io.BytesIO(user.passport), mimetype="image/jpeg")
    return "", 404


@user_bp.route('/logout')
def logout():
    session.clear()
    flash("Logged out", "info")
    return redirect(url_for("user.homePage"))
