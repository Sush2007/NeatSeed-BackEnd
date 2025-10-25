import os
import sys
import traceback
from flask import Flask, jsonify
from flask_cors import CORS
from supabase import create_client, Client 

# --- 1. CREATE FLASK APP FIRST ---
app = Flask(__name__)

# --- 2. CONFIGURE CORS ---
ADMIN_ORIGIN = os.getenv("FRONTEND_ADMIN_URL", "*") 
CLIENT_ORIGIN = os.getenv("FRONTEND_CLIENTS_URL", "*") 
CORS(app, origins=[ADMIN_ORIGIN, CLIENT_ORIGIN])

# --- 3. CREATE SUPABASE CLIENT ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = None # Initialize variable first

try:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("FATAL ERROR: SUPABASE_URL or SUPABASE_KEY is missing.")
    
    # Assign the actual client object *here*
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY) 
    print("SUCCESS: Supabase client initialized.")

except Exception as e:
    print(f"!!! FATAL CRASH DURING SUPABASE SETUP !!! Error: {e}", file=sys.stderr)
    sys.exit(1) # Exit if Supabase fails

from .admin_routes import admin_bp
from .clients_routes import client_bp

app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(client_bp, url_prefix='/client')

# --- Health check and error handlers ---
@app.route("/")
def health_check():
    """Health check endpoint for Render."""
    return "Unified server is running and healthy!", 200 

@app.errorhandler(Exception)
def handle_error(e):
    """Global error handler for unexpected issues."""
    traceback.print_exc(file=sys.stderr) # Log the full error
    return jsonify({
        "ok": False,
        "message": "Internal Server Error. Please check backend logs."
    }), 500

# --- Main execution block (for local testing) ---
if __name__ == "__main__":
    if supabase is None:
         print("ERROR: Supabase client failed to initialize. Cannot run locally.", file=sys.stderr)
         sys.exit(1)
    app.run(debug=True)

