# Health Records Management Application

A secure web-based application for managing health records and booking medical appointments.

## Features

- Secure health record management
- Appointment booking system
- Health data analysis
- Role-based access control
- File encryption
- Audit logging
- Email notifications
- Advanced search functionality
- Trend analysis for health metrics

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your configuration:
```
SECRET_KEY=your-secret-key-change-this-in-production
DATABASE_URL=sqlite:///./health_records.db
NOTIFICATION_EMAIL=your-notification-email@gmail.com
NOTIFICATION_PASSWORD=your-app-specific-password
ENCRYPTION_KEY=your-encryption-key-change-this-in-production
```

4. Run the application:
```bash
python app.py
```

## Usage

The application provides three types of user roles:
- Patient: Can upload health records and book appointments
- Doctor: Can view patient records and manage appointments
- Admin: Has full access to all features and user management

## Assumptions & Limitations

- No real-time patient-doctor chat
- File uploads limited to PDF, PNG, JPG
- Local SQLite database for development
- Basic security implementation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License
