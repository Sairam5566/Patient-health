from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import current_user, login_required
from backend.app import db
from backend.app.models import User, Appointment, HealthRecord, PatientProfile
from backend.app.forms.doctor import AppointmentNoteForm, HealthRecordForm, DoctorProfileForm
from backend.app.utils.notification_utils import get_notification_utils
from datetime import datetime, timedelta
from functools import wraps

doctor_bp = Blueprint('doctor', __name__, url_prefix='/doctor')

def doctor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()
        if current_user.role != 'doctor':
            flash('Access denied. Doctor privileges required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@doctor_bp.route('/dashboard')
@doctor_required
def dashboard():
    # Get today's appointments
    today = datetime.now().date()
    today_appointments = Appointment.query.filter(
        Appointment.doctor_id == current_user.doctor_profile.id,
        Appointment.appointment_date >= today,
        Appointment.appointment_date < today + timedelta(days=1)
    ).order_by(Appointment.appointment_date).all()
    
    # Get upcoming appointments
    upcoming_appointments = Appointment.query.filter(
        Appointment.doctor_id == current_user.doctor_profile.id,
        Appointment.appointment_date >= today + timedelta(days=1),
        Appointment.status == 'scheduled'
    ).order_by(Appointment.appointment_date).limit(5).all()
    
    return render_template('doctor/dashboard.html',
                         title='Doctor Dashboard',
                         today_appointments=today_appointments,
                         upcoming_appointments=upcoming_appointments)

@doctor_bp.route('/appointments')
@doctor_required
def appointments():
    appointments = Appointment.query.filter_by(
        doctor_id=current_user.doctor_profile.id
    ).order_by(Appointment.appointment_date.desc()).all()
    return render_template('doctor/appointments.html',
                         title='My Appointments',
                         appointments=appointments)

@doctor_bp.route('/appointment/<int:id>', methods=['GET', 'POST'])
@doctor_required
def appointment_detail(id):
    appointment = Appointment.query.get_or_404(id)
    if appointment.doctor_id != current_user.doctor_profile.id:
        flash('Access denied. This appointment belongs to another doctor.', 'danger')
        return redirect(url_for('doctor.appointments'))
    
    form = AppointmentNoteForm()
    if form.validate_on_submit():
        appointment.notes = form.notes.data
        appointment.status = form.status.data
        db.session.commit()
        
        # Send notification if appointment is completed
        if form.status.data == 'completed':
            notification = get_notification_utils()
            notification.send_email(
                appointment.user.email,
                'Appointment Completed',
                f'Your appointment with Dr. {current_user.first_name} {current_user.last_name} has been completed. Please check your health records for any updates.'
            )
        
        flash('Appointment updated successfully!', 'success')
        return redirect(url_for('doctor.appointments'))
    
    elif request.method == 'GET':
        form.notes.data = appointment.notes
        form.status.data = appointment.status
    
    return render_template('doctor/appointment_detail.html',
                         title='Appointment Detail',
                         appointment=appointment,
                         form=form)

@doctor_bp.route('/patients')
@doctor_required
def patients():
    # Get unique patients who have appointments with this doctor
    patients = User.query.join(Appointment).filter(
        Appointment.doctor_id == current_user.doctor_profile.id
    ).distinct().all()
    return render_template('doctor/patients.html',
                         title='My Patients',
                         patients=patients)

@doctor_bp.route('/patient/<int:id>')
@doctor_required
def patient_detail(id):
    patient = User.query.get_or_404(id)
    if not patient.role == 'patient':
        flash('Invalid patient ID.', 'danger')
        return redirect(url_for('doctor.patients'))
    
    # Check if doctor has seen this patient
    has_appointment = Appointment.query.filter_by(
        doctor_id=current_user.doctor_profile.id,
        user_id=patient.id
    ).first() is not None
    
    if not has_appointment:
        flash('Access denied. This patient has not had an appointment with you.', 'danger')
        return redirect(url_for('doctor.patients'))
    
    appointments = Appointment.query.filter_by(
        doctor_id=current_user.doctor_profile.id,
        user_id=patient.id
    ).order_by(Appointment.appointment_date.desc()).all()
    
    health_records = HealthRecord.query.join(
        HealthRecord.patient
    ).filter_by(
        user_id=patient.id
    ).order_by(HealthRecord.created_at.desc()).all()
    
    return render_template('doctor/patient_detail.html',
                         title=f'Patient: {patient.first_name} {patient.last_name}',
                         patient=patient,
                         appointments=appointments,
                         health_records=health_records)

@doctor_bp.route('/add-health-record/<int:patient_id>', methods=['GET', 'POST'])
@doctor_required
def add_health_record(patient_id):
    patient = User.query.get_or_404(patient_id)
    if not patient.role == 'patient':
        flash('Invalid patient ID.', 'danger')
        return redirect(url_for('doctor.patients'))
    
    # Check if doctor has seen this patient
    has_appointment = Appointment.query.filter_by(
        doctor_id=current_user.doctor_profile.id,
        user_id=patient.id
    ).first() is not None
    
    if not has_appointment:
        flash('Access denied. This patient has not had an appointment with you.', 'danger')
        return redirect(url_for('doctor.patients'))
    
    form = HealthRecordForm()
    if form.validate_on_submit():
        record = HealthRecord(
            patient_id=patient.patient_profile.id,
            record_type=form.record_type.data,
            title=form.title.data,
            content=form.content.data
        )
        db.session.add(record)
        db.session.commit()
        
        # Send notification
        notification = get_notification_utils()
        notification.send_email(
            patient.email,
            'New Health Record Added',
            f'Dr. {current_user.first_name} {current_user.last_name} has added a new health record to your profile.'
        )
        
        flash('Health record added successfully!', 'success')
        return redirect(url_for('doctor.patient_detail', id=patient.id))
    
    return render_template('doctor/add_health_record.html',
                         title=f'Add Health Record for {patient.first_name} {patient.last_name}',
                         form=form,
                         patient=patient)

@doctor_bp.route('/profile', methods=['GET', 'POST'])
@doctor_required
def profile():
    form = DoctorProfileForm()
    if form.validate_on_submit():
        current_user.doctor_profile.specialty = form.specialty.data
        current_user.doctor_profile.license_number = form.license_number.data
        current_user.doctor_profile.office_hours = form.office_hours.data
        current_user.doctor_profile.phone = form.phone.data
        current_user.doctor_profile.address = form.address.data
        current_user.doctor_profile.hospital_affiliation = form.hospital_affiliation.data
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('doctor.profile'))
    elif request.method == 'GET':
        form.specialty.data = current_user.doctor_profile.specialty
        form.license_number.data = current_user.doctor_profile.license_number
        form.office_hours.data = current_user.doctor_profile.office_hours
        form.phone.data = current_user.doctor_profile.phone
        form.address.data = current_user.doctor_profile.address
        form.hospital_affiliation.data = current_user.doctor_profile.hospital_affiliation

    # Get statistics for the doctor
    total_patients = User.query.join(Appointment).filter(
        Appointment.doctor_id == current_user.doctor_profile.id
    ).distinct().count()

    total_appointments = Appointment.query.filter_by(
        doctor_id=current_user.doctor_profile.id
    ).count()

    # Get appointments for the current month
    today = datetime.now()
    first_day = today.replace(day=1)
    if today.month == 12:
        next_month = today.replace(year=today.year + 1, month=1, day=1)
    else:
        next_month = today.replace(month=today.month + 1, day=1)
    
    appointments_this_month = Appointment.query.filter(
        Appointment.doctor_id == current_user.doctor_profile.id,
        Appointment.appointment_date >= first_day,
        Appointment.appointment_date < next_month
    ).count()

    return render_template('doctor/profile.html',
                         title='My Profile',
                         doctor=current_user,
                         form=form,
                         total_patients=total_patients,
                         total_appointments=total_appointments,
                         appointments_this_month=appointments_this_month) 