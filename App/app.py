import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# 1. Load environment variables first
load_dotenv()

# Import database (make sure database.py exists and works)
from .database import supabase

app = Flask(__name__)

# 2. Professional CORS Setup
# allowing "Content-Type" and "Authorization" headers is crucial for your frontend to communicate
CORS(app, resources={r"/*": {
    "origins": ["https://neatseed-user.onrender.com", "https://neatseed.onrender.com"],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"]
}})

# 3. Import and Register Routes
from .admin_routes import admin_bp
from .clients_routes import client_bp

app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(client_bp, url_prefix='/client')

@app.route('/')
def health_check():
    return jsonify({
        "status": "success",
        "message": "Backend is running smooth!",
        "connected_services": {
            "admin_frontend": "Healthy & Connected",
            "client_frontend": "Healthy & Connected"
        }
    }), 200

# 4. Run Server
if __name__ == "__main__":
    # Use a standard port like 5000
    app.run(debug=True, port=5000)