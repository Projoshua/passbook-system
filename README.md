# Passbook System

A comprehensive Django-based student management and registration system for educational institutions. This system manages student registration, academic records, attendance tracking, clearance processes, and various administrative functions.

## 📋 Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Docker Deployment](#docker-deployment)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

### Student Management
- **Student Registration**: Complete student registration with photos, signatures, and parent/guardian information
- **Access Number Generation**: Automatic generation of unique access numbers (format: PROGRAM-XXXX)
- **Student Profiles**: Comprehensive student profiles with academic and personal information
- **User Account Integration**: Automatic user account creation for students

### Academic Management
- **Program Management**: Create and manage academic programs (degrees, diplomas, etc.)
- **Course Management**: Hierarchical course structure management
- **Course Units**: Detailed course unit management with credit units, descriptions, and semesters
- **Academic Years**: Academic year configuration and management
- **Semester Management**: Semester creation and tracking

### Clearance & Registration
- **Semester Clearance**: Academic and finance clearance tracking
- **Graduation Clearance**: Complete graduation clearance workflow
- **Medical Registration**: Student medical registration management
- **NCHE Registration**: National Council for Higher Education registration
- **Dead Semester Applications**: Management of dead semester applications

### Attendance Tracking
- **SMS-Based Attendance**: SMS-based lecture attendance system
- **AI Attendance**: AI-powered attendance tracking (future implementation)
- **Attendance Reports**: Comprehensive attendance reporting

### Additional Features
- **Internship Management**: Student internship tracking and management
- **Laptop Scheme**: Laptop scheme application management
- **Student Associations**: Student association membership tracking
- **Course Work**: Course work management and tracking
- **Reports & Analytics**: Various reporting features including:
  - Program enrollment reports
  - Graduation eligibility reports
  - Finance reports
  - Semester clearance reports
  - Dead semester applications reports

### User Management
- **Role-Based Access**: Different user types (Student, Staff, Admin)
- **Authentication System**: Secure login and authentication
- **Staff Management**: Staff account creation and management

## 🛠 Technology Stack

- **Backend Framework**: Django 5.2.6
- **Database**: PostgreSQL (production) / SQLite (development)
- **REST API**: Django REST Framework
- **Storage**: Django Storages (S3/MinIO compatible)
- **Frontend**: Django Templates with Bootstrap
- **Containerization**: Docker & Docker Compose
- **Python Version**: 3.12+

### Key Dependencies
- Django 5.2.6
- Django REST Framework
- django-storages
- boto3 (for S3 storage)
- psycopg2-binary (PostgreSQL adapter)
- Pillow (image processing)
- widget-tweaks (form rendering)

## 📦 Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.12 or higher
- pip (Python package manager)
- PostgreSQL (for production) or SQLite (for development)
- Git
- Docker and Docker Compose (optional, for containerized deployment)

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Projoshua/passbook-system.git
cd passbook-system
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the project root:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DB_ENGINE=django.db.backends.postgresql
DB_NAME=passbook_db
DB_USER=postgres
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432

# Static Files & Media Storage (Optional - for S3/MinIO)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_ENDPOINT_URL=http://localhost:9000  # For MinIO
```

### 5. Database Setup

#### For SQLite (Development):
```bash
python manage.py migrate
```

#### For PostgreSQL (Production):
```bash
# Create database
createdb passbook_db

# Run migrations
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

Or use the custom command:
```bash
python manage.py create_superuser --username admin --email admin@example.com --password admin123
```

### 7. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 8. Run Development Server

```bash
python manage.py runserver
```

The application will be available at `http://localhost:8000`

## ⚙️ Configuration

### Database Configuration

The system supports both SQLite (development) and PostgreSQL (production). Configure in `AttendanceSystem/settings.py` or via environment variables.

### Storage Configuration

For file storage, you can use:
- **Local Storage**: Default Django file storage
- **S3/MinIO**: Configure AWS credentials in `.env` file

### User Types

The system supports three user types:
- **Student**: Can view their own records and submit applications
- **Staff**: Can manage students and process clearances
- **Admin/Sysadmin**: Full system access

## 📖 Usage

### Accessing the System

1. Navigate to `http://localhost:8000`
2. Login with your credentials
3. Access different modules based on your user type

### Student Registration

1. Navigate to **Student Registration** → **Create Student**
2. Fill in student information:
   - Personal details (name, nationality, contact)
   - Academic information (program, admission year, session)
   - Parent/Guardian information
   - Upload photos and signatures
3. The system automatically generates:
   - Registration number
   - Static access number (format: PROGRAM-XXXX)
   - User account

### Importing Academic Data

Use the provided import script to bulk import academic data:

```bash
python import_academic_data.py
```

See [IMPORT_README.md](IMPORT_README.md) for detailed import instructions.

### Managing Clearances

1. **Semester Clearance**:
   - Navigate to **Semester Clearance**
   - Select student
   - Process academic and finance clearances

2. **Graduation Clearance**:
   - Navigate to **Graduation Clearance**
   - Select student
   - Process through various departments

