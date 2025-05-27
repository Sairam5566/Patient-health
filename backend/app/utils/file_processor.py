import pytesseract
from PIL import Image
import pdfplumber
import cv2
import numpy as np
import os
from datetime import datetime
import json
import re

class FileProcessor:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FileProcessor, cls).__new__(cls)
        return cls._instance

    def process_pdf(self, file_path: str) -> dict:
        """Extract text from PDF and analyze content"""
        try:
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
            
            return self._analyze_content(text)
        except Exception as e:
            print(f"PDF processing error: {str(e)}")
            return self._get_empty_analysis()

    def process_image(self, file_path: str) -> dict:
        """Process medical images"""
        try:
            # Load image
            image = cv2.imread(file_path)
            if image is None:
                raise ValueError("Could not load image")
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply thresholding
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            
            # Extract text using OCR
            text = pytesseract.image_to_string(thresh)
            
            return self._analyze_content(text)
        except Exception as e:
            print(f"Image processing error: {str(e)}")
            return self._get_empty_analysis()

    def _analyze_content(self, text: str) -> dict:
        """Analyze content for health metrics"""
        try:
            return {
                "blood_pressure": self._extract_blood_pressure(text),
                "cholesterol": self._extract_cholesterol(text),
                "glucose": self._extract_glucose(text),
                "heart_rate": self._extract_heart_rate(text)
            }
        except Exception as e:
            print(f"Content analysis error: {str(e)}")
            return self._get_empty_analysis()

    def _get_empty_analysis(self) -> dict:
        """Return empty analysis structure"""
        return {
            "blood_pressure": {"value": "N/A", "status": "Unknown"},
            "cholesterol": {"value": "N/A", "status": "Unknown"},
            "glucose": {"value": "N/A", "status": "Unknown"},
            "heart_rate": {"value": "N/A", "status": "Unknown"}
        }

    def _extract_blood_pressure(self, text: str) -> dict:
        """Extract blood pressure readings"""
        try:
            # Simple pattern matching for blood pressure
            bp_pattern = r"\d+/\d+"
            matches = re.findall(bp_pattern, text)
            
            if matches:
                return {
                    "value": matches[0],
                    "status": self._check_bp_status(matches[0])
                }
        except Exception as e:
            print(f"Blood pressure extraction error: {str(e)}")
        return {"value": "N/A", "status": "Unknown"}

    def _extract_cholesterol(self, text: str) -> dict:
        """Extract cholesterol readings"""
        try:
            # Simple pattern matching for cholesterol
            cholesterol_pattern = r"\d+(\.\d+)?\s*mg/dL"
            matches = re.findall(cholesterol_pattern, text)
            
            if matches:
                value = matches[0][0] if matches[0][0] else matches[0]
                return {
                    "value": value,
                    "status": self._check_cholesterol_status(value)
                }
        except Exception as e:
            print(f"Cholesterol extraction error: {str(e)}")
        return {"value": "N/A", "status": "Unknown"}

    def _extract_glucose(self, text: str) -> dict:
        """Extract glucose readings"""
        try:
            # Simple pattern matching for glucose
            glucose_pattern = r"\d+(\.\d+)?\s*mg/dL"
            matches = re.findall(glucose_pattern, text)
            
            if matches:
                value = matches[0][0] if matches[0][0] else matches[0]
                return {
                    "value": value,
                    "status": self._check_glucose_status(value)
                }
        except Exception as e:
            print(f"Glucose extraction error: {str(e)}")
        return {"value": "N/A", "status": "Unknown"}

    def _extract_heart_rate(self, text: str) -> dict:
        """Extract heart rate readings"""
        try:
            # Simple pattern matching for heart rate
            hr_pattern = r"\d+\s*bpm"
            matches = re.findall(hr_pattern, text)
            
            if matches:
                value = matches[0].split()[0]
                return {
                    "value": value,
                    "status": self._check_hr_status(value)
                }
        except Exception as e:
            print(f"Heart rate extraction error: {str(e)}")
        return {"value": "N/A", "status": "Unknown"}

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
            value = float(cholesterol)
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
            value = float(glucose)
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
            value = int(hr)
            if value > 100:
                return "High"
            if value < 60:
                return "Low"
            return "Normal"
        except:
            return "Unknown"

_file_processor_instance = None

def get_file_processor():
    global _file_processor_instance
    if _file_processor_instance is None:
        _file_processor_instance = FileProcessor()
    return _file_processor_instance 