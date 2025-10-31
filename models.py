# models.py

from extensions import db  # Import the db instance from our main app.py file
from datetime import datetime

# --- User (Patient) Model ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    
    # This relationship links appointments to the user
    # 'lazy=True' means SQLAlchemy will load the data as needed
    appointments = db.relationship('Appointment', backref='patient', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

# --- Doctor Model ---
class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    specialty = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text, nullable=True) # A short biography
    
    # This relationship links appointments to the doctor
    appointments = db.relationship('Appointment', backref='doctor', lazy=True)

    def __repr__(self):
        return f'<Doctor {self.full_name} - {self.specialty}>'

# --- Appointment Model ---
class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys link this table to other tables
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    
    appointment_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='Confirmed') # e.g., "Confirmed", "Cancelled"

    def __repr__(self):
        return f'<Appointment {self.id} - {self.status}>'