from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
import hashlib
from datetime import datetime
import os
import sys

FRONTEND_ORIGIN = os.getenv("FRONTEND_CLIENTS_URL", "*")  # Default to "*" if not set
app = Flask(__name__)
CORS(app, origins=[FRONTEND_ORIGIN] if FRONTEND_ORIGIN else "*")

# Supabase configuration - YOU NEED TO REPLACE THESE WITH YOUR ACTUAL SUPABASE URL AND KEY
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# Function to hash a password
def hash_password(password):
    """Simple password hashing using SHA256"""
    # hashlib.sha256(password.encode()).hexdigest() returns a string, no need for .decode('utf-8')
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/user_signup', methods=['POST'])
def user_signup():
    data = request.get_json(silent=True) or {}
    full_name = data.get("fullName", "")
    email = data.get("email", "")
    phone = data.get("phone", "")
    role = data.get("role", "").lower() # Convert role to lowercase for consistent checking
    password = data.get("password", "")
    address = data.get("address", "")

    if not all([full_name, phone, address, role, password]):
        return jsonify({"message": "All fields are required"}), 400
    
    # --- Role-based Table Selection ---
    if role == "client":
        table_name = "client_users"
    elif role == "driver":
        table_name = "driver_users"
    else:
        return jsonify({"message": "Invalid role specified"}), 400

    try:
        # Check if email already exists in the selected table
        existing_email_check = supabase.table(table_name).select("email").eq("email", email).execute()
        existing_phone_check = supabase.table(table_name).select("phone").eq("phone", phone).execute()

        if existing_email_check.data:
            return jsonify({"ok": False, "message": f"Email already exists"}), 400
        
        if existing_phone_check.data:
            return jsonify({"ok": False, "message": f"Phone number already exists"}), 400

        # Hash the password
        hashed_password = hash_password(password) # Corrected: Removed .decode('utf-8')

        # Prepare data for insertion
        user_data = {
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "password": hashed_password,
            "address": address,
            "created_at": datetime.now().isoformat(),
            "last_login": None 
        }

        # Insert data into the determined table
        result = supabase.table(table_name).insert(user_data).execute()
        
        return jsonify({"ok": True, "message": f"Account created successfully for role: {role}"})
    
    except Exception as e:
        # It's good practice to log the full exception for debugging
        print(f"Error during signup: {e}")
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500
        

@app.route('/client_login', methods=['POST'])
def client_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400
    
    # Assuming 'check_password' is defined elsewhere (it's missing in the original code)
    def check_password(plain_password, hashed_password):
        return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password
    
    try:
        # Example modification for checking the client table (adjust as needed for drivers)
        response = supabase.table('client_users').select("*").eq('email', email).execute() 
        
        if response.data:
            user = response.data[0]
            # You must define check_password (using hash_password for comparison)
            if check_password(password, user['password']):
                # Update last_login time here
                return jsonify({"message": "Login successful", "role": user['role']}), 200
            else:
                return jsonify({"message": "Invalid credentials"}), 401
        else:
             return jsonify({"message": "User not found"}), 404
             
    except Exception as e:
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500
    
@app.route("/")
def health_check():
    # Render's health check will hit this and get a 200 OK
    return "Server is running and healthy!", 200 
    # Return a status code 200 to confirm success

if __name__ == '__main__':
    app.run(debug=True)