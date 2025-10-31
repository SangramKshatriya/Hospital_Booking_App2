# api.py

from flask import Blueprint, jsonify, request
from models import Doctor, Appointment, User
from extensions import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

# Create a Blueprint
api_bp = Blueprint('api', __name__)

# --- Doctor Routes ---

@api_bp.route('/doctors', methods=['GET'])
def get_doctors():
    """Gets a list of all doctors, optionally filtered by specialty."""
    
    # Check if a 'specialty' query parameter was provided
    specialty = request.args.get('specialty')
    
    if specialty:
        # Filter by specialty
        doctors = Doctor.query.filter_by(specialty=specialty).all()
    else:
        # Get all doctors
        doctors = Doctor.query.all()
        
    # Convert doctor objects to a list of dictionaries
    doctor_list = []
    for doc in doctors:
        doctor_list.append({
            "id": doc.id,
            "full_name": doc.full_name,
            "specialty": doc.specialty,
            "bio": doc.bio
        })
        
    return jsonify(doctors=doctor_list), 200


@api_bp.route('/doctors/<int:doctor_id>', methods=['GET'])
def get_doctor(doctor_id):
    """Gets details for a single doctor by their ID."""
    
    # .get_or_404() is a handy shortcut:
    # It tries to get the doctor, or returns a 404 Not Found error if the ID doesn't exist.
    doc = Doctor.query.get_or_404(doctor_id)
    
    return jsonify({
        "id": doc.id,
        "full_name": doc.full_name,
        "specialty": doc.specialty,
        "bio": doc.bio
    }), 200

# We will add appointment routes here later...

# api.py (at the end of the file)

# ... (your /doctors routes are here) ...

# --- Appointment Routes ---

@api_bp.route('/appointments', methods=['POST'])
@jwt_required() # This decorator protects the route
def book_appointment():
    """Books an appointment for the currently logged-in user."""
    
    # Get the ID of the logged-in user from their token
    current_user_id = get_jwt_identity()
    
    # Get data from the request
    data = request.get_json()
    doctor_id = data.get('doctor_id')
    time_string = data.get('appointment_time') # e.g., "2025-11-20T14:30:00"

    # --- Validation ---
    if not doctor_id or not time_string:
        return jsonify({"error": "doctor_id and appointment_time are required"}), 400

    # Check if doctor exists
    if not Doctor.query.get(doctor_id):
        return jsonify({"error": "Doctor not found"}), 404

    # Try to parse the time string
    try:
        # fromisoformat() is the standard way to parse strings like "2025-11-20T14:30:00"
        appointment_time = datetime.fromisoformat(time_string)
    except ValueError:
        return jsonify({"error": "Invalid time format. Use ISO 8601 (YYYY-MM-DDTHH:MM:SS)"}), 400
        
    # Check if this exact time slot is already booked for this doctor
    existing_appt = Appointment.query.filter_by(
        doctor_id=doctor_id, 
        appointment_time=appointment_time
    ).first()
    
    if existing_appt:
        return jsonify({"error": "This time slot is already booked"}), 409
    # --- End Validation ---

    # Create the new appointment
    new_appt = Appointment(
        user_id=current_user_id,
        doctor_id=doctor_id,
        appointment_time=appointment_time,
        status="Confirmed"
    )
    
    # Add to database
    db.session.add(new_appt)
    db.session.commit()
    
    return jsonify({
        "message": "Appointment booked successfully!",
        "appointment_id": new_appt.id
    }), 201


@api_bp.route('/appointments', methods=['GET'])
@jwt_required()
def get_my_appointments():
    """Gets all appointments for the currently logged-in user."""
    
    current_user_id = get_jwt_identity()
    
    # Find all appointments for this user
    appointments = Appointment.query.filter_by(user_id=current_user_id).order_by(Appointment.appointment_time.asc()).all()
    
    results = []
    for appt in appointments:
        # Find the doctor for this appointment to include their name
        doc = Doctor.query.get(appt.doctor_id)
        results.append({
            "id": appt.id,
            "doctor_name": doc.full_name if doc else "Unknown",
            "specialty": doc.specialty if doc else "Unknown",
            "appointment_time": appt.appointment_time.isoformat(), # Use .isoformat() for a standard string
            "status": appt.status
        })
        
    return jsonify(appointments=results), 200

# api.py
# ... (all your other imports and routes are here) ...

@api_bp.route('/appointments/<int:appointment_id>', methods=['DELETE'])
@jwt_required()
def cancel_appointment(appointment_id):
    """Cancels an appointment for the currently logged-in user."""
    
    # Get the ID of the logged-in user from their token
    current_user_id = int(get_jwt_identity())
    
    # Find the appointment, or return 404 if it doesn't exist
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # --- Security Check ---
    # Make sure the person deleting the appointment is the one who made it
    if appointment.user_id != current_user_id:
        return jsonify({"error": "Unauthorized. You can only cancel your own appointments."}), 403
        
    try:
        # Delete the appointment from the database
        db.session.delete(appointment)
        db.session.commit()
        
        return jsonify({"message": "Appointment cancelled successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to cancel appointment", "details": str(e)}), 500