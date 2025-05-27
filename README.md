# Health Records Management System

A comprehensive web application for managing patient health records, appointments, and doctor-patient interactions.

## Features

- **User Authentication**
  - Separate registration and login for patients and doctors
  - Secure password hashing and session management
  - Role-based access control

- **Patient Features**
  - Book appointments with doctors
  - Upload and manage health records
  - View appointment history
  - Track medical history
  - Receive notifications for appointments and updates

- **Doctor Features**
  - Manage patient appointments
  - Add health records and notes
  - View patient medical history
  - Track patient progress
  - Set availability and office hours

- **Health Records**
  - Support for various record types (lab results, prescriptions, etc.)
  - File attachments (PDF, images)
  - Automatic data extraction from uploaded documents
  - Secure storage and encryption

- **API Endpoints**
  - RESTful API for appointments, health records, and user data
  - JSON responses for easy integration
  - Secure authentication and authorization

## Technology Stack

- **Backend**
  - Python 3.8+
  - Flask web framework
  - SQLAlchemy ORM
  - Flask-Login for authentication
  - Cryptography for data encryption
  - OpenCV and Tesseract for document processing

- **Frontend**
  - HTML5, CSS3, JavaScript
  - Bootstrap 5 for responsive design
  - jQuery for AJAX requests
  - Chart.js for data visualization

- **Database**
  - SQLite for development
  - PostgreSQL for production

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Sairam5566/Patient-health.git
   cd Patient-health
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Initialize the database:
   ```bash
   python init_db.py
   ```

6. Run the application:
   ```bash
   python run.py
   ```

## Configuration

The application can be configured using environment variables or a `.env` file:

- `FLASK_ENV`: development/production
- `SECRET_KEY`: Flask secret key
- `DATABASE_URL`: Database connection URL
- `MAIL_SERVER`: SMTP server for email notifications
- `MAIL_PORT`: SMTP port
- `MAIL_USERNAME`: SMTP username
- `MAIL_PASSWORD`: SMTP password
- `ENCRYPTION_KEY`: Key for encrypting sensitive data

## Development

1. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Run tests:
   ```bash
   pytest
   ```

3. Check code style:
   ```bash
   flake8
   ```

## Deployment

The application is configured for deployment on Render:

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set environment variables
4. Deploy the application

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Authors

- Sairam5566 - Initial work and maintenance

## Acknowledgments

- Flask documentation and community
- SQLAlchemy documentation
- Bootstrap team
- OpenCV and Tesseract communities
