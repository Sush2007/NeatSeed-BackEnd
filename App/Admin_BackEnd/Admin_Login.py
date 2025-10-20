from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
import hashlib
from datetime import datetime
import os


app = Flask(__name__)
CORS(app, origins=["https://neatseed.onrender.com"])

# Supabase configuration from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def hash_password(password):
    """Simple password hashing using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

@app.route("/admin_signup", methods=["POST"])
def admin_signup():
    data = request.get_json(silent=True) or {}
    full_name = data.get("fullName", "")
    email = data.get("email", "")
    phone = data.get("phone", "")
    password = data.get("password", "")

    if not all([full_name, email, phone, password]):
        return jsonify({"ok": False, "message": "All fields are required"}), 400

    try:
        # Check if email already exists
        existing_user = supabase.table("admin_users").select("email").eq("email", email).execute()
        if existing_user.data:
            return jsonify({"ok": False, "message": "Email already exists"}), 400

        # Hash password and insert user
        hashed_password = hash_password(password)
        result = supabase.table("admin_users").insert({
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "password": hashed_password,
            "created_at": datetime.now().isoformat(),
            "last_login": None  # Add a field to track last login time
        }).execute()
        
        return jsonify({"ok": True, "message": "Account created successfully"})
    except Exception as e:
        return jsonify({"ok": False, "message": f"Signup error: {str(e)}"}), 500

@app.route("/admin_login", methods=["POST"])
def admin_login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"ok": False, "message": "Email and password required"}), 400

    try:
        # Check if user exists and password matches
        hashed_password = hash_password(password)
        user = supabase.table("admin_users").select("*").eq("email", email).eq("password", hashed_password).execute()
        
        if not user.data:
            return jsonify({"ok": False, "message": "Invalid email or password"}), 401

        user_data = user.data[0]
        
        # Update the last login time in the admin_users table
        supabase.table("admin_users").update({
        "last_login": datetime.now().isoformat()
        }).eq("phone", user_data["phone"]).execute()
        
        return jsonify({
            "ok": True, 
            "message": "Login successful",
            "user": {
                "full_name": user_data["full_name"],
                "email": user_data["email"],
                "role": user_data["role"]
            }
        })
    except Exception as e:
        return jsonify({"ok": False, "message": f"Login error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
