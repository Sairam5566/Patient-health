from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, DateTimeField, SubmitField, DateField
from wtforms.validators import DataRequired, Length, Email

class AppointmentForm(FlaskForm):
    doctor = SelectField('Doctor', coerce=int, validators=[DataRequired()])
    appointment_date = DateTimeField('Appointment Date', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    reason = TextAreaField('Reason for Visit', validators=[DataRequired(), Length(min=10, max=500)])
    submit = SubmitField('Book Appointment')

class HealthRecordForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    record_type = SelectField('Record Type', choices=[
        ('lab_result', 'Lab Result'),
        ('prescription', 'Prescription'),
        ('general_note', 'General Note'),
        ('imaging', 'Imaging'),
        ('vaccination', 'Vaccination')
    ], validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=10, max=1000)])
    file = FileField('File', validators=[
        FileRequired(),
        FileAllowed(['pdf', 'jpg', 'jpeg', 'png'], 'Only PDF and image files are allowed!')
    ])
    submit = SubmitField('Upload Record')

class ProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    phone = StringField('Phone Number')
    address = TextAreaField('Address')
    submit = SubmitField('Update Profile') 