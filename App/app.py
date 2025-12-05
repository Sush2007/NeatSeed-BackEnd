import os
import logging
from flask import Flask, jsonify, make_response, request
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
# This effectively replaces "Morgan" from Node.js. 
# It ensures you see request details in your Render logs.
logging.basicConfig(level=logging.INFO)
logger = app.logger

# --- 3. Professional CORS Setup ---
# IMPORTANT:
#   - Origins in CORS are just scheme + host + (optional) port, no trailing slash.
#   - Make sure these match exactly how your frontend is served.
allowed_origins = [
    "https://neatseed-user.onrender.com",
    "https://neatseed.onrender.com",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

# Allow additional origins from environment variable (comma-separated)
additional_origins = os.getenv("CORS_ORIGINS", "")
if additional_origins:
    allowed_origins.extend([origin.strip() for origin in additional_origins.split(",") if origin.strip()])

logger.info(f"CORS Allowed Origins: {allowed_origins}")

# Enhanced CORS configuration with better error handling
# In development, allow all origins for easier debugging
is_development = os.getenv("FLASK_ENV", "").lower() == "development"
cors_origins_config = "*" if is_development else allowed_origins

if is_development:
    logger.warning("⚠️  DEVELOPMENT MODE: CORS allowing all origins (*)")

CORS(
    app,
    resources={
        r"/*": {
            "origins": cors_origins_config,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            "allow_headers": [
                "Content-Type",
                "Authorization",
                "X-Requested-With",
                "Accept",
                "Origin",
                "Access-Control-Request-Method",
                "Access-Control-Request-Headers",
            ],
            "expose_headers": [
                "Content-Type",
                "Authorization",
            ],
        }
    },
    supports_credentials=True,
    max_age=3600,  # Cache preflight requests for 1 hour
)

# --- 4. CORS Error Handler and Explicit Header Setting ---
@app.after_request
def after_request(response):
    # Get the origin from the request
    origin = request.headers.get('Origin')
    
    # Log CORS-related information for debugging
    if origin:
        logger.info(f"CORS Request from origin: {origin}")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request path: {request.path}")
    
    # In development mode, allow all origins
    if is_development:
        if origin:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin, Access-Control-Request-Method, Access-Control-Request-Headers'
            response.headers['Access-Control-Expose-Headers'] = 'Content-Type, Authorization'
            response.headers['Access-Control-Max-Age'] = '3600'
            logger.info(f"DEV MODE: CORS headers set for origin: {origin}")
    else:
        # Production mode: only allow listed origins
        if origin and origin in allowed_origins:
            # Explicitly set CORS headers to ensure they're present
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin, Access-Control-Request-Method, Access-Control-Request-Headers'
            response.headers['Access-Control-Expose-Headers'] = 'Content-Type, Authorization'
            response.headers['Access-Control-Max-Age'] = '3600'
            logger.info(f"CORS headers set for origin: {origin}")
        elif origin:
            logger.warning(f"Origin {origin} not in allowed list: {allowed_origins}")
    
    # Handle OPTIONS preflight requests explicitly
    if request.method == 'OPTIONS':
        if is_development:
            response.headers['Access-Control-Allow-Origin'] = origin if origin else '*'
        else:
            response.headers['Access-Control-Allow-Origin'] = origin if origin and origin in allowed_origins else (allowed_origins[0] if allowed_origins else '*')
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin, Access-Control-Request-Method, Access-Control-Request-Headers'
        response.headers['Access-Control-Max-Age'] = '3600'
        response.status_code = 200
        logger.info(f"OPTIONS preflight handled for origin: {origin}")
    
    return response

# --- 5. Explicit OPTIONS handlers for main routes (backup for CORS) ---
@app.route('/client/login', methods=['OPTIONS'])
@app.route('/client/signup', methods=['OPTIONS'])
@app.route('/client/verify-otp', methods=['OPTIONS'])
@app.route('/admin/login', methods=['OPTIONS'])
@app.route('/admin/signup', methods=['OPTIONS'])
@app.route('/admin/verify-otp', methods=['OPTIONS'])
@app.route('/admin/resend-otp', methods=['OPTIONS'])
def handle_options():
    """Explicit OPTIONS handler for CORS preflight requests"""
    response = make_response()
    origin = request.headers.get('Origin')
    
    if is_development:
        response.headers['Access-Control-Allow-Origin'] = origin if origin else '*'
    else:
        response.headers['Access-Control-Allow-Origin'] = origin if origin and origin in allowed_origins else (allowed_origins[0] if allowed_origins else '*')
    
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin, Access-Control-Request-Method, Access-Control-Request-Headers'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Max-Age'] = '3600'
    response.status_code = 200
    logger.info(f"Explicit OPTIONS handler called for {request.path} from origin: {origin}")
    return response

# --- 6. Register Blueprints ---
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