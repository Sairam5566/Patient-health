import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import threading
import json
import os
from config import Config

class NotificationUtils:
    def __init__(self):
        self.smtp_server = Config.MAIL_SERVER
        self.smtp_port = Config.MAIL_PORT
        self.sender_email = Config.MAIL_USERNAME
        self.sender_password = Config.MAIL_PASSWORD

    def send_email(self, recipient: str, subject: str, message: str):
        """Send email notification"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            print(f"Email error: {str(e)}")
            return False

    def send_appointment_reminder(self, patient_email: str, doctor_name: str, appointment_date: str):
        """Send appointment reminder"""
        subject = f"Appointment Reminder - {doctor_name}"
        message = f"Dear Patient,\n\nYou have an appointment with Dr. {doctor_name} on {appointment_date}.\nPlease arrive 15 minutes early for your appointment.\n\nBest regards,\nHealth Records System"
        
        self.send_email(patient_email, subject, message)

    def send_health_alert(self, patient_email: str, alert_type: str, value: str):
        """Send health alert notification"""
        subject = f"Health Alert: {alert_type}"
        message = f"Dear Patient,\n\nWe have detected an abnormal {alert_type} reading:\n{value}\n\nPlease consult your doctor immediately.\n\nBest regards,\nHealth Records System"
        
        self.send_email(patient_email, subject, message)

    def start_reminder_thread(self, appointment_date: datetime, patient_email: str, doctor_name: str):
        """Start a thread to send reminder 24 hours before appointment"""
        reminder_date = appointment_date - timedelta(days=1)
        current_time = datetime.now()
        delay = (reminder_date - current_time).total_seconds()
        
        if delay > 0:
            def send_reminder():
                threading.Timer(delay, self.send_appointment_reminder, 
                              args=[patient_email, doctor_name, appointment_date.strftime("%Y-%m-%d %H:%M")]).start()
            
            send_reminder()

def get_notification_utils():
    return NotificationUtils()
