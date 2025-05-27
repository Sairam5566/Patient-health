from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from backend.app import db
from backend.app.models import User, DoctorProfile, PatientProfile
from backend.app.forms.auth import LoginForm, RegistrationForm, DoctorRegistrationForm
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Clear any existing session
    if '_user_id' in session:
        session.pop('_user_id')
    if '_fresh' in session:
        session.pop('_fresh')
    
    if current_user.is_authenticated:
        if current_user.role == 'doctor':
            return redirect(url_for('doctor.dashboard'))
        elif current_user.role == 'patient':
            return redirect(url_for('patient.dashboard'))
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('auth.login'))
        
        # Login user with remember me option
        login_user(user, remember=form.remember_me.data)
        
        # Get the next page from args, defaulting to appropriate dashboard
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            if user.role == 'doctor':
                return redirect(url_for('doctor.dashboard'))
            elif user.role == 'patient':
                return redirect(url_for('patient.dashboard'))
            return redirect(url_for('main.index'))
        
        # Redirect to next page
        return redirect(next_page)
    
    return render_template('auth/login.html', title='Sign In', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role='patient'
        )
        user.set_password(form.password.data)
        
        # Create patient profile
        profile = PatientProfile(
            user=user,
            date_of_birth=form.date_of_birth.data,
            blood_type=form.blood_type.data,
            allergies=form.allergies.data,
            medical_history=form.medical_history.data,
            emergency_contact=form.emergency_contact.data
        )
        
        db.session.add(user)
        db.session.add(profile)
        db.session.commit()
        
        flash('Congratulations, you are now a registered patient!', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='Register', form=form)

@auth_bp.route('/register/doctor', methods=['GET', 'POST'])
def register_doctor():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = DoctorRegistrationForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role='doctor'
        )
        user.set_password(form.password.data)
        
        # Create doctor profile
        profile = DoctorProfile(
            user=user,
            specialty=form.specialty.data,
            license_number=form.license_number.data,
            office_hours=form.office_hours.data
        )
        
        db.session.add(user)
        db.session.add(profile)
        db.session.commit()
        
        flash('Congratulations, you are now a registered doctor!', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register_doctor.html', title='Register as Doctor', form=form) 