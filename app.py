import os
import pandas as pd
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import sqlite3

# --- Flask App Configuration ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_very_secret_key' # Replace with a real secret key
app.config['DATABASE'] = 'hospital.db'

# --- Database Setup ---
def init_db():
    """Initializes the database from schema.sql."""
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = sqlite3.connect(
            app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.sqlite_db.row_factory = sqlite3.Row
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

# --- ML Model Integration ---
# Mock data for training the ML model
data = {
    'patient_id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] * 50,
    'last_appointment_missed': [0, 1, 0, 0, 1, 0, 0, 1, 0, 0] * 50,
    'appointment_hour': [9, 10, 11, 14, 15, 9, 10, 11, 14, 15] * 50,
    'appointment_day_of_week': [1, 2, 3, 4, 5, 1, 2, 3, 4, 5] * 50,
    'is_no_show': [0, 1, 0, 0, 1, 0, 0, 1, 0, 0] * 50
}
df = pd.DataFrame(data)
X = df[['last_appointment_missed', 'appointment_hour', 'appointment_day_of_week']]
y = df['is_no_show']
model = RandomForestClassifier(random_state=42)
model.fit(X, y)
# Helper function for model prediction
def predict_no_show(last_missed, appointment_hour, appointment_day_of_week):
    prediction = model.predict([[last_missed, appointment_hour, appointment_day_of_week]])
    return prediction[0]

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register_patient', methods=['GET', 'POST'])
def register_patient():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='scrypt')
        
        db = get_db()
        db.execute(
            'INSERT INTO patients (name, email, password) VALUES (?, ?, ?)',
            (name, email, hashed_password)
        )
        db.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('index'))
    return render_template('register_patient.html')

@app.route('/register_doctor', methods=['GET', 'POST'])
def register_doctor():
    if request.method == 'POST':
        name = request.form['name']
        specialty = request.form['specialty']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='scrypt')

        db = get_db()
        db.execute(
            'INSERT INTO doctors (name, specialty, email, password) VALUES (?, ?, ?)',
            (name, specialty, email, hashed_password)
        )
        db.commit()
        flash('Doctor registration successful! Please log in.', 'success')
        return redirect(url_for('index'))
    return render_template('register_doctor.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user_type = request.form['user_type']
        db = get_db()
        
        if user_type == 'patient':
            user = db.execute('SELECT * FROM patients WHERE email = ?', (email,)).fetchone()
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['user_type'] = 'patient'
                flash('Logged in successfully as a patient.', 'success')
                return redirect(url_for('patient_dashboard'))
            else:
                flash('Invalid email or password for patient.', 'danger')
        
        elif user_type == 'doctor':
            user = db.execute('SELECT * FROM doctors WHERE email = ?', (email,)).fetchone()
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['user_type'] = 'doctor'
                flash('Logged in successfully as a doctor.', 'success')
                return redirect(url_for('doctor_dashboard'))
            else:
                flash('Invalid email or password for doctor.', 'danger')

    return redirect(url_for('index'))

@app.route('/patient_dashboard')
def patient_dashboard():
    if 'user_id' not in session or session['user_type'] != 'patient':
        return redirect(url_for('index'))
    
    db = get_db()
    patient_id = session['user_id']
    patient = db.execute('SELECT * FROM patients WHERE id = ?', (patient_id,)).fetchone()
    
    appointments = db.execute(
        'SELECT a.appointment_date, a.appointment_time, a.status, d.name AS doctor_name, d.specialty FROM appointments a JOIN doctors d ON a.doctor_id = d.id WHERE a.patient_id = ? ORDER BY a.appointment_date DESC',
        (patient_id,)
    ).fetchall()

    doctors = db.execute('SELECT id, name, specialty FROM doctors').fetchall()

    return render_template('patient_dashboard.html', patient=patient, appointments=appointments, doctors=doctors)

@app.route('/doctor_dashboard')
def doctor_dashboard():
    if 'user_id' not in session or session['user_type'] != 'doctor':
        return redirect(url_for('index'))
    
    db = get_db()
    doctor_id = session['user_id']
    doctor = db.execute('SELECT * FROM doctors WHERE id = ?', (doctor_id,)).fetchone()
    
    pending_appointments = db.execute(
        'SELECT a.id, a.appointment_date, a.appointment_time, p.name AS patient_name FROM appointments a JOIN patients p ON a.patient_id = p.id WHERE a.doctor_id = ? AND a.status = "pending" ORDER BY a.appointment_date ASC',
        (doctor_id,)
    ).fetchall()
    
    return render_template('doctor_dashboard.html', doctor=doctor, pending_appointments=pending_appointments)

@app.route('/book_appointment', methods=['POST'])
def book_appointment():
    if 'user_id' not in session or session['user_type'] != 'patient':
        return redirect(url_for('index'))
    
    patient_id = session['user_id']
    doctor_id = request.form['doctor_id']
    appointment_date = request.form['appointment_date']
    appointment_time = request.form['appointment_time']
    
    db = get_db()
    
    # Check for existing appointment
    existing_appointment = db.execute(
        'SELECT * FROM appointments WHERE doctor_id = ? AND appointment_date = ? AND appointment_time = ?',
        (doctor_id, appointment_date, appointment_time)
    ).fetchone()
    if existing_appointment:
        flash('This appointment slot is already taken.', 'danger')
        return redirect(url_for('patient_dashboard'))

    # Simple ML model prediction for no-show risk
    # This is a basic example; a real-world model would be more complex
    last_missed = 0 # Assume no previous missed appointments for this simple example
    appointment_hour = datetime.strptime(appointment_time, '%H:%M').hour
    appointment_day_of_week = datetime.strptime(appointment_date, '%Y-%m-%d').weekday() + 1
    
    no_show_risk = predict_no_show(last_missed, appointment_hour, appointment_day_of_week)
    
    db.execute(
        'INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, no_show_risk) VALUES (?, ?, ?, ?, ?)',
        (patient_id, doctor_id, appointment_date, appointment_time, no_show_risk)
    )
    db.commit()
    
    if no_show_risk == 1:
        flash('Appointment booked, but patient is flagged as a potential no-show.', 'warning')
    else:
        flash('Appointment booked successfully.', 'success')

    return redirect(url_for('patient_dashboard'))

@app.route('/update_appointment_status/<int:appointment_id>', methods=['POST'])
def update_appointment_status(appointment_id):
    if 'user_id' not in session or session['user_type'] != 'doctor':
        return redirect(url_for('index'))
    
    status = request.form['status']
    db = get_db()
    db.execute('UPDATE appointments SET status = ? WHERE id = ?', (status, appointment_id))
    db.commit()
    flash(f'Appointment {status} successfully.', 'success')
    return redirect(url_for('doctor_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    from flask import g
    if not os.path.exists('hospital.db'):
        print("Creating database...")
        init_db()
    app.run(debug=True)
