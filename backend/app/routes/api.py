from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from backend.app import db
from backend.app.models import User, Appointment, HealthRecord, DoctorProfile, PatientProfile
from datetime import datetime

api_bp = Blueprint('api', __name__)

@api_bp.route('/appointments', methods=['GET'])
@login_required
def get_appointments():
    try:
        if current_user.role == 'doctor':
            appointments = Appointment.query.filter_by(
                doctor_id=current_user.doctor_profile.id
            ).order_by(Appointment.appointment_date.desc()).all()
        else:
            appointments = Appointment.query.filter_by(
                user_id=current_user.id
            ).order_by(Appointment.appointment_date.desc()).all()
        
        return jsonify([{
            'id': a.id,
            'date': a.appointment_date.isoformat(),
            'status': a.status,
            'doctor': f"Dr. {a.doctor.user.first_name} {a.doctor.user.last_name}" if current_user.role == 'patient' else None,
            'patient': f"{a.user.first_name} {a.user.last_name}" if current_user.role == 'doctor' else None,
            'reason': a.reason,
            'notes': a.notes
        } for a in appointments])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/health-records', methods=['GET'])
@login_required
def get_health_records():
    try:
        if current_user.role == 'patient':
            records = HealthRecord.query.join(
                HealthRecord.patient
            ).filter_by(
                user_id=current_user.id
            ).order_by(HealthRecord.created_at.desc()).all()
        else:
            patient_id = request.args.get('patient_id')
            if not patient_id:
                return jsonify({'error': 'Patient ID is required'}), 400
            
            # Verify doctor has access to patient records
            has_appointment = Appointment.query.filter_by(
                doctor_id=current_user.doctor_profile.id,
                user_id=patient_id
            ).first() is not None
            
            if not has_appointment:
                return jsonify({'error': 'Access denied'}), 403
            
            records = HealthRecord.query.join(
                HealthRecord.patient
            ).filter_by(
                user_id=patient_id
            ).order_by(HealthRecord.created_at.desc()).all()
        
        return jsonify([{
            'id': r.id,
            'title': r.title,
            'type': r.record_type,
            'content': r.content,
            'created_at': r.created_at.isoformat(),
            'attachments': [{
                'id': a.id,
                'filename': a.filename,
                'file_type': a.file_type,
                'uploaded_at': a.uploaded_at.isoformat()
            } for a in r.attachments]
        } for r in records])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/doctors', methods=['GET'])
@login_required
def get_doctors():
    try:
        doctors = DoctorProfile.query.join(User).all()
        return jsonify([{
            'id': d.id,
            'name': f"Dr. {d.user.first_name} {d.user.last_name}",
            'specialty': d.specialty,
            'office_hours': d.office_hours
        } for d in doctors])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    try:
        profile = {
            'id': current_user.id,
            'email': current_user.email,
            'first_name': current_user.first_name,
            'last_name': current_user.last_name,
            'role': current_user.role,
            'created_at': current_user.created_at.isoformat()
        }
        
        if current_user.role == 'doctor':
            doctor_profile = current_user.doctor_profile
            profile.update({
                'specialty': doctor_profile.specialty,
                'license_number': doctor_profile.license_number,
                'office_hours': doctor_profile.office_hours
            })
        else:
            patient_profile = current_user.patient_profile
            profile.update({
                'date_of_birth': patient_profile.date_of_birth.isoformat(),
                'blood_type': patient_profile.blood_type,
                'allergies': patient_profile.allergies,
                'medical_history': patient_profile.medical_history,
                'emergency_contact': patient_profile.emergency_contact
            })
        
        return jsonify(profile)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    try:
        if current_user.role == 'doctor':
            total_patients = User.query.join(Appointment).filter(
                Appointment.doctor_id == current_user.doctor_profile.id
            ).distinct().count()
            
            total_appointments = Appointment.query.filter_by(
                doctor_id=current_user.doctor_profile.id
            ).count()
            
            completed_appointments = Appointment.query.filter_by(
                doctor_id=current_user.doctor_profile.id,
                status='completed'
            ).count()
            
            return jsonify({
                'total_patients': total_patients,
                'total_appointments': total_appointments,
                'completed_appointments': completed_appointments,
                'completion_rate': round(completed_appointments / total_appointments * 100, 2) if total_appointments > 0 else 0
            })
        else:
            total_appointments = Appointment.query.filter_by(
                user_id=current_user.id
            ).count()
            
            completed_appointments = Appointment.query.filter_by(
                user_id=current_user.id,
                status='completed'
            ).count()
            
            total_records = HealthRecord.query.join(
                HealthRecord.patient
            ).filter_by(
                user_id=current_user.id
            ).count()
            
            return jsonify({
                'total_appointments': total_appointments,
                'completed_appointments': completed_appointments,
                'total_records': total_records,
                'attendance_rate': round(completed_appointments / total_appointments * 100, 2) if total_appointments > 0 else 0
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500 