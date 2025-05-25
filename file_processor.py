import pytesseract
from PIL import Image
import pdfplumber
import cv2
import numpy as np
import os
from datetime import datetime
import json
from encryption_utils import get_encryption_utils

class FileProcessor:
    def __init__(self):
        self.encryption_utils = get_encryption_utils()

    def process_pdf(self, file_path: str) -> dict:
        """Extract text from PDF and analyze content"""
        try:
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text()
            
            return self._analyze_pdf_content(text)
        except Exception as e:
            return {"error": str(e)}

    def process_image(self, file_path: str) -> dict:
        """Process medical images"""
        try:
            # Load image
            image = cv2.imread(file_path)
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply thresholding
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            
            # Extract text using OCR
            text = pytesseract.image_to_string(thresh)
            
            return self._analyze_image_content(text)
        except Exception as e:
            return {"error": str(e)}

    def _analyze_pdf_content(self, text: str) -> dict:
        """Analyze PDF content for health metrics"""
        analysis = {
            "blood_pressure": self._extract_blood_pressure(text),
            "cholesterol": self._extract_cholesterol(text),
            "glucose": self._extract_glucose(text),
            "heart_rate": self._extract_heart_rate(text)
        }
        
        # Encrypt sensitive data
        encrypted_analysis = {}
        for key, value in analysis.items():
            encrypted_analysis[key] = self.encryption_utils.encrypt_data(json.dumps(value))
        
        return encrypted_analysis

    def _analyze_image_content(self, text: str) -> dict:
        """Analyze image content for health metrics"""
        analysis = {
            "blood_pressure": self._extract_blood_pressure(text),
            "cholesterol": self._extract_cholesterol(text),
            "glucose": self._extract_glucose(text),
            "heart_rate": self._extract_heart_rate(text)
        }
        
        # Encrypt sensitive data
        encrypted_analysis = {}
        for key, value in analysis.items():
            encrypted_analysis[key] = self.encryption_utils.encrypt_data(json.dumps(value))
        
        return encrypted_analysis

    def _extract_blood_pressure(self, text: str) -> dict:
        """Extract blood pressure readings"""
        # Simple pattern matching for blood pressure
        bp_pattern = r"\d+/\d+"
        matches = re.findall(bp_pattern, text)
        
        if matches:
            return {
                "value": matches[0],
                "status": self._check_bp_status(matches[0])
            }
        return {"value": "N/A", "status": "Normal"}

    def _extract_cholesterol(self, text: str) -> dict:
        """Extract cholesterol readings"""
        # Simple pattern matching for cholesterol
        cholesterol_pattern = r"\d+(\.\d+)? mg/dL"
        matches = re.findall(cholesterol_pattern, text)
        
        if matches:
            return {
                "value": matches[0],
                "status": self._check_cholesterol_status(matches[0])
            }
        return {"value": "N/A", "status": "Normal"}

    def _extract_glucose(self, text: str) -> dict:
        """Extract glucose readings"""
        # Simple pattern matching for glucose
        glucose_pattern = r"\d+(\.\d+)? mg/dL"
        matches = re.findall(glucose_pattern, text)
        
        if matches:
            return {
                "value": matches[0],
                "status": self._check_glucose_status(matches[0])
            }
        return {"value": "N/A", "status": "Normal"}

    def _extract_heart_rate(self, text: str) -> dict:
        """Extract heart rate readings"""
        # Simple pattern matching for heart rate
        hr_pattern = r"\d+ bpm"
        matches = re.findall(hr_pattern, text)
        
        if matches:
            return {
                "value": matches[0],
                "status": self._check_hr_status(matches[0])
            }
        return {"value": "N/A", "status": "Normal"}

    def _check_bp_status(self, bp_reading: str) -> str:
        """Check blood pressure status"""
        try:
            systolic, diastolic = map(int, bp_reading.split("/"))
            if systolic > 130 or diastolic > 80:
                return "High"
            if systolic < 90 or diastolic < 60:
                return "Low"
            return "Normal"
        except:
            return "Unknown"

    def _check_cholesterol_status(self, cholesterol: str) -> str:
        """Check cholesterol status"""
        try:
            value = float(cholesterol.split()[0])
            if value > 200:
                return "High"
            if value < 150:
                return "Low"
            return "Normal"
        except:
            return "Unknown"

    def _check_glucose_status(self, glucose: str) -> str:
        """Check glucose status"""
        try:
            value = float(glucose.split()[0])
            if value > 126:
                return "High"
            if value < 70:
                return "Low"
            return "Normal"
        except:
            return "Unknown"

    def _check_hr_status(self, hr: str) -> str:
        """Check heart rate status"""
        try:
            value = int(hr.split()[0])
            if value > 100:
                return "High"
            if value < 60:
                return "Low"
            return "Normal"
        except:
            return "Unknown"

def get_file_processor():
    return FileProcessor()
