import sqlite3
from werkzeug.security import generate_password_hash

def create_superadmin():
    conn = sqlite3.connect("superadmins.db")
    cursor = conn.cursor()

    # Check if a superadmin already exists
    cursor.execute("SELECT COUNT(*) FROM superadmins")
    superadmin_count = cursor.fetchone()[0]
    if superadmin_count > 0:
        print("Error: A superadmin already exists. Only one superadmin is allowed.")
        conn.close()
        return

    # Superadmin details
    first_name = "Edmund"
    middle_name = "Eniola"
    last_name = "Adeyi"
    sex = "Male"
    dob = "2007-06-26"
    email = "eddiedmund123@gmail.com"
    passport = "jikkkkl"
    password = "Administrator"  
    role = "superadmin"
    hashed_password = generate_password_hash(password)
    

    try:
        cursor.execute('''INSERT INTO superadmins 
                         (first_name, middle_name, last_name, sex, dob, email, passport, password, role)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                       (first_name, middle_name, last_name, sex, dob, email, passport, hashed_password, role))
        conn.commit()
        print("Superadmin account created successfully!")
        print(f"Email: {email}")
        print(f"Password: {password}")
    except sqlite3.IntegrityError:
        print("Error: Email already exists in superadmins.db")
    finally:
        conn.close()

if __name__ == "__main__":
    create_superadmin()