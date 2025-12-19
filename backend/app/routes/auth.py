# Authentication routes
from flask import Blueprint, request, jsonify

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@bp.route('/login', methods=['POST'])
def login():
    # Login logic here
    return jsonify({"message": "Login successful"}), 200

@bp.route('/register', methods=['POST'])
def register():
    # Registration logic here
    return jsonify({"message": "User registered successfully"}), 201