import os
import sys
import traceback
from flask import Flask, jsonify
from flask_cors import CORS
from .database import supabase # Import from new file

app = Flask(__name__)

# CORS Setup
CORS(app, origins=["*"]) # Allow all for testing, restrict in production

# Import Routes
from .admin_routes import admin_bp
from .clients_routes import client_bp

app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(client_bp, url_prefix='/client')

if __name__ == "__main__":
    app.run(debug=True)