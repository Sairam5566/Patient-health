from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import json
from config import Config
from encryption_utils import get_encryption_utils
from notification_utils import get_notification_utils
from file_processor import get_file_processor

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
mail = Mail(app)

encryption_utils = get_encryption_utils()
notification_utils = get_notification_utils()
file_processor = get_file_processor()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    records = db.relationship('HealthRecord', backref='user', lazy=True)
    appointments_as_patient = db.relationship('Appointment', backref='patient', lazy=True, foreign_keys='Appointment.user_id')
    appointments_as_doctor = db.relationship('Appointment', backref='doctor', lazy=True, foreign_keys='Appointment.doctor_id')

class HealthRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    record_type = db.Column(db.String(50), nullable=False)
    file_path = db.Column(db.String(200), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    record_metadata = db.Column(db.Text, nullable=False)
    is_public = db.Column(db.Boolean, default=False)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    appointment_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        flash('Invalid email or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
            
        # Hash the password using SHA256
        password_hash = generate_password_hash(password, method='sha256')
        
        user = User(
            email=email,
            password_hash=password_hash,
            role=role
        )
        db.session.add(user)
        db.session.commit()
        
        # Generate audit log
        audit_log = encryption_utils.generate_audit_log(
            "user_registration",
            user.id
        )
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@app.route('/upload_record', methods=['POST'])
@login_required
def upload_record():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
        
    file = request.files['file']
    record_type = request.form.get('record_type')
    
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
        
    if file and file.filename.split('.')[-1].lower() in Config.ALLOWED_FILE_TYPES:
        # Process file based on type
        upload_dir = Config.UPLOAD_FOLDER
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{upload_dir}/{timestamp}_{current_user.id}_{record_type}"
        ext = file.filename.split('.')[-1].lower()
        filename += f".{ext}"
        
        # Save and encrypt file
        file.save(filename)
        encrypted_filename = filename + ".enc"
        encryption_utils.encrypt_file(filename, encrypted_filename)
        os.remove(filename)
        
        # Process file content
        analysis = {}
        if ext == "pdf":
            analysis = file_processor.process_pdf(filename)
        elif ext in ["png", "jpg", "jpeg"]:
            analysis = file_processor.process_image(filename)
        
        # Create database record
        record = HealthRecord(
            user_id=current_user.id,
            record_type=record_type,
            file_path=encrypted_filename,
            record_metadata=encryption_utils.encrypt_data(json.dumps(analysis)),
            is_public=False
        )
        db.session.add(record)
        db.session.commit()
        
        # Generate audit log
        audit_log = encryption_utils.generate_audit_log(
            "record_upload",
            current_user.id,
            record.id
        )
        
        flash('Record uploaded successfully!')
        return redirect(url_for('dashboard'))
    
    flash('Invalid file type')
    return redirect(request.url)

@app.route('/appointments')
@login_required
def appointments():
    if current_user.role == 'doctor':
        return redirect(url_for('doctor_appointments'))
    
    appointments = current_user.appointments_as_patient
    return render_template('appointments.html', appointments=appointments)

@app.route('/cancel_appointment/<int:appointment_id>', methods=['POST'])
@login_required
def cancel_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Check if the user has permission to cancel this appointment
    if appointment.user_id != current_user.id and appointment.doctor_id != current_user.id:
        flash('You do not have permission to cancel this appointment')
        return redirect(url_for('appointments'))
    
    # Get the other party's email for notification
    notify_user = User.query.get(appointment.doctor_id if current_user.id == appointment.user_id else appointment.user_id)
    
    # Update appointment status
    appointment.status = 'cancelled'
    db.session.commit()
    
    # Send notification
    if notify_user:
        subject = "Appointment Cancelled"
        message = f"The appointment scheduled for {appointment.appointment_date.strftime('%Y-%m-%d %H:%M')} has been cancelled."
        notification_utils.send_email(notify_user.email, subject, message)
    
    # Generate audit log
    audit_log = encryption_utils.generate_audit_log(
        "appointment_cancellation",
        current_user.id,
        appointment.id
    )
    
    flash('Appointment cancelled successfully')
    return redirect(url_for('appointments' if current_user.role != 'doctor' else 'doctor_appointments'))

@app.route('/book_appointment', methods=['POST'])
@login_required
def book_appointment():
    if current_user.role == 'doctor':
        flash('Doctors cannot book appointments')
        return redirect(url_for('appointments'))
        
    doctor_id = request.form.get('doctor_id')
    appointment_date = request.form.get('appointment_date')
    
    try:
        appointment_date = datetime.fromisoformat(appointment_date)
        if appointment_date < datetime.now():
            flash('Appointment date must be in the future')
            return redirect(url_for('appointments'))
            
        appointment = Appointment(
            user_id=current_user.id,
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            status='pending'
        )
        db.session.add(appointment)
        db.session.commit()
        
        # Get doctor's email
        doctor = User.query.get(doctor_id)
        if doctor:
            # Send appointment confirmation
            notification_utils.send_appointment_reminder(
                current_user.email,
                f"Doctor {doctor.email.split('@')[0]}",
                appointment_date.strftime("%Y-%m-%d %H:%M")
            )
            
            # Start reminder thread
            notification_utils.start_reminder_thread(
                appointment_date,
                current_user.email,
                doctor.email.split('@')[0]
            )
        
        # Generate audit log
        audit_log = encryption_utils.generate_audit_log(
            "appointment_creation",
            current_user.id,
            appointment.id
        )
        
        flash('Appointment booked successfully!')
        return redirect(url_for('appointments'))
    except Exception as e:
        flash(f'Error booking appointment: {str(e)}')
        return redirect(url_for('appointments'))

@app.route('/doctor_appointments')
@login_required
def doctor_appointments():
    if current_user.role != 'doctor':
        return redirect(url_for('appointments'))
        
    appointments = current_user.appointments_as_doctor
    return render_template('doctor_appointments.html', appointments=appointments)

@app.route('/analyze/<int:patient_id>')
@login_required
def analyze_health(patient_id):
    if current_user.role != 'doctor' and current_user.role != 'admin':
        return redirect(url_for('dashboard'))
        
    records = HealthRecord.query.filter_by(user_id=patient_id).all()
    
    # Get all decrypted metadata
    all_metadata = []
    for record in records:
        decrypted_metadata = encryption_utils.decrypt_data(record.record_metadata)
        all_metadata.append(json.loads(decrypted_metadata))
    
    # Perform comprehensive analysis
    analysis = {
        "blood_pressure": {
            "current": "",
            "history": [],
            "trend": "",
            "status": ""
        },
        "cholesterol": {
            "current": "",
            "history": [],
            "trend": "",
            "status": ""
        },
        "glucose": {
            "current": "",
            "history": [],
            "trend": "",
            "status": ""
        },
        "heart_rate": {
            "current": "",
            "history": [],
            "trend": "",
            "status": ""
        }
    }
    
    # Analyze each metric
    for metric in ["blood_pressure", "cholesterol", "glucose", "heart_rate"]:
        for meta in all_metadata:
            if metric in meta:
                analysis[metric]["history"].append({
                    "value": meta[metric]["value"],
                    "status": meta[metric]["status"],
                    "date": record.upload_date
                })
                
                # Update current value
                if not analysis[metric]["current"]:
                    analysis[metric]["current"] = meta[metric]["value"]
                    analysis[metric]["status"] = meta[metric]["status"]
        
        # Generate trend analysis
        if len(analysis[metric]["history"]) > 1:
            analysis[metric]["trend"] = "Stable"
            if len(analysis[metric]["history"]) >= 3:
                last_three = analysis[metric]["history"][-3:]
                if all(x["status"] == "High" for x in last_three):
                    analysis[metric]["trend"] = "Increasing"
                elif all(x["status"] == "Low" for x in last_three):
                    analysis[metric]["trend"] = "Decreasing"
    
    # Generate audit log
    audit_log = encryption_utils.generate_audit_log(
        "health_analysis",
        current_user.id
    )
    
    return render_template('health_analysis.html', analysis=analysis)

@app.route('/search')
@login_required
def search_patients():
    if current_user.role != 'doctor' and current_user.role != 'admin':
        return redirect(url_for('dashboard'))
        
    query = request.args.get('query', '')
    
    # Search by email or record content
    patients = []
    users = User.query.filter(User.email.like(f"%{query}%"), User.role == "patient").all()
    
    for user in users:
        records = HealthRecord.query.filter_by(user_id=user.id).all()
        for record in records:
            decrypted_metadata = encryption_utils.decrypt_data(record.record_metadata)
            if query.lower() in json.loads(decrypted_metadata).values():
                patients.append({
                    "patient_id": user.id,
                    "email": user.email,
                    "last_record_date": record.upload_date
                })
                break
    
    return render_template('search_results.html', patients=patients)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
