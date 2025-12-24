# Academic Data Import Guide

This guide explains how to import academic data from JSON files into the Django application using the DRF API.

## Prerequisites

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Ensure the Django server is running:
   ```bash
   python manage.py runserver
   ```

3. Place the JSON files in the Downloads folder (or specify custom path):
   - `acad_programme.json` (or `acad_programme.json`)
   - `acad_course.json`
   - `acad_student.json`

## API Endpoints

The following DRF API endpoints are available:

### Programs
- List/Create: `GET/POST /passbook/api/rest/programs/`
- Retrieve/Update/Delete: `GET/PUT/PATCH/DELETE /passbook/api/rest/programs/<code>/`
- Bulk Create: `POST /passbook/api/rest/programs/bulk/`

### Courses
- List/Create: `GET/POST /passbook/api/rest/courses/`
- Retrieve/Update/Delete: `GET/PUT/PATCH/DELETE /passbook/api/rest/courses/<code>/`
- Bulk Create: `POST /passbook/api/rest/courses/bulk/`

### Course Units
- List/Create: `GET/POST /passbook/api/rest/course-units/`
- Retrieve/Update/Delete: `GET/PUT/PATCH/DELETE /passbook/api/rest/course-units/<code>/`
- Bulk Create: `POST /passbook/api/rest/course-units/bulk/`

### Students
- List/Create: `GET/POST /passbook/api/rest/students/`
- Retrieve/Update/Delete: `GET/PUT/PATCH/DELETE /passbook/api/rest/students/<registration_number>/`
- Bulk Create: `POST /passbook/api/rest/students/bulk/`

## Import Script Usage

### Basic Usage

```bash
python import_academic_data.py
```

This will:
1. Look for JSON files in `~/Downloads`
2. Connect to API at `http://localhost:8000/passbook/api/rest/`
3. Import data in the correct order:
   - Programs (from `acad_programme.json`)
   - Courses (from `acad_programme.json` - progname as course name, abbrev as course code)
   - Course Units (from `acad_course.json` - matched to courses via courseID prefix)
   - Students (from `acad_student.json` - only required fields)

### Custom Options

```bash
# Specify custom API URL
python import_academic_data.py --base-url http://localhost:8000/passbook/api/rest/

# Specify custom JSON directory
python import_academic_data.py --json-dir /path/to/json/files

# Combine options
python import_academic_data.py --base-url http://example.com/api/rest/ --json-dir /custom/path
```

## Data Mapping

### Programs (`acad_programme.json`)
- `progcode` → `Program.code`
- `progname` → `Program.name`
- `couselength`/`maxduration` → `Program.duration`
- `faculty_code` → `Program.faculty` (mapped to "Faculty {code}")

### Courses (`acad_programme.json`)
- `progname` → `Course.name`
- `abbrev` → `Course.code`
- `progcode` → `Course.program` (via `program_code`)
- `levelCode` → `Course.level` (>= 4 = POSTGRAD, else UNDERGRAD)
- `couselength`/`maxduration` → `Course.duration`

### Course Units (`acad_course.json`)
- `courseID` → `CourseUnit.code`
- `courseName` → `CourseUnit.title`
- `CreditUnit` → `CourseUnit.credit_units`
- `courseID` prefix (e.g., "BABA" from "BABA 3101") → `CourseUnit.course` (matched to `Course.code`)
- `courseDescription` → `CourseUnit.description`
- `stat` → `CourseUnit.is_active` (Active = True)
- Department defaults to "General" (can be adjusted in script)
- Semester extracted from courseID number (first digit)

### Students (`acad_student.json`)
Only required fields are imported:
- `firstname` + `othername` → `Student.name`
- `progid` → `Student.program` (via `program_code`)
- `nationality` → `Student.nationality`
- `studPhone` → `Student.student_contact`
- `entryyear` → `Student.admission_year` (extracted as first 4 digits)
- `studsesion` → `Student.session` (DAY→D, EVENING→E, WEEKEND→W)
- `regno` → `Student.registration_number`

## Course Unit to Course Matching

The script matches course units to courses by extracting the prefix from `courseID`:
- `"BABA 3101"` → prefix `"BABA"` → matches `Course.code = "BABA"`
- `"BABA3101"` → prefix `"BABA"` → matches `Course.code = "BABA"`
- `"ACBA 1103"` → prefix `"ACBA"` → matches `Course.code = "ACBA"`

If a course unit's prefix doesn't match any course code, it will be skipped with a warning.

## Error Handling

The script:
- Continues processing even if individual items fail
- Provides summary statistics at the end
- Logs errors for failed items
- Processes students in batches of 100 to avoid overwhelming the server

## Example API Request

You can also use the API directly with curl:

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

# Bulk create programs
curl -X POST http://localhost:8000/passbook/api/rest/programs/bulk/ \
  -H "Content-Type: application/json" \
  -d '[{
    "code": "BSCS",
    "name": "Bachelor of Science in Computer Science",
    "duration": 3,
    "faculty": "Faculty of Science",
    "is_active": true
  }]'
```

## Notes

- The import script processes data in the correct dependency order
- Duplicate entries (same code/registration_number) may cause errors
- Student import is done in batches to improve performance
- The script provides detailed progress information during import

