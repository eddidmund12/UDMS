from flask import Blueprint, render_template, request, redirect, flash, url_for, session, send_file
import io
import sqlite3
import os
import tempfile
from utils import role_required, hash_password, check_password, data_validation,process_image,generate_otp,send_otp_email, log_admin_activity

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

#admin login
@admin_bp.route("/login", methods=["GET", "POST"])
def admin_logon():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        
        conn_admins = sqlite3.connect("admins.db")
        cursor_admins = conn_admins.cursor()
        cursor_admins.execute("SELECT * FROM admins WHERE email=?", (email,))
        admin = cursor_admins.fetchone()
        conn_admins.close()

        if admin and check_password(admin[8], password):  # Index 8 is password
            if admin[9] == "admin" and admin[10] == 0:  # Index 9 is role, 10 is is_approved
                flash("Your admin account is pending approval", "warning")
                return render_template("admin_login.html")
            session["user_id"] = admin[0] 
            session["email"] = admin[6] #Email adress
            session["name"] = f"{admin[1]} {admin[3]}"  # First name and last name
            session["role"] = admin[9]
            log_admin_activity(admin[0], admin[6], "Logged in")
            flash("Login successful!", "success")
            return redirect(url_for("admin.admin_dashboard"))
        else:
            flash("Invalid email or password", "danger")
            return render_template("admin_login.html")

    return render_template("admin_login.html")


@admin_bp.route("/create_admin", methods=["GET", "POST"])
@role_required("admin")
def create_admin():
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
        role = request.form["role"]  

        if role == "user":
            flash("User account creation is not allowed through this form", "error")
            return redirect(url_for("user.user_logon"))

        error = data_validation(first_name, last_name, sex, dob, passport, email, password, confirm_password)
        if error:
            flash(error, "error")
            return redirect(url_for("superadmin.superadmin_create_admin"))
        
        
        

        hashed_password = hash_password(password)
        file= request.files['image']
        try:
            if 'image' not in request.files:
                raise ValueError('No image provided')
            image_data = process_image(file)
            conn = sqlite3.connect("admins.db")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM admins WHERE email=?", (email,))
            if cursor.fetchone():
                flash("Email already taken, please use another one", "error")
                return redirect(url_for("admin.create_admin"))
            if 'image' not in request.files:
                flash("No image provided","error")
            if file.filename=='':
                flash("No image provided","error")
            cursor.execute('''INSERT INTO admins
                              (first_name, middle_name, last_name, sex, dob, email, passport, password, role, is_approved)
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                           (first_name, middle_name, last_name, sex, dob, email, image_data, hashed_password, role, 0))
            conn.commit()
            admin_id = cursor.lastrowid
            conn.close()
            log_admin_activity(admin_id, email, "Created admin account")
            flash("Account creation request sent succesfully and is pending approval!", "success")
            return redirect(url_for("admin.admin_logon"))
        except sqlite3.IntegrityError:
            flash("Email already exists!", "error")
            return redirect(url_for("admin.admin_logon"))

    return render_template("admin_signup.html")

#admins signup route
@admin_bp.route("/signup", methods=["GET", "POST"])
# @role_required("admin")
def admin_signup():
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
        role = request.form["role"]  

        if role == "user":
            flash("User account creation is not allowed through this form", "error")
            return redirect(url_for("user.user_logon"))

        error = data_validation(first_name, last_name, sex, dob, passport, email, password, confirm_password)
        if error:
            flash(error, "error")
            return redirect(url_for("admin.admin_signup"))
        
        file= request.files['image']
        try:
            if 'image' not in request.files:
                raise ValueError('No image provided')
            image_data = process_image(file)
            conn = sqlite3.connect("admins.db")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM admins WHERE email=?", (email,))
            if cursor.fetchone():
                flash("Email already taken, please use another one", "error")
                return redirect(url_for("admin.admin_signup"))
            if 'image' not in request.files:
                flash("No image provided","error")
            file= request.files['image']
            if file.filename=='':
                flash("No image provided","error")

            # Generate OTP and send email
            from app import mail
            otp = generate_otp()
            send_otp_email(email, otp, mail)

            # Save image data to a temporary file
            temp_filename = tempfile.mktemp(suffix='.jpg')
            with open(temp_filename, 'wb') as f:
                f.write(image_data)

            # Store admin data and OTP in session for verification
            session['pending_admin'] = {
                'first_name': first_name,
                'middle_name': middle_name,
                'last_name': last_name,
                'sex': sex,
                'dob': dob,
                'email': email,
                'password': password,
                'role': role,
                'temp_image': temp_filename
            }
            session['otp'] = otp

            flash("An OTP has been sent to your email. Please verify to complete registration.", "info")
            session['show_otp_modal'] = True
            return render_template("admin_signup.html", show_otp_modal=True)

        except sqlite3.IntegrityError:
            flash("Email already exists!", "error")
            return redirect(url_for("admin.admin_logon"))

    return render_template("admin_signup.html")

#Otp verification
@admin_bp.route('/verify_otp', methods=['GET', 'POST'])
def admin_verify_otp():
    if request.method == 'POST':
        otp_input = request.form.get('otp', '').strip()
        if not otp_input.isdigit() or len(otp_input) != 6:
            flash("OTP must be exactly 6 digits", "error")
            session['show_otp_modal'] = True
            return render_template("admin_signup.html", show_otp_modal=True)

        if otp_input == session.get('otp'):
            pending_admin = session.get('pending_admin')
            if pending_admin:
                hashed_password = hash_password(pending_admin['password'])
                conn = sqlite3.connect("admins.db")
                cursor = conn.cursor()

                # Read image data from temporary file
                temp_image_path = pending_admin.get('temp_image')
                image_data = None
                if temp_image_path and os.path.exists(temp_image_path):
                    with open(temp_image_path, 'rb') as f:
                        image_data = f.read()
                    os.remove(temp_image_path)  # Remove temp file after reading

                cursor.execute('''INSERT INTO admins
                                  (first_name, middle_name, last_name, sex, dob, email, passport, password, role, is_approved)
                                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                               (pending_admin['first_name'], pending_admin['middle_name'], pending_admin['last_name'],
                                pending_admin['sex'], pending_admin['dob'], pending_admin['email'],
                                image_data, hashed_password, pending_admin['role'], 0))
                conn.commit()
                admin_id = cursor.lastrowid
                conn.close()
                log_admin_activity(admin_id, pending_admin['email'], "Registered as admin")
                session.pop('otp', None)
                session.pop('pending_admin', None)
                session.pop('show_otp_modal', None)
                flash(" success! Your account is pending approval by the superadmin.", "success")
                return redirect(url_for("admin.admin_logon"))
            else:
                # Clean up temp file if session expired
                temp_image_path = session.get('pending_admin', {}).get('temp_image')
                if temp_image_path and os.path.exists(temp_image_path):
                    os.remove(temp_image_path)
                session.pop('otp', None)
                session.pop('pending_admin', None)
                flash("Session expired, please try again", "error")
                return redirect(url_for("admin.signup"))
        else:
            flash("Invalid OTP", "error")
            session['show_otp_modal'] = True
            return render_template("admin_signup.html", show_otp_modal=True)
    return render_template("admin_signup.html")


