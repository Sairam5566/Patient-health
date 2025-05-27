import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import threading
import json
import os
from backend.config.config import Config

class NotificationUtils:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NotificationUtils, cls).__new__(cls)
            cls._instance.smtp_server = Config.MAIL_SERVER
            cls._instance.smtp_port = Config.MAIL_PORT
            cls._instance.sender_email = Config.MAIL_USERNAME
            cls._instance.sender_password = Config.MAIL_PASSWORD
            cls._instance.email_enabled = all([
                Config.MAIL_SERVER,
                Config.MAIL_PORT,
                Config.MAIL_USERNAME,
                Config.MAIL_PASSWORD
            ])
        return cls._instance

    def send_email(self, recipient: str, subject: str, message: str):
        """Send email notification"""
        if not self.email_enabled:
            print("Email notifications are disabled. Please configure email settings.")
            return False

        def send_async():
            try:
                msg = MIMEMultipart()
                msg['From'] = self.sender_email
                msg['To'] = recipient
                msg['Subject'] = subject
                
                msg.attach(MIMEText(message, 'plain'))
                
                server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=5)
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
                server.quit()
                return True
            except Exception as e:
                print(f"Email error: {str(e)}")
                return False

        # Send email in a separate thread
        thread = threading.Thread(target=send_async)
        thread.daemon = True
        thread.start()
        return True

    def send_appointment_reminder(self, patient_email: str, doctor_name: str, appointment_date: str):
        """Send appointment reminder"""
        subject = f"Appointment Reminder - {doctor_name}"
        message = f"Dear Patient,\n\nYou have an appointment with Dr. {doctor_name} on {appointment_date}.\nPlease arrive 15 minutes early for your appointment.\n\nBest regards,\nHealth Records System"
        
        return self.send_email(patient_email, subject, message)

    def send_health_alert(self, patient_email: str, alert_type: str, value: str):
        """Send health alert notification"""
        subject = f"Health Alert: {alert_type}"
        message = f"Dear Patient,\n\nWe have detected an abnormal {alert_type} reading:\n{value}\n\nPlease consult your doctor immediately.\n\nBest regards,\nHealth Records System"
        
        return self.send_email(patient_email, subject, message)

    def start_reminder_thread(self, appointment_date: datetime, patient_email: str, doctor_name: str):
        """Start a thread to send reminder 24 hours before appointment"""
        if not self.email_enabled:
            return

        reminder_date = appointment_date - timedelta(days=1)
        current_time = datetime.now()
        delay = (reminder_date - current_time).total_seconds()
        
        if delay > 0:
            def send_reminder():
                self.send_appointment_reminder(
                    patient_email,
                    doctor_name,
                    appointment_date.strftime("%Y-%m-%d %H:%M")
                )
            
            timer = threading.Timer(delay, send_reminder)
            timer.daemon = True
            timer.start()

_notification_utils_instance = None

def get_notification_utils():
    global _notification_utils_instance
    if _notification_utils_instance is None:
        _notification_utils_instance = NotificationUtils()
    return _notification_utils_instance
