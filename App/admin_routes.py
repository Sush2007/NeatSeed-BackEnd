from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import sys

# CHANGE: Import supabase from database.py, NOT app.py
from .database import supabase 
from .utils import hash_password, generate_otp, send_email_otp

admin_bp = Blueprint('admin_bp', __name__)

@admin_bp.route("/signup", methods=["POST"])
def admin_signup():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    password = data.get("password", "")
    
    try:
        # 1. Check existence
        existing = supabase.table("admin_users").select("email").eq("email", email).execute()
        if existing.data:
            return jsonify({"ok": False, "message": "Email already exists"}), 400

        # 2. Create User (Verified = FALSE)
        hashed_password = hash_password(password)
        supabase.table("admin_users").insert({
            "email": email,
            "password": hashed_password,
            "is_verified": False,  # NEW FIELD
            "created_at": datetime.now().isoformat()
        }).execute()

        # 3. Send OTP
        otp = generate_otp()
        if send_email_otp(email, otp):
            # Save OTP to DB
            expiry = (datetime.now() + timedelta(minutes=5)).isoformat()
            supabase.table("otp_codes").upsert({
                "email": email, "otp": otp, "expires_at": expiry
            }).execute()
            return jsonify({"ok": True, "message": "OTP sent to email"})
        
        return jsonify({"ok": False, "message": "Failed to send OTP"}), 500

    except Exception as e:
        print(f"Admin Signup Error: {e}", file=sys.stderr)
        return jsonify({"ok": False, "message": str(e)}), 500

# NEW ROUTE: Verify OTP
@admin_bp.route("/verify-otp", methods=["POST"])
def verify_admin_otp():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    otp = data.get("otp")

    try:
        # 1. Check OTP table
        record = supabase.table("otp_codes").select("*").eq("email", email).execute()
        if not record.data:
            return jsonify({"ok": False, "message": "No OTP found"}), 400
        
        db_otp = record.data[0]['otp']
        
        # 2. Validate
        if db_otp == otp:
            # Mark user as verified
            supabase.table("admin_users").update({"is_verified": True}).eq("email", email).execute()
            # Clean up OTP
            supabase.table("otp_codes").delete().eq("email", email).execute()
            return jsonify({"ok": True, "message": "Verification Successful"})
        
        return jsonify({"ok": False, "message": "Invalid OTP"}), 400
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500

@admin_bp.route("/login", methods=["POST"])
def admin_login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    
    hashed = hash_password(password)
    user = supabase.table("admin_users").select("*").eq("email", email).eq("password", hashed).execute()

    if user.data:
        # NEW CHECK: Is Verified?
        if user.data[0].get('is_verified') is False:
            return jsonify({"ok": False, "message": "Please verify your email first"}), 403

        return jsonify({"ok": True, "message": "Login Success", "user": user.data[0]})
    
    return jsonify({"ok": False, "message": "Invalid credentials"}), 401