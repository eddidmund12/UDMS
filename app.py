# app.py
from flask import Flask, session, flash, redirect, url_for, render_template
from flask_mail import Mail
from utils import init_db

app = Flask(__name__)
app.secret_key = "EDMUND"

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Gmail SMTP
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'edmundaseyi@gmail.com'  # email
app.config['MAIL_PASSWORD'] = 'subf twev gayv qxwr'  # app password (not regular password). Generated from Google account settings.
app.config['MAIL_DEFAULT_SENDER'] = 'edmundaseyi@gmail.com'  # email

mail = Mail(app)

# Imported blueprints after mail initialization to avoid circular import
from users_rt import user_bp
from admin_rt import admin_bp
from superadmin_rt import superadmin_bp

# Register blueprints
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

if __name__ == "__main__":
    init_db()
    from utils import init_logs_db
    init_logs_db()
    app.run(debug=True)
