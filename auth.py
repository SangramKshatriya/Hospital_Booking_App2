# auth.py

from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token

from models import User
from extensions import db

# Create a Blueprint
auth_bp = Blueprint('auth', __name__)

# --- Registration Route ---
@auth_bp.route('/register', methods=['POST'])
def register():
    # Get data from the request's JSON body
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # Basic validation
    if not username or not email or not password:
        return jsonify({"error": "Username, email, and password are required"}), 400

    # Check if user already exists
    if User.query.filter_by(email=email).first() or User.query.filter_by(username=username).first():
        return jsonify({"error": "Email or username already exists"}), 409

    # Hash the password for security
    hashed_password = generate_password_hash(password)

    # Create new user object
    new_user = User(
        username=username,
        email=email,
        password_hash=hashed_password
    )

    # Add to database
    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create user", "details": str(e)}), 500

    return jsonify({"message": f"User {username} created successfully"}), 201

# --- Login Route ---
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    # Find user by email
    user = User.query.filter_by(email=email).first()

    # Check if user exists and password is correct
    if user and check_password_hash(user.password_hash, password):
        # Create a new token (JWT)
        # This is the NEW line
        access_token = create_access_token(identity=str(user.id))
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401