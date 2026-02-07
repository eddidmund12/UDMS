from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import users_col
import cloudinary.uploader
import uuid
from datetime import datetime

users_bp = Blueprint("users", __name__)

@users_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]

        if users_col.find_one({"email": email}):
            flash("Email already exists")
            return redirect(url_for("users.signup"))

        image = request.files.get("passport")
        upload = cloudinary.uploader.upload(image) if image else None

        user = {
            "_id": str(uuid.uuid4()),
            "name": request.form["name"],
            "email": email,
            "password": generate_password_hash(request.form["password"]),
            "passport_url": upload["secure_url"] if upload else None,
            "approved": False,
            "created_at": datetime.utcnow()
        }

        users_col.insert_one(user)
        flash("Signup successful. Await approval.")
        return redirect(url_for("users.login"))

    return render_template("signup.html")


@users_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = users_col.find_one({"email": request.form["email"]})

        if not user or not check_password_hash(user["password"], request.form["password"]):
            flash("Invalid credentials")
            return redirect(url_for("users.login"))

        if not user["approved"]:
            flash("Account not approved yet")
            return redirect(url_for("users.login"))

        session["user_id"] = user["_id"]
        return redirect(url_for("users.dashboard"))

    return render_template("login.html")


@users_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("users.login"))
    return render_template("user_dashboard.html")


@users_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("users.login"))
