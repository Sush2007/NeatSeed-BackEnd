from flask import Blueprint, request, jsonify
from datetime import datetime
import sys
from .database import supabase 
from .utils import hash_password, generate_otp, send_email_otp

admin_bp = Blueprint('admin_bp', __name__)

@admin_bp.route("/signup", methods=["POST"])
def admin_signup():
    try:
        data = request.get_json(silent=True) or {}
        email = data.get("email", "")
        password = data.get("password", "")
        
        # 1. Validation
        if not email or not password:
            return jsonify({"ok": False, "message": "Email and Password are required"}), 400

        # 2. Check Duplicates (Safe Check)
        try:
            existing = supabase.table("admin_users").select("email").eq("email", email).execute()
            if existing.data:
                return jsonify({"ok": False, "message": "Email already exists"}), 400
        except Exception as db_err:
             print(f"DB CHECK IGNORED: {db_err}")

        hashed_password = hash_password(password)
        otp = generate_otp()

        # 3. INSERT NOW (Pending Verification)
        # We MUST save them now to store the password.
        # Removing 'full_name' as requested.
        supabase.table("admin_users").insert({
            "email": email,
            "password": hashed_password,
            "created_at": datetime.now().isoformat(),
            "otp": otp,
            "is_verified": False  # <--- This prevents them from logging in yet
        }).execute()
        
        # 4. Send Email (FAIL-SAFE)
        # Even if email fails, we don't crash, so redirect still happens.
        send_email_otp(email, otp)
        
        # 5. Redirect to OTP Page
        return jsonify({
            "ok": True, 
            "message": "Admin account created. Check email for OTP.",
            "redirect": True
        }), 200

    except Exception as e:
        print(f"!!! ADMIN ROUTE CRASH: {e}", file=sys.stderr)
        return jsonify({"ok": False, "message": f"Server error: {str(e)}"}), 500

@admin_bp.route("/verify-otp", methods=["POST"])
def verify_otp():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    otp = data.get("otp")
    
    if not email or not otp:
        return jsonify({"ok": False, "message": "Email and OTP are required"}), 400
        
    try:
        response = supabase.table("admin_users").select("*").eq("email", email).eq("otp", otp).execute()
        
        if not response.data:
            return jsonify({"ok": False, "message": "Invalid OTP or email"}), 400
            
        supabase.table("admin_users").update({
            "is_verified": True,
            "otp": None
        }).eq("email", email).execute()
        
        return jsonify({"ok": True, "message": "Email verified successfully"})
        
    except Exception as e:
        print(f"Error verifying OTP: {e}")
        return jsonify({"ok": False, "message": f"Verification failed: {str(e)}"}), 500

# This route will be at /admin/login
@admin_bp.route("/login", methods=["POST"])
def admin_login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    password = data.get("password", "")

    try:
        hashed_password = hash_password(password)
        user = supabase.table("admin_users").select("*").eq("email", email).eq("password", hashed_password).execute()
        
        if not user.data:
            return jsonify({"ok": False, "message": "Invalid email or password"}), 401
    
        user_data = user.data[0]
        
        if not user_data.get("is_verified", False):
            return jsonify({"ok": False, "message": "Please verify your email first"}), 403
        
        supabase.table("admin_users").update({
            "last_login": datetime.now().isoformat()
        }).eq("email", user_data["email"]).execute()
        
        return jsonify({
            "ok": True, 
            "message": "Login successful",
            "user": {
                "email": user_data["email"],
            }
        })
    except Exception as e:
        print(f"!!! CRASH IN ADMIN_LOGIN ROUTE !!! Error: {e}", file=sys.stderr)
        return jsonify({"ok": False, "message": f"Internal server error. Log: {e}"}), 500