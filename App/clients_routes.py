from flask import Blueprint, request, jsonify
from datetime import datetime
import sys

# --- Import the main supabase client and hash function ---
from .database import supabase 
from .utils import hash_password, generate_otp, send_email_otp

# --- Create the Blueprint ---
client_bp = Blueprint('client_bp', __name__)

# This route will be at /client/signup
@client_bp.route('/signup', methods=['POST'])
def user_signup():
    try:
        data = request.get_json(silent=True) or {}
        full_name = data.get('name') or data.get('fullName') 
        email = data.get('email')
        phone = data.get('phone') # Added phone capture
        password = data.get('password')
        address = data.get('address') # Added address capture
        role = data.get('role', 'user').lower()
        
        print(f"DEBUG: Signup request for {email} as {role}")

        # 1. Determine Table Name
        if role == 'user':
            table_name = 'client_users'
        elif role == 'driver':
            table_name = 'driver_users'
        else:
            return jsonify({"error": "Invalid role specified"}), 400

        # 2. Validation
        if not email or not password or not full_name:
            return jsonify({"error": "Missing required fields"}), 400

        # 3. Check if user exists (in the CORRECT table)
        existing_user = supabase.table(table_name).select("*").eq('email', email).execute()
        if existing_user.data:
            return jsonify({"error": f"User already exists in {table_name}"}), 400

        hashed_password = hash_password(password)
        otp = generate_otp()

        # 4. Prepare Data (Match your database schema)
        user_data = {
            "full_name": full_name, # Ensure column name matches DB (full_name vs name)
            "email": email,
            "phone": phone,
            "address": address,
            "password": hashed_password,
            "role": role,
            "otp": otp,
            "is_verified": False,
            "created_at": datetime.now().isoformat()
        }
        
        # 5. Insert into DB (The CORRECT table)
        supabase.table(table_name).insert(user_data).execute()
        
        # 6. Send Email
        email_status = send_email_otp(email, otp)
        
        if not email_status:
            print("WARNING: Database insert success, but Email failed.")
            return jsonify({
                "message": "Account created. (Email sending failed - check server logs)",
                "redirect": True 
            }), 200

        return jsonify({"message": "Signup successful! OTP sent.", "redirect": True}), 201

    except Exception as e:
        print(f"!!! CRITICAL SERVER ERROR: {str(e)}")
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

@client_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    otp = data.get("otp")
    role = data.get("role", "").lower()
    
    if not email or not otp:
        return jsonify({"ok": False, "message": "Email and OTP are required"}), 400
        
    if role == "user":
        table_name = "client_users"
    elif role == "driver":
        table_name = "driver_users"
    else:
        return jsonify({"ok": False, "message": "Invalid role"}), 400
        
    try:
        # Check if user exists with this email and OTP
        response = supabase.table(table_name).select("*").eq("email", email).eq("otp", otp).execute()
        
        if not response.data:
            return jsonify({"ok": False, "message": "Invalid OTP or email"}), 400
            
        # Update user as verified and clear OTP
        supabase.table(table_name).update({
            "is_verified": True,
            "otp": None
        }).eq("email", email).execute()
        
        return jsonify({"ok": True, "message": "Email verified successfully"})
        
    except Exception as e:
        print(f"Error verifying OTP: {e}")
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
            
        # Check if verified
        if not user_data.get("is_verified", False):
             return jsonify({"ok": False, "message": "Please verify your email first"}), 403
        
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