## 🔌 API Documentation

The system provides REST API endpoints for programmatic access:

### Base URL
```
http://localhost:8000/passbook/api/rest/
```

### Available Endpoints

#### Programs
- `GET/POST /programs/` - List/Create programs
- `GET/PUT/PATCH/DELETE /programs/<code>/` - Retrieve/Update/Delete program
- `POST /programs/bulk/` - Bulk create programs

#### Courses
- `GET/POST /courses/` - List/Create courses
- `GET/PUT/PATCH/DELETE /courses/<code>/` - Retrieve/Update/Delete course
- `POST /courses/bulk/` - Bulk create courses

#### Course Units
- `GET/POST /course-units/` - List/Create course units
- `GET/PUT/PATCH/DELETE /course-units/<code>/` - Retrieve/Update/Delete course unit
- `POST /course-units/bulk/` - Bulk create course units

#### Students
- `GET/POST /students/` - List/Create students
- `GET/PUT/PATCH/DELETE /students/<registration_number>/` - Retrieve/Update/Delete student
- `POST /students/bulk/` - Bulk create students

### Example API Request

```bash
# Create a program
curl -X POST http://localhost:8000/passbook/api/rest/programs/ \
  -H "Content-Type: application/json" \
  -d '{
    "code": "BSCS",
    "name": "Bachelor of Science in Computer Science",
    "duration": 3,
    "faculty": "Faculty of Science",
    "is_active": true
  }'
```

For detailed API documentation, see [IMPORT_README.md](IMPORT_README.md).

## 🐳 Docker Deployment

The system can be deployed using Docker Compose for easy setup and deployment.

### Quick Start with Docker

1. **Configure Environment**:
   Edit `.env` file with your settings:
   ```env
   DJANGO_SUPERUSER_USERNAME=admin
   DJANGO_SUPERUSER_EMAIL=admin@example.com
   DJANGO_SUPERUSER_PASSWORD=SecurePassword123!
   ```

2. **Build and Start Containers**:
   ```bash
   docker-compose up --build
   ```

3. **Access the Application**:
   - Django App: http://localhost:8000
   - MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
   - PostgreSQL: localhost:5432

### Docker Commands

```bash
# Start containers
docker-compose up

# Start in background
docker-compose up -d

# Stop containers
docker-compose down

# View logs
docker-compose logs -f web

# Run Django commands
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

For detailed Docker setup instructions, see [README-DOCKER.md](README-DOCKER.md).

## 📁 Project Structure

```
passbook-system/
├── accounts/                 # User authentication and management
│   ├── models.py           # Custom User model
│   ├── views.py            # Authentication views
│   └── management/         # Custom management commands
├── attendance_ai/          # AI-based attendance (future)
├── attendance_sms/         # SMS-based attendance system
├── pass_book/              # Main passbook application
│   ├── models.py           # Student, Program, Course models
│   ├── views.py            # Main views
│   ├── api_views.py        # REST API endpoints
│   └── serializers.py      # DRF serializers
├── AttendanceSystem/       # Django project settings
│   ├── settings.py         # Main settings file
│   ├── urls.py             # Root URL configuration
│   └── wsgi.py             # WSGI configuration
├── templates/              # HTML templates
│   ├── accounts/           # Authentication templates
│   ├── student_registration/ # Student management templates
│   └── sms_attendance/     # Attendance templates
├── media/                  # User-uploaded files
├── static/               # Static files (CSS, JS, images)
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
├── docker-compose.yml     # Docker Compose configuration
├── Dockerfile            # Docker image configuration
├── import_academic_data.py # Data import script
└── README.md             # This file
```

## 🔧 Management Commands

### Create Users

```bash
# Create superuser
python manage.py create_superuser \
  --username admin \
  --email admin@example.com \
  --password admin123

# Create regular user
python manage.py create_user \
  --username student1 \
  --email student1@example.com \
  --password password123 \
  --user_type student \
  --phone_number +256700000000
```

### Database Operations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

## 🧪 Testing

```bash
# Run tests
python manage.py test

# Run specific app tests
python manage.py test pass_book
python manage.py test accounts
```

## 📝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Write docstrings for all functions and classes
- Add tests for new features
- Update documentation as needed

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Error**:
   - Ensure PostgreSQL is running
   - Check database credentials in `.env`
   - Verify database exists

2. **Static Files Not Loading**:
   ```bash
   python manage.py collectstatic
   ```

3. **Migration Errors**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Port Already in Use**:
   - Change port in `docker-compose.yml` or use different port:
   ```bash
   python manage.py runserver 8001
   ```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Authors

- **Projoshua** - *Initial work* - [GitHub](https://github.com/Projoshua)

## 🙏 Acknowledgments

- Django community for the excellent framework
- All contributors and users of this system

## 📞 Support

For support, please open an issue on the [GitHub repository](https://github.com/Projoshua/passbook-system/issues).

---

**Note**: This is an active development project. Features and APIs may change. Please refer to the latest documentation for current functionality.
