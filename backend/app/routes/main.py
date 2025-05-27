from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import current_user, login_required
from backend.app.models import User, Appointment, HealthRecord

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'doctor':
            return redirect(url_for('doctor.dashboard'))
        elif current_user.role == 'patient':
            return redirect(url_for('patient.dashboard'))
        else:
            flash('Invalid user role. Please contact support.', 'danger')
            return render_template('main/index.html', title='Welcome')
    return render_template('main/index.html', title='Welcome')

@main_bp.route('/about')
def about():
    return render_template('main/about.html', title='About Us')

@main_bp.route('/contact')
def contact():
    return render_template('main/contact.html', title='Contact Us')

@main_bp.route('/services')
def services():
    return render_template('main/services.html', title='Our Services')

@main_bp.route('/privacy')
def privacy():
    return render_template('main/privacy.html', title='Privacy Policy')

@main_bp.route('/terms')
def terms():
    return render_template('main/terms.html', title='Terms of Service') 