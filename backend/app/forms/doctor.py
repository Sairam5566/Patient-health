from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length

class AppointmentNoteForm(FlaskForm):
    notes = TextAreaField('Notes', validators=[DataRequired(), Length(min=10, max=1000)])
    status = SelectField('Status', choices=[
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show')
    ], validators=[DataRequired()])
    submit = SubmitField('Update Appointment')

class HealthRecordForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    record_type = SelectField('Record Type', choices=[
        ('lab_result', 'Lab Result'),
        ('prescription', 'Prescription'),
        ('general_note', 'General Note'),
        ('diagnosis', 'Diagnosis'),
        ('treatment_plan', 'Treatment Plan')
    ], validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired(), Length(min=10, max=2000)])
    submit = SubmitField('Add Health Record')

class DoctorProfileForm(FlaskForm):
    specialty = StringField('Specialty', validators=[DataRequired(), Length(max=100)])
    license_number = StringField('License Number', validators=[DataRequired(), Length(max=50)])
    office_hours = TextAreaField('Office Hours', validators=[Length(max=200)])
    phone = StringField('Phone Number', validators=[Length(max=20)])
    address = TextAreaField('Address')
    hospital_affiliation = StringField('Hospital Affiliation', validators=[Length(max=100)])
    submit = SubmitField('Update Profile') 