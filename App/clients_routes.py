from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import sys

# CHANGE: Import supabase from database.py
from .database import supabase
from .utils import hash_password, generate_otp, send_email_otp

client_bp = Blueprint('client_bp', __name__)

@client_bp.route('/signup', methods=['POST'])
def user_signup():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    phone = data.get("phone")
    role = data.get("role", "").lower()
    password = data.get("password")
    full_name = data.get("fullName")
    address = data.get("address")

    table_name = "client_users" if role == "user" else "driver_users"
    
    try:
        # 1. Check Duplicates
        if supabase.table(table_name).select("email").eq("email", email).execute().data:
            return jsonify({"ok": False, "message": "Email exists"}), 400

        # 2. Insert User (Verified = False)
        hashed = hash_password(password)
        supabase.table(table_name).insert({
            "full_name": full_name, "email": email, "phone": phone,
            "password": hashed, "address": address, "is_verified": False,
            "created_at": datetime.now().isoformat()
        }).execute()

        # 3. Send OTP
        otp = generate_otp()
        if send_email_otp(email, otp):
            expiry = (datetime.now() + timedelta(minutes=5)).isoformat()
            supabase.table("otp_codes").upsert({
                "email": email, "otp": otp, "expires_at": expiry
            }).execute()
            return jsonify({"ok": True, "message": "OTP sent"})
            
        return jsonify({"ok": False, "message": "Failed to send OTP"}), 500

    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500

@client_bp.route("/verify-otp", methods=["POST"])
def verify_client_otp():
    data = request.get_json()
    email = data.get("email")
    otp = data.get("otp")
    role = data.get("role", "user") # Passed from frontend

    table_name = "client_users" if role == "user" else "driver_users"

    try:
        # Verify OTP
        record = supabase.table("otp_codes").select("*").eq("email", email).execute()
        if not record.data or record.data[0]['otp'] != otp:
            return jsonify({"ok": False, "message": "Invalid OTP"}), 400

        # Activate User
        supabase.table(table_name).update({"is_verified": True}).eq("email", email).execute()
        
        # Clean OTP
        supabase.table("otp_codes").delete().eq("email", email).execute()
        
        return jsonify({"ok": True, "message": "Verified"})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500

@client_bp.route('/login', methods=['POST'])
def client_login():
    data = request.get_json(silent=True) or {}
    # --- This is the new logic for Email or Phone ---
    identifier = data.get("identifier") 
    password = data.get("password")

    if not identifier or not password:
        return jsonify({"ok": False, "message": "Email/phone and password are required"}), 400

    try:
        hashed_password = hash_password(password)
        
        user_data = None
        table_to_check = None

        # Smart check: Is it an email or a phone?
        if "@" in identifier:
            query_field = "email"
        else:
            query_field = "phone"
            
        # Check client_users table
        user_response = supabase.table("client_users").select("*").eq(query_field, identifier).eq("password", hashed_password).execute()
        if user_response.data:
            user_data = user_response.data[0]
            table_to_check = "client_users"
        else:
            # Check driver_users table
            user_response = supabase.table("driver_users").select("*").eq(query_field, identifier).eq("password", hashed_password).execute()
            if user_response.data:
                user_data = user_response.data[0]
                table_to_check = "driver_users"

        if not user_data or not table_to_check:
            return jsonify({"ok": False, "message": "Invalid credentials"}), 401
        
        # Update last_login
        supabase.table(table_to_check).update({
            "last_login": datetime.now().isoformat()
        }).eq("phone", user_data["phone"]).execute()
        
        return jsonify({
            "ok": True, 
            "message": "Login successful",
            "user": {
                "full_name": user_data["full_name"],
                "email": user_data.get("email"),
                "phone": user_data["phone"],
                "role": user_data.get("role")
            }
        })
    except Exception as e:
        print(f"!!! CRASH IN CLIENT_LOGIN ROUTE !!! Error: {e}", file=sys.stderr)
        return jsonify({"ok": False, "message": f"Internal server error. Log: {e}"}), 500