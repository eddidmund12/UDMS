from flask import Blueprint, render_template, request, redirect, flash, url_for, session
import sqlite3
from utils import role_required, data_validation, hash_password, check_password, log_user_activity, log_admin_activity

superadmin_bp = Blueprint('superadmin', __name__, url_prefix='/superadmin')

@superadmin_bp.route("/login", methods=["GET", "POST"])
# @role_required("superadmin")
def superadmin_login():
    if request.method == "POST":
        email= request.form["email"]
        password= request.form["password"]
        #Check superdmins db
        conn = sqlite3.connect("superadmins.db")
        cursor=conn.cursor()
        cursor.execute("SELECT * FROM superadmins WHERE email=?",(email,))
        superadmin = cursor.fetchone()
        conn.close()

        if superadmin and check_password(superadmin[8], password):
            session["user_id"] = superadmin[0]
            session["email"] = superadmin[0]
            session["role"] = superadmin[9]
            flash("Login succesful!", "success")
            return redirect(url_for("superadmin.superadmin_dashboard"))
        else:
            flash("Invalid email or password", "danger")
            return render_template("superadmin_login.html")

    return render_template("superadmin_login.html")

#Superadmin dashboard
@superadmin_bp.route("/dashboard")
@role_required("superadmin")
def superadmin_dashboard():
    conn_users = sqlite3.connect("users.db")
    cursor_users = conn_users.cursor()
    cursor_users.execute("SELECT * FROM users")
    users = cursor_users.fetchall()
    daily_users = 0  
    conn_users.close()

    conn_admins = sqlite3.connect("admins.db")
    cursor_admins = conn_admins.cursor()
    cursor_admins.execute("SELECT * FROM admins WHERE is_approved=1")
    approved_admins = cursor_admins.fetchall()
    cursor_admins.execute("SELECT * FROM admins WHERE is_approved=0")
    pending_admins = cursor_admins.fetchall()
    conn_admins.close()

    conn_superadmins = sqlite3.connect("superadmins.db")
    cursor_superadmins = conn_superadmins.cursor()
    cursor_superadmins.execute("SELECT * FROM superadmins")
    superadmins = cursor_superadmins.fetchall()
    conn_superadmins.close()

    return render_template("superadmin_dashboard.html", users=users, daily_users=daily_users, approved_admins=approved_admins, pending_admins=pending_admins, superadmins=superadmins)

#Manage users
@superadmin_bp.route("/manage_users")
@role_required("superadmin")
def manage_users():
    conn_users = sqlite3.connect("users.db")
    cursor_users = conn_users.cursor()
    cursor_users.execute("SELECT * FROM users")
    users = cursor_users.fetchall()
    conn_users.close()
    return render_template("superadmin_manage_users.html", users=users)

#Manage pending admins page
@superadmin_bp.route("/manage_pending_admins")
@role_required("superadmin")
def manage_pending_admins():
    conn_admins = sqlite3.connect("admins.db")
    cursor_admins = conn_admins.cursor()
    cursor_admins.execute("SELECT * FROM admins WHERE is_approved=1")
    approved_admins = cursor_admins.fetchall()
    cursor_admins.execute("SELECT * FROM admins WHERE is_approved=0")
    pending_admins = cursor_admins.fetchall()
    conn_admins.close()
    return render_template("superadmin_manage_pending_admins.html", approved_admins=approved_admins, pending_admins=pending_admins)


#manage Approved admins 
@superadmin_bp.route("/manage_admins")
@role_required("superadmin")
def manage_admins():
    conn_admins = sqlite3.connect("admins.db")
    cursor_admins = conn_admins.cursor()
    cursor_admins.execute("SELECT * FROM admins WHERE is_approved=1")
    approved_admins = cursor_admins.fetchall()
    cursor_admins.execute("SELECT * FROM admins WHERE is_approved=0")
    pending_admins = cursor_admins.fetchall()
    conn_admins.close()
    return render_template("superadmin_manage_admins.html", approved_admins=approved_admins, pending_admins=pending_admins)

