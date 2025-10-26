from flask import Blueprint, request, jsonify
from datetime import datetime
import sys

# --- Import the main supabase client and hash function ---
from .app import supabase 
from .utils import hash_password

# --- Create the Blueprint ---
admin_bp = Blueprint('admin_bp', __name__)

# --- Define your routes using the Blueprint ---
# This route will be at /admin/signup
@admin_bp.route("/signup", methods=["POST"])
def admin_signup():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    password = data.get("password", "")
    
    # ... (Rest of your signup logic) ...
    
    try:
        # Check if email already exists
        existing_user = supabase.table("admin_users").select("email").eq("email", email).execute()
        if existing_user.data:
            return jsonify({"ok": False, "message": "Email already exists"}), 400

        hashed_password = hash_password(password)
        supabase.table("admin_users").insert({
            "email": email,
            "password": hashed_password,
            "created_at": datetime.now().isoformat(),
            "last_login": None
        }).execute()
        
        return jsonify({"ok": True, "message": "Account created successfully"})
    except Exception as e:
        print(f"!!! CRASH IN ADMIN_SIGNUP ROUTE !!! Error: {e}", file=sys.stderr)
        return jsonify({"ok": False, "message": f"Internal server error. Log: {e}"}), 500

# This route will be at /admin/login
@admin_bp.route("/login", methods=["POST"])
def admin_login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    password = data.get("password", "")

    # ... (Rest of your login logic) ...
    
    try:
        hashed_password = hash_password(password)
        user = supabase.table("admin_users").select("*").eq("email", email).eq("password", hashed_password).execute()
        
        if not user.data:
            return jsonify({"ok": False, "message": "Invalid email or password"}), 401
    
        user_data = user.data[0]
        
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