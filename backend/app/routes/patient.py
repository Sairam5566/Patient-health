from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import current_user, login_required
from backend.app import db
from backend.app.models import User, Appointment, HealthRecord, DoctorProfile, FileAttachment
from backend.app.forms.patient import AppointmentForm, HealthRecordForm, ProfileForm
from backend.app.utils.file_processor import get_file_processor
from backend.app.utils.notification_utils import get_notification_utils
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from functools import wraps

patient_bp = Blueprint('patient', __name__, url_prefix='/patient')

def patient_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()
        if current_user.role != 'patient':
            flash('Access denied. Patient privileges required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@patient_bp.route('/dashboard')
@patient_required
def dashboard():
    # Get upcoming appointments
    upcoming_appointments = Appointment.query.filter_by(
        user_id=current_user.id,
        status='scheduled'
    ).order_by(Appointment.appointment_date).limit(5).all()
    
    # Get recent health records
    recent_records = HealthRecord.query.join(
        HealthRecord.patient
    ).filter_by(
        user_id=current_user.id
    ).order_by(HealthRecord.created_at.desc()).limit(5).all()
    
    return render_template('patient/dashboard.html',
                         title='Patient Dashboard',
                         appointments=upcoming_appointments,
                         records=recent_records)

@patient_bp.route('/appointments')
@patient_required
def appointments():
    appointments = Appointment.query.filter_by(
        user_id=current_user.id
    ).order_by(Appointment.appointment_date.desc()).all()
    return render_template('patient/appointments.html',
                         title='My Appointments',
                         appointments=appointments)

@patient_bp.route('/book-appointment', methods=['GET', 'POST'])
@patient_required
def book_appointment():
    form = AppointmentForm()
    # Get list of doctors for the form
    doctors = DoctorProfile.query.join(User).all()
    form.doctor.choices = [(d.id, f"Dr. {d.user.first_name} {d.user.last_name} - {d.specialty}") for d in doctors]
    
    if form.validate_on_submit():
        appointment = Appointment(
            user_id=current_user.id,
            doctor_id=form.doctor.data,
            appointment_date=form.appointment_date.data,
            reason=form.reason.data,
            status='scheduled'
        )
        db.session.add(appointment)
        db.session.commit()
        
        # Send notification
        doctor = DoctorProfile.query.get(form.doctor.data)
        notification = get_notification_utils()
        notification.send_appointment_reminder(
            current_user.email,
            f"Dr. {doctor.user.first_name} {doctor.user.last_name}",
            form.appointment_date.data.strftime("%Y-%m-%d %H:%M")
        )
        
        flash('Appointment booked successfully!', 'success')
        return redirect(url_for('patient.appointments'))
    
    return render_template('patient/book_appointment.html',
                         title='Book Appointment',
                         form=form)

@patient_bp.route('/health-records')
@patient_required
def health_records():
    records = HealthRecord.query.join(
        HealthRecord.patient
    ).filter_by(
        user_id=current_user.id
    ).order_by(HealthRecord.created_at.desc()).all()
    return render_template('patient/health_records.html',
                         title='My Health Records',
                         records=records)

@patient_bp.route('/upload-record', methods=['GET', 'POST'])
@patient_required
def upload_record():
    form = HealthRecordForm()
    if form.validate_on_submit():
        if form.file.data:
            file = form.file.data
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Process file
            processor = get_file_processor()
            extracted_data = processor.process_pdf(file_path) if filename.endswith('.pdf') \
                else processor.process_image(file_path)
            
            # Create health record
            record = HealthRecord(
                patient_id=current_user.patient_profile.id,
                record_type=form.record_type.data,
                title=form.title.data,
                content=form.description.data
            )
            db.session.add(record)
            
            # Create file attachment
            attachment = FileAttachment(
                health_record=record,
                filename=filename,
                file_type=file.content_type,
                file_path=file_path,
                extracted_data=extracted_data
            )
            db.session.add(attachment)
            db.session.commit()
            
            flash('Health record uploaded successfully!', 'success')
            return redirect(url_for('patient.health_records'))
    
    return render_template('patient/upload_record.html',
                         title='Upload Health Record',
                         form=form)

@patient_bp.route('/profile', methods=['GET', 'POST'])
@patient_required
def profile():
    form = ProfileForm()
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.email = form.email.data
        current_user.patient_profile.date_of_birth = form.date_of_birth.data
        current_user.patient_profile.phone = form.phone.data
        current_user.patient_profile.address = form.address.data
        db.session.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('patient.profile'))
    elif request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.email.data = current_user.email
        form.date_of_birth.data = current_user.patient_profile.date_of_birth
        form.phone.data = current_user.patient_profile.phone
        form.address.data = current_user.patient_profile.address
    return render_template('patient/profile.html',
                         title='My Profile',
                         form=form) 