#Approve admins
@superadmin_bp.route("/approve_admin/<int:admin_id>", methods=["GET", "POST"])
@role_required("superadmin")
def superadmin_approve_admin(admin_id):
    conn = sqlite3.connect("admins.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admins WHERE id=? AND is_approved=0", (admin_id,))
    admin = cursor.fetchone()

    if request.method == "POST":
        action = request.form["action"]
        if action == "approve":
            cursor.execute("UPDATE admins SET is_approved=1 WHERE id=?", (admin_id,))
            flash(f"Admin {admin[6]} approved successfully!", "success")
        elif action == "reject":
            cursor.execute("DELETE FROM admins WHERE id=?", (admin_id,))
            flash(f"Admin {admin[6]} rejected and deleted!", "success")
        conn.commit()
        conn.close()
        return redirect(url_for("superadmin.superadmin_dashboard"))

    conn.close()
    if not admin:
        flash("Admin not found or already approved", "error")
        return redirect(url_for("superadmin.superadmin_dashboard"))
    return render_template("approve_admin.html", admin=admin)

#Edit users data
@superadmin_bp.route("/edit_user/<int:user_id>", methods=["GET", "POST"])
@role_required("superadmin")
def superadmin_edit_user(user_id):
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
        flash("User updated successfully!", "success")
        return redirect(url_for("superadmin.manage_users"))

    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return render_template("superadmin_edit_user.html", user=user)

#Edit admin data
@superadmin_bp.route("/edit_admin/<int:admin_id>", methods=["GET", "POST"])
@role_required("superadmin")
def superadmin_edit_admin(admin_id):
    conn = sqlite3.connect("admins.db")
    cursor = conn.cursor()

    if request.method == "POST":
        firstname = request.form["firstname"]
        middlename = request.form["middlename"]
        lastname = request.form["lastname"]
        dob = request.form["dob"]
        email = request.form["email"]
        sex = request.form["sex"]
        role = request.form["role"]

        cursor.execute("""UPDATE admins 
                          SET first_name=?, middle_name=?, last_name=?, sex=?, dob=?, email=?, role=?
                          WHERE id=?""",
                       (firstname, middlename, lastname, sex, dob, email, role, admin_id))
        conn.commit()
        conn.close()
        flash("Admin updated successfully!", "success")
        return redirect(url_for("superadmin.superadmin_dashboard"))

    cursor.execute("SELECT * FROM admins WHERE id=?", (admin_id,))
    admin = cursor.fetchone()
    conn.close()
    return render_template("superadmin_edit_admin.html", admin=admin)


@superadmin_bp.route("/edit_superadmin/<int:superadmin_id>", methods=["GET", "POST"])
@role_required("superadmin")
def superadmin_edit_superadmin(superadmin_id):
    conn = sqlite3.connect("superadmins.db")
    cursor = conn.cursor()

    if request.method == "POST":
        firstname = request.form["firstname"]
        middlename = request.form["middlename"]
        lastname = request.form["lastname"]
        dob = request.form["dob"]
        email = request.form["email"]
        sex = request.form["sex"]
        password = hash_password(request.form["password"])

        cursor.execute("""UPDATE superadmins 
                          SET first_name=?, middle_name=?, last_name=?, sex=?, dob=?, email=?, password=?
                          WHERE id=?""",
                       (firstname, middlename, lastname, sex, dob, email, password, superadmin_id))
        conn.commit()
        conn.close()
        flash("Superadmin updated successfully!", "success")
        return redirect(url_for("superadmin.superadmin_dashboard"))

    cursor.execute("SELECT * FROM superadmins WHERE id=?", (superadmin_id,))
    superadmin = cursor.fetchone()
    conn.close()
    return render_template("superadmin_edit_superadmin.html", superadmin=superadmin)

