import os
import sys
import traceback
from flask import Flask, jsonify
from flask_cors import CORS
from supabase import create_client, Client

# --- Import your new route blueprints ---
from .admin_routes import admin_bp
from .clients_routes import client_bp

app = Flask(__name__)

# --- Get BOTH frontend URLs from environment ---
ADMIN_ORIGIN = os.getenv("FRONTEND_ADMIN_URL", "*")
CLIENT_ORIGIN = os.getenv("FRONTEND_CLIENTS_URL", "*")

# --- Setup CORS to allow BOTH frontends ---
CORS(app, origins=[ADMIN_ORIGIN, CLIENT_ORIGIN])

# --- Create ONE Supabase client for the whole app ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

try:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("FATAL ERROR: SUPABASE_URL or SUPABASE_KEY is missing.")
    
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("SUCCESS: Supabase client initialized.")

except Exception as e:
    print(f"!!! FATAL CRASH DURING SUPABASE SETUP !!! Error: {e}", file=sys.stderr)
    sys.exit(1)

# --- Register your "mini-apps" (Blueprints) ---
# All admin routes will be at /admin/...
app.register_blueprint(admin_bp, url_prefix='/admin')
# All client routes will be at /client/...
app.register_blueprint(client_bp, url_prefix='/client')


# --- Health check for Render ---
@app.route("/")
def health_check():
    return "Unified server is running and healthy!", 200 

# --- Global error handler ---
@app.errorhandler(Exception)
def handle_error(e):
    traceback.print_exc(file=sys.stderr)
    return jsonify({
        "ok": False,
        "message": "Internal Server Error. Please check backend logs."
    }), 500

if __name__ == "__main__":
    app.run(debug=True)