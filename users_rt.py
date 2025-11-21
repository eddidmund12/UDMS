
from flask import Blueprint, render_template, request, redirect, flash, url_for, session,send_file, jsonify
import io
import sqlite3
import os
import tempfile
import time
from utils import data_validation, role_required, hash_password, check_password, process_image, generate_otp, send_otp_email, log_user_activity

user_bp = Blueprint('user', __name__)

#Welcome page
@user_bp.route('/')
def homePage():
    return render_template("welcome.html")

#Users login route
@user_bp.route('/login', methods=["GET", "POST"])
def user_logon():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password(user[8], password):  # Index 8 is password
            session["user_id"] = user[0]
            session["email"] = user[6]
            session["role"] = "user"
            log_user_activity(user[0], user[6], "Logged in")
            flash("Login successful!", "success")
            return redirect(url_for("user.home", user_id=user[0]))
        else:
            flash("Invalid email or password", "danger")
            return render_template("login.html")

    return render_template("login.html")


# Users signup route
@user_bp.route('/signup', methods=["GET", "POST"])
def user_input():
    if request.method == "POST":
        first_name = request.form["firstname"]
        middle_name = request.form.get("middlename")
        last_name = request.form["lastname"]
        sex = request.form["sex"]
        dob = request.form["dob"]
        passport = request.files["image"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["c-password"]

        error = data_validation(first_name, last_name, sex, dob, passport, email, password, confirm_password)
        if error:
            flash(error, "error")
            return redirect(url_for("user.user_input"))

        file = request.files['image']
        try:
            if 'image' not in request.files:
                raise ValueError('No image provided')
            image_data = process_image(file)  # Convert image to binary data
            if 'image' not in request.files:
               flash("No image provided","error")
            file = request.files['image']
            if file.filename == '':
                flash("No image provided","error")

            # Check for duplicate email before sending OTP
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email=?", (email,))
            if cursor.fetchone():
                conn.close()
                flash("Email already taken, please use another one", "error")
                return redirect(url_for("user.user_input"))
            conn.close()

            # Generate OTP and send email
            from app import mail
            otp = generate_otp()
            send_otp_email(email, otp, mail)
            session['last_otp_sent'] = time.time()

            # Save image data to temporary file
            temp_filename = tempfile.mktemp(suffix='.jpg')
            with open(temp_filename, 'wb') as f:
                f.write(image_data)

            # Store user data and OTP in session for verification
            session['pending_user'] = {
                'first_name': first_name,
                'middle_name': middle_name,
                'last_name': last_name,
                'sex': sex,
                'dob': dob,
                'email': email,
                'password': password,
                'temp_image': temp_filename
            }
            session['otp'] = otp

            flash("An OTP has been sent to your email. Please verify to complete registration.", "info")
            return redirect(url_for("user.verify_otp"))

        except ValueError as e:
            flash(str(e), "error")
            return redirect(url_for("user.user_input"))

    return render_template("signup.html")

 
#Otp verification route
@user_bp.route('/verify_otp', methods=["GET", "POST"])
def verify_otp():
    if request.method == "POST":
        otp_input = request.form["otp"].strip()
        if not otp_input.isdigit() or len(otp_input) != 6:
            flash("OTP must be exactly 6 digits", "error")
            return render_template("verify_otp.html", last_otp_sent=session.get('last_otp_sent'))
        if otp_input == session.get('otp'):
            pending_user = session.get('pending_user')
            if pending_user:
                conn = sqlite3.connect("users.db")
                cursor = conn.cursor()
                cursor.execute("PRAGMA journal_mode=WAL;")

                hashed_password = hash_password(pending_user['password'])

                # Read image data from temporary file
                temp_image_path = pending_user.get('temp_image')
                image_data = None
                if temp_image_path and os.path.exists(temp_image_path):
                    with open(temp_image_path, 'rb') as f:
                        image_data = f.read()
                    os.remove(temp_image_path)  # Remove temp file after reading

                cursor.execute('''INSERT INTO users
                                  (first_name, middle_name, last_name, sex, dob, email, passport, password)
                                  VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                               (pending_user['first_name'], pending_user['middle_name'], pending_user['last_name'],
                                pending_user['sex'], pending_user['dob'], pending_user['email'],
                                image_data, hashed_password))
                conn.commit()
                user_id = cursor.lastrowid
                conn.close()
                log_user_activity(user_id, pending_user['email'], "Registered")
                session.pop('otp', None)
                session.pop('pending_user', None)
                flash("You have been registered successfully!", "success")
                return redirect(url_for("user.user_logon"))
            else:
                # Clean up temp file if session expired
                temp_image_path = session.get('pending_user', {}).get('temp_image')
                if temp_image_path and os.path.exists(temp_image_path):
                    os.remove(temp_image_path)
                session.pop('otp', None)
                session.pop('pending_user', None)
                flash("Session expired, please try again", "error")
                return redirect(url_for("user.homePage"))
        else:
            flash("Invalid OTP", "error")
            return render_template("verify_otp.html", last_otp_sent=session.get('last_otp_sent'))
    return render_template("verify_otp.html")

@user_bp.route('/resend_otp', methods=["POST"])
def resend_otp():
    if 'pending_user' not in session:
        return jsonify({'success': False, 'message': 'Session expired'})
    
    last_sent = session.get('last_otp_sent', 0)
    if time.time() - last_sent < 60:
        remaining = 60 - (time.time() - last_sent)
        return jsonify({'success': False, 'message': 'Please wait', 'remaining': int(remaining)})
    
    from app import mail
    email = session['pending_user']['email']
    otp = generate_otp()
    send_otp_email(email, otp, mail)
    session['otp'] = otp
    session['last_otp_sent'] = time.time()
    return jsonify({'success': True, 'message': 'OTP resent successfully'})

#Users homepage
@user_bp.route("/home/<int:user_id>")
@role_required("user")
def home(user_id):
    if session["user_id"] != user_id:
        flash("Please login first", "warning")
        return redirect(url_for("user.user_logon"))

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user is None:
        flash("User not found", "error")
        return redirect(url_for("user.user_logon"))

    return render_template("home.html", user=user)

@user_bp.route("/edit/<int:user_id>", methods=["GET", "POST"])
@role_required("user")
def edit_user(user_id):
    if session["user_id"] != user_id:
        flash("You can only edit your own profile", "danger")
        return redirect(url_for("user.home", user_id=session["user_id"]))

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
                           
    
    if request.method == "POST":
        firstname = request.form["firstname"]
        middlename = request.form["middlename"]
        lastname = request.form["lastname"]
        dob = request.form["dob"]
        sex = request.form["sex"]
        
        

        cursor.execute("""UPDATE users
                          SET first_name=?, middle_name=?, last_name=?, sex=?, dob=?
                          WHERE id=?""",
                       (firstname, middlename, lastname, sex, dob, user_id))
        conn.commit()
        conn.close()
        email=session.get("email")
        log_user_activity(user_id, email, "Updated profile")
        flash("Profile updated successfully!", "success")
        return redirect(url_for("user.home", user_id=user_id,))

    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return render_template("edit.html", user=user)


#Users profile photo
@user_bp.route('/passport/<int:user_id>')
def user_passport(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT passport FROM users WHERE id=?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row and row[0]:
        return send_file(
            io.BytesIO(row[0]),
            mimetype='image/jpeg'
        )
    else:
        # Return a placeholder image or 404
        return '', 404
    
@user_bp.route('/logout')
@role_required('user')
def logout():
    session.clear()
    flash("You have been logged out!", "info")
    return redirect(url_for("user.homePage"))