#delete users account
@superadmin_bp.route("/delete_user/<int:user_id>")
@role_required("superadmin")
def superadmin_delete_user(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    flash("User deleted successfully!", "success")
    return redirect(url_for("superadmin.manage_users"))

#delete admins account
@superadmin_bp.route("/delete_admin/<int:admin_id>")
@role_required("superadmin")
def superadmin_delete_admin(admin_id):
    conn = sqlite3.connect("admins.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM admins WHERE id=?", (admin_id,))
    conn.commit()
    conn.close()
    flash("Admin deleted successfully!", "success")
    return redirect(url_for("superadmin.superadmin_dashboard"))


@superadmin_bp.route("/delete_superadmin/<int:superadmin_id>")
@role_required("superadmin")
def superadmin_delete_superadmin(superadmin_id):
    if session["user_id"] == superadmin_id:
        flash("You cannot delete your own account", "danger")
        return redirect(url_for("superadmin.superadmin_dashboard"))

    conn = sqlite3.connect("superadmins.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM superadmins")
    if cursor.fetchone()[0] <= 1:
        flash("Cannot delete the last superadmin account", "danger")
        conn.close()
        return redirect(url_for("superadmin.superadmin_dashboard"))
    cursor.execute("DELETE FROM superadmins WHERE id=?", (superadmin_id,))
    conn.commit()
    conn.close()
    flash("Superadmin deleted successfully!", "success")
    return redirect(url_for("superadmin.superadmin_dashboard"))

#Manually create admin
@superadmin_bp.route("/create_admin", methods=["GET", "POST"])
@role_required("superadmin")
def superadmin_create_admin():
    if request.method == "POST":
        first_name = request.form["firstname"]
        middle_name = request.form.get("middlename")
        last_name = request.form["lastname"]
        sex = request.form["sex"]
        dob = request.form["dob"]
        passport = request.form["img"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["c-password"]
        role = request.form["role"]  # Only 'admin' allowed here

        if role == "superadmin":
            flash("Superadmin creation is not allowed through this form", "error")
            return redirect(url_for("superadmin.superadmin_create_admin"))

        error = data_validation(first_name, last_name, sex, dob, passport, email, password, confirm_password)
        if error:
            flash(error, "error")
            return redirect(url_for("superadmin.superadmin_create_admin"))

        hashed_password = hash_password(password)
        try:
            conn = sqlite3.connect("admins.db")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM admins WHERE email=?", (email,))
            if cursor.fetchone():
                flash("Email already taken, please use another one", "error")
                return redirect(url_for("superadmin.superadmin_create_admin"))
            cursor.execute('''INSERT INTO admins
                              (first_name, middle_name, last_name, sex, dob, email, passport, password, role, is_approved)
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                           (first_name, middle_name, last_name, sex, dob, email, passport, hashed_password, role, 0))
            conn.commit()
            conn.close()
            flash("Admin created successfully and is pending approval!", "success")
            return redirect(url_for("superadmin.superadmin_dashboard"))
        except sqlite3.IntegrityError:
            flash("Email already exists!", "error")
            return redirect(url_for("superadmin.superadmin_create_admin"))

    return render_template("create_admin.html")

#User logpage
@superadmin_bp.route("/user_logs")
@role_required("superadmin")
def user_logs():
    conn = sqlite3.connect("logs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, action, timestamp FROM user_logs ORDER BY timestamp DESC")
    logs = cursor.fetchall()
    conn.close()
    return render_template("superadmin_user_logs.html", logs=logs)

#admin logpage
@superadmin_bp.route("/admin_logs")
@role_required("superadmin")
def admin_logs():
    conn = sqlite3.connect("logs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, action, timestamp FROM admin_logs ORDER BY timestamp DESC")
    logs = cursor.fetchall()
    conn.close()
    return render_template("superadmin_admin_logs.html", logs=logs)

@superadmin_bp.route("/clear_user_logs", methods=["POST"])
@role_required("superadmin")
def clear_user_logs():
    conn = sqlite3.connect("logs.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_logs")
    conn.commit()
    conn.close()
    flash("User logs cleared successfully!", "success")
    return redirect(url_for("superadmin.user_logs"))

@superadmin_bp.route("/clear_admin_logs", methods=["POST"])
@role_required("superadmin")
def clear_admin_logs():
    conn = sqlite3.connect("logs.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM admin_logs")
    conn.commit()
    conn.close()
    flash("Admin logs cleared successfully!", "success")
    return redirect(url_for("superadmin.admin_logs"))

@superadmin_bp.route('/logout')
@role_required("superadmin")
def logout():
    session.clear()
    flash("You have been logged out!", "info")
    return redirect(url_for("superadmin.superadmin_login"))
