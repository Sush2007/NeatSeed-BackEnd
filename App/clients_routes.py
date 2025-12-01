from flask import Blueprint, request, jsonify
from datetime import datetime
from .database import supabase 
from .utils import hash_password, generate_otp, send_email_otp

client_bp = Blueprint('client_bp', __name__)

@client_bp.route('/signup', methods=['POST'])
def user_signup():
    try:
        data = request.get_json(silent=True) or {}
        
        # Map Frontend 'name' to Backend 'full_name'
        full_name = data.get('name') or data.get('fullName')
        email = data.get('email')
        password = data.get('password')
        phone = data.get('phone', '') 
        address = data.get('address', '')
        role = data.get('role', 'user').lower()
        
        if not full_name or not email or not password:
             return jsonify({"ok": False, "message": "Missing required fields"}), 400

        table_name = 'client_users' if role == 'user' else 'driver_users'

        hashed_password = hash_password(password)
        otp = generate_otp()

        # Prepare Data
        user_data = {
            "full_name": full_name, 
            "email": email,
            "password": hashed_password,
            "phone": phone,
            "address": address,
            "otp": otp,
            "is_verified": False, 
            "created_at": datetime.now().isoformat()
        }

        # Check Duplicates & Handle Unverified Users
        try:
            existing = supabase.table(table_name).select("*").eq("email", email).execute()
            if existing.data:
                existing_user = existing.data[0]
                if existing_user.get('is_verified'):
                    return jsonify({"ok": False, "message": "Email already exists"}), 400
                else:
                    supabase.table(table_name).update(user_data).eq("email", email).execute()
            else:
                # New User -> Insert
                supabase.table(table_name).insert(user_data).execute()
        except Exception as db_err:
             print(f"Database Error: {db_err}")
             return jsonify({"ok": False, "message": "Database error during signup"}), 500
        
        # Send Email (Fail-Safe)
        send_email_otp(email, otp)
            
        # Redirect
        return jsonify({
            "ok": True,
            "message": "Account created. Please verify OTP.", 
            "redirect": True
        }), 200

    except Exception as e:
        print(f"!!! CLIENT ROUTE CRASH: {str(e)}")
        return jsonify({"ok": False, "message": f"Server Crash: {str(e)}"}), 500

# --- VERIFY OTP ROUTE (Crucial for the flow) ---
@client_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    otp = data.get("otp")
    role = data.get("role", "").lower()
    
    if not email or not otp:
        return jsonify({"ok": False, "message": "Email and OTP are required"}), 400
        
    # Determine which table to check
    elif role == 'user':
        table_name = "client_users"
    elif role == 'driver':
        table_name = "driver_users"
    else:
        return jsonify({"ok": False, "message": "Invalid role"}), 400
        
    try:
        # 1. Find User with matching Email AND OTP
        response = supabase.table(table_name).select("*").eq("email", email).eq("otp", otp).execute()
        
        if not response.data:
            return jsonify({"ok": False, "message": "Invalid OTP"}), 400
            
        # 2. Success! Mark as verified and clear OTP
        supabase.table(table_name).update({
            "is_verified": True,
            "otp": None
        }).eq("email", email).execute()
        
        return jsonify({"ok": True, "message": "Email verified successfully"})
        
    except Exception as e:
        return jsonify({"ok": False, "message": f"Verification failed: {str(e)}"}), 500

@client_bp.route('/login', methods=['POST'])
def client_login():
    data = request.get_json(silent=True) or {}
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
            
        if not user_data.get("is_verified", False):
            new_otp = generate_otp()
            
            # Update DB with new OTP using email (most reliable key)
            supabase.table(table_to_check).update({
                "otp": new_otp
            }).eq("email", user_data["email"]).execute() 
            
            send_email_otp(user_data["email"], new_otp)
            
            # Tell Frontend to redirect to verification page
            return jsonify({
                "ok": False, 
                "message": "Account not verified. A new OTP has been sent.",
                "redirect_to_verify": True,
                "email": user_data["email"],
                "role": "user" if table_to_check == "client_users" else "driver"
            }), 403 
        
        # --- FIX 3: Update last_login using email (More Robust) ---
        supabase.table(table_to_check).update({
            "last_login": datetime.now().isoformat()
        }).eq("email", user_data["email"]).execute() 
        
        role_found = "user" if table_to_check == "client_users" else "driver"

        return jsonify({
            "ok": True, 
            "message": "Login successful",
            "token": "client-session-token", # Token for frontend to save
            "user": {
                "full_name": user_data.get("full_name"),
                "email": user_data.get("email"),
                "role": role_found
            }
        })
    except Exception as e:
        print(f"!!! CRASH IN CLIENT_LOGIN ROUTE !!! Error: {e}")
        return jsonify({"ok": False, "message": f"Internal server error. Log: {e}"}), 500