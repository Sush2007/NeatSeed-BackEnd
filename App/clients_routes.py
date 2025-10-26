from flask import Blueprint, request, jsonify
from datetime import datetime
import sys

# --- Import the main supabase client and hash function ---
from .app import supabase
from .utils import hash_password

# --- Create the Blueprint ---
client_bp = Blueprint('client_bp', __name__)

# This route will be at /client/signup
@client_bp.route('/signup', methods=['POST'])
def user_signup():
    print("--- POST /client/signup route function STARTED ---", file=sys.stderr)
    print(f"Request Headers: {request.headers}", file=sys.stderr)
    print(f"Request Raw Data: {request.data}", file=sys.stderr)
    data = request.get_json(silent=True) or {}
    # ... (Your signup logic from Clients_Login.py) ...
    full_name = data.get("fullName", "")
    email = data.get("email", "")
    phone = data.get("phone", "")
    role = data.get("role", "").lower()
    password = data.get("password", "")
    address = data.get("address", "")
    
    if role == "user":
        table_name = "client_users"
    elif role == "driver":
        table_name = "driver_users"
    else:
        return jsonify({"message": "Invalid role specified"}), 400
    
    try:
        if email: 
            existing_email_check = supabase.table(table_name).select("email").eq("email", email).execute()
            if existing_email_check.data:
                return jsonify({"ok": False, "message": f"Email already exists in {table_name}"}), 400

        existing_phone_check = supabase.table(table_name).select("phone").eq("phone", phone).execute()
        if existing_phone_check.data:
            return jsonify({"ok": False, "message": f"Phone number already exists in {table_name}"}), 400
            
        hashed_password = hash_password(password)
        
        user_data = {
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "password": hashed_password,
            "address": address,
            "created_at": datetime.now().isoformat()
        }
        supabase.table(table_name).insert(user_data).execute()
        
        return jsonify({"ok": True, "message": f"Account created successfully for role: {role}"})
    
    except Exception as e:
        print(f"Error during client signup: {e}")
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500

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