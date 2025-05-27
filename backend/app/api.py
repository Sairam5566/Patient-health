from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from models import User, HealthRecord, Appointment
from utils import verify_password, get_password_hash, create_access_token
from config import settings
from encryption_utils import get_encryption_utils
from notification_utils import get_notification_utils
from file_processor import get_file_processor
import os
import json
import re

app = FastAPI(title="Health Records Management API")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Initialize utility classes
encryption_utils = get_encryption_utils()
notification_utils = get_notification_utils()
file_processor = get_file_processor()

# Dependency
def get_db():
    from database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Authentication
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        return user
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

@app.post("/register")
async def register_user(email: str, password: str, role: str, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Encrypt sensitive data
    encrypted_password = encryption_utils.encrypt_data(password)
    
    db_user = User(
        email=email,
        hashed_password=encrypted_password,
        role=role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Generate audit log
    audit_log = encryption_utils.generate_audit_log(
        "user_registration",
        db_user.id
    )
    
    return {"message": "User registered successfully", "audit_log": audit_log}

@app.post("/token")
async def login(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    # Decrypt password for verification
    decrypted_password = encryption_utils.decrypt_data(user.hashed_password)
    if decrypted_password != password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )
    
    access_token = create_access_token(data={"sub": user.email})
    
    # Generate audit log
    audit_log = encryption_utils.generate_audit_log(
        "user_login",
        user.id
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "audit_log": audit_log
    }

# Health Records
@app.post("/upload_record")
async def upload_record(
    file: UploadFile = File(...),
    record_type: str = "",
    metadata: str = "",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate file type and size
    if file.filename.split('.')[-1].lower() not in settings.ALLOWED_FILE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    if len(await file.read()) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")
    
    # Process file based on type
    upload_dir = "uploads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{upload_dir}/{timestamp}_{current_user.id}_{record_type}"
    
    # Add file extension
    ext = file.filename.split('.')[-1].lower()
    filename += f".{ext}"
    
    # Save and encrypt file
    with open(filename, "wb") as f:
        f.write(await file.read())
    
    encrypted_filename = filename + ".enc"
    encryption_utils.encrypt_file(filename, encrypted_filename)
    os.remove(filename)  # Remove unencrypted file
    
    # Process file content
    analysis = {}
    if ext == "pdf":
        analysis = file_processor.process_pdf(filename)
    elif ext in ["png", "jpg", "jpeg"]:
        analysis = file_processor.process_image(filename)
    
    # Create database record
    db_record = HealthRecord(
        user_id=current_user.id,
        record_type=record_type,
        file_path=encrypted_filename,
        metadata=encryption_utils.encrypt_data(json.dumps(analysis)),
        is_public=False
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    
    # Generate audit log
    audit_log = encryption_utils.generate_audit_log(
        "record_upload",
        current_user.id,
        db_record.id
    )
    
    return {
        "record_id": db_record.id,
        "status": "success",
        "audit_log": audit_log,
        "analysis": analysis
    }

@app.get("/records/{user_id}")
async def get_records(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        if current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to view these records")
    
    records = db.query(HealthRecord).filter(HealthRecord.user_id == user_id).all()
    
    # Decrypt metadata for each record
    decrypted_records = []
    for record in records:
        decrypted_metadata = encryption_utils.decrypt_data(record.metadata)
        decrypted_records.append({
            "id": record.id,
            "record_type": record.record_type,
            "upload_date": record.upload_date,
            "metadata": json.loads(decrypted_metadata)
        })
    
    return decrypted_records

# Appointments
@app.post("/appointments")
async def create_appointment(
    doctor_id: int,
    appointment_date: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == "doctor":
        raise HTTPException(status_code=403, detail="Doctors cannot create appointments")
    
    try:
        appointment_date = datetime.fromisoformat(appointment_date)
        if appointment_date < datetime.now():
            raise HTTPException(status_code=400, detail="Appointment date must be in the future")
            
        db_appointment = Appointment(
            user_id=current_user.id,
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            status="pending"
        )
        db.add(db_appointment)
        db.commit()
        db.refresh(db_appointment)
        
        # Get doctor's email
        doctor = db.query(User).filter(User.id == doctor_id).first()
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
            db_appointment.id
        )
        
        return {
            "appointment_id": db_appointment.id,
            "status": "success",
            "audit_log": audit_log
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

@app.get("/appointments/{user_id}")
async def get_appointments(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        if current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to view these appointments")
    
    appointments = db.query(Appointment).filter(Appointment.user_id == user_id).all()
    return appointments

# Health Analysis
@app.get("/analyze/{user_id}")
async def analyze_health(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        if current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to view this analysis")
    
    records = db.query(HealthRecord).filter(HealthRecord.user_id == user_id).all()
    
    # Get all decrypted metadata
    all_metadata = []
    for record in records:
        decrypted_metadata = encryption_utils.decrypt_data(record.metadata)
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
            # Simple trend analysis based on last 3 readings
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
    
    return {
        "analysis": analysis,
        "audit_log": audit_log
    }

# Search functionality
@app.get("/search")
async def search_patients(
    query: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "doctor" and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to search patients")
    
    # Search by email or record content
    patients = []
    users = db.query(User).filter(User.email.like(f"%{query}%"), User.role == "patient").all()
    
    for user in users:
        records = db.query(HealthRecord).filter(HealthRecord.user_id == user.id).all()
        for record in records:
            decrypted_metadata = encryption_utils.decrypt_data(record.metadata)
            if query.lower() in json.loads(decrypted_metadata).values():
                patients.append({
                    "patient_id": user.id,
                    "email": user.email,
                    "last_record_date": record.upload_date
                })
                break
    
    return patients