#admin dashboard
@admin_bp.route("/dashboard")
@role_required("admin")
def admin_dashboard():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    conn.close()
    return render_template("admin_dashboard.html", user_count=user_count)

#users management route
@admin_bp.route("/manage_users")
@role_required("admin")
def admin_manage_users():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()
    return render_template("admin_manage_users.html", users=users)


#admin profile image
@admin_bp.route('/passport/<int:admin_id>')
def admin_passport(admin_id):
    conn = sqlite3.connect("admins.db")
    cursor = conn.cursor()
    cursor.execute("SELECT passport FROM admins WHERE id=?", (admin_id,))
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

#edit users route
@admin_bp.route("/edit/<int:user_id>", methods=["GET", "POST"])
@role_required("admin")
def admin_edit_user(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    if request.method == "POST":
        firstname = request.form["firstname"]
        middlename = request.form["middlename"]
        lastname = request.form["lastname"]
        dob = request.form["dob"]
        email = request.form["email"]
        sex = request.form["sex"]

        cursor.execute("""UPDATE users
                          SET first_name=?, middle_name=?, last_name=?, sex=?, dob=?, email=?
                          WHERE id=?""",
                       (firstname, middlename, lastname, sex, dob, email, user_id))
        conn.commit()
        conn.close()
        log_admin_activity(session["user_id"], session["email"], "Edited user profile")
        flash("User updated successfully!", "success")
        return redirect(url_for("admin.admin_manage_users"))

    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return render_template("admin_edit.html", user=user)

#Delete user account
@admin_bp.route("/delete/<int:user_id>")
@role_required("admin")
def admin_delete_user(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    if user:
        log_admin_activity(session["user_id"], session["email"], "Deleted user account")
    cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    flash("Account deleted successfully!", "success")
    return redirect(url_for("admin.admin_manage_users"))


@admin_bp.route('/logout')
@role_required("admin")
def logout():
    session.clear()
    flash("You have been logged out!", "info")
    return redirect(url_for("admin.admin_logon"))
