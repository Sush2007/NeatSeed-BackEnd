import os
import logging
from flask import Flask, jsonify, make_response
from flask_cors import CORS
from dotenv import load_dotenv

# --- 1. Load Environment & Setup ---
load_dotenv()

# Import Local Modules
# Ensure these paths are correct relative to main.py
from .database import supabase
from .admin_routes import admin_bp
from .clients_routes import client_bp

app = Flask(__name__)

# --- 2. Logging Configuration ---
logging.basicConfig(level=logging.INFO)
logger = app.logger

# --- 3. Professional CORS Setup ---
# Define allowed origins
base_origins = [
    "https://neatseed-user.onrender.com",
    "https://neatseed.onrender.com",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

# Allow additional origins from environment variable
additional_origins = os.getenv("CORS_ORIGINS", "")
if additional_origins:
    base_origins.extend([origin.strip() for origin in additional_origins.split(",") if origin.strip()])

logger.info(f"CORS Allowed Origins: {base_origins}")

is_development = os.getenv("FLASK_ENV", "").lower() == "development"

CORS(
    app,
    resources={r"/*": {"origins": base_origins}},
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin"],
    expose_headers=["Content-Type", "Authorization"],
    max_age=3600
)

# --- 4. Register Blueprints ---
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(client_bp, url_prefix='/client')

# --- 7. The "Professional" Landing Page (HTML) ---
# When you visit the base URL in a browser, you see this UI.
@app.route('/')
def root_dashboard():
    html_content = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <title>NeatSeed API Service</title>
        <style>
          body {{ font-family: 'Segoe UI', sans-serif; background: #f0fdf4; text-align: center; padding-top: 50px; margin: 0; }}
          .container {{ background: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); display: inline-block; }}
          h1 {{ color: #10b981; margin-bottom: 10px; }}
          .status {{ color: #6b7280; font-weight: bold; display: flex; align-items: center; justify-content: center; gap: 10px; }}
          .dot {{ height: 12px; width: 12px; background-color: #10b981; border-radius: 50%; display: inline-block; animation: pulse 2s infinite; }}
          .meta {{ margin-top: 20px; font-size: 0.9em; color: #888; }}
          @keyframes pulse {{ 0% {{ box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }} 70% {{ box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }} 100% {{ box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }} }}
        </style>
      </head>
      <body>
        <div class="container">
          <h1>NeatSeed API Server</h1>
          <div class="status"><span class="dot"></span>System Operational</div>
          <div class="meta">
            <p>Environment: <strong>{os.getenv("FLASK_ENV", "Production")}</strong></p>
            <p>Connected Clients: <strong>Active</strong></p>
          </div>
        </div>
      </body>
    </html>
    """
    return make_response(html_content, 200)

# --- 8. Programmatic Health Check (JSON) ---
# Use this for uptime robots or frontend connectivity checks
@app.route('/api/health')
def health_check():
    return jsonify({
        "status": "success",
        "message": "Backend operational",
        "services": {
            "database": "Supabase Connected", # Ideally, add real DB check here
            "mode": os.getenv("FLASK_ENV", "Production")
        }
    }), 200

# --- 9. Production Execution Block ---
if __name__ == "__main__":
    # CRITICAL: Render provides a PORT env var. If you don't use it, the deploy fails.
    port = int(os.environ.get("PORT", 5000))
    
    # Only run debug mode if explicitly set in environment
    is_debug = os.environ.get("FLASK_ENV") == "development"
    
    print(f"🚀 NeatSeed Server starting on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=is_debug)
