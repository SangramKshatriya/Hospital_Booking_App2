# app.py

import os
from flask import Flask
# Import extensions from our new file
from extensions import db, migrate, jwt 

# --- IMPORTANT ---
# We must import the models here *after* db is defined
# so that Flask-Migrate can "see" them.
import models 
import click
from flask_cors import CORS
from auth import auth_bp
from api import api_bp

def create_app():
    # --- App Configuration ---
    app = Flask(__name__)
    CORS(app)
    
    basedir = os.path.abspath(os.path.dirname(__file__))

    # Configure the database
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'app.db')
    # app.py

# ... (right after 'basedir = ...' line)

# Check if we are in production (on Render)
is_production = os.environ.get('RENDER', False)

if is_production:
    # Use the Render PostgreSQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
else:
    # Use the local SQLite database for development
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'app.db')

# ... (the rest of your config) ...
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Configure JWT
    app.config['JWT_SECRET_KEY'] = 'my-super-secret-key' 
    print(f"--- JWT Secret Key has been set to: {app.config['JWT_SECRET_KEY']} ---")

    # --- Initialize Extensions with App ---
    # The extensions were created in extensions.py
    # Now we just initialize them with our app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Create the 'instance' folder
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # --- Test Route ---
    @app.route('/')
    def hello():
        return "Hospital Booking API is running!"
    
    # --- Register Blueprints ---
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp, url_prefix='/api') # <-- 3. REGISTER IT

    # --- Add a CLI Command to Seed the Database ---
    @app.cli.command("seed-db")
    def seed_db():
        """Adds some dummy doctors to the database."""
        
        from models import Doctor
        # Create dummy doctors
        doc1 = Doctor(full_name="Dr. Alice Smith", specialty="Cardiology", bio="Expert in heart health.")
        doc2 = Doctor(full_name="Dr. Bob Johnson", specialty="Dermatology", bio="Specializes in skin care.")
        doc3 = Doctor(full_name="Dr. Carol Williams", specialty="Pediatrics", bio="Loves working with children.")

        # Add them to the session
        db.session.add(doc1)
        db.session.add(doc2)
        db.session.add(doc3)
        
        # Commit the changes
        db.session.commit()
        print("Database seeded with 3 doctors!")
    # We will register our blueprints (routes) here later
    
    return app

# This allows us to run the app using 'python app.py'
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)