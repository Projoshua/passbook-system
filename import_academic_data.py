#!/usr/bin/env python
"""
Script to import academic data from JSON files to Django REST Framework API

Usage:
    python import_academic_data.py [--base-url BASE_URL] [--json-dir JSON_DIR]

This script imports data in the following order:
1. Programs (from acad_programme.json - using progcode as Program.code)
2. Courses (from acad_programme.json - using progname as Course.name, abbrev as Course.code)
3. Course Units (from acad_course.json - matching courseID prefix to Course.code)
4. Students (from acad_student.json - only required fields)
"""

import json
import os
import sys
import argparse
import re
import requests
from typing import Dict, List, Optional
from urllib.parse import urljoin


class AcademicDataImporter:
    def __init__(self, base_url: str = "http://localhost:8000/passbook/api/rest/", json_dir: str = "~/Downloads"):
        """
        Initialize the importer
        
        Args:
            base_url: Base URL for the API (default: http://localhost:8000/passbook/api/rest/)
            json_dir: Directory containing JSON files (default: ~/Downloads)
        """
        self.base_url = base_url.rstrip('/') + '/'
        self.json_dir = os.path.expanduser(json_dir)
        self.session = requests.Session()
        self.stats = {
            'programs': {'created': 0, 'failed': 0, 'skipped': 0},
            'courses': {'created': 0, 'failed': 0, 'skipped': 0},
            'course_units': {'created': 0, 'failed': 0, 'skipped': 0},
            'students': {'created': 0, 'failed': 0, 'skipped': 0},
        }
        self.program_code_map = {}  # Map progcode -> Program code
        self.course_code_map = {}  # Map abbrev -> Course code
        
    def load_json_file(self, filename: str) -> List[Dict]:
        """Load and parse JSON file, extracting actual data from metadata structure"""
        filepath = os.path.join(self.json_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"JSON file not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract data from table object
        for item in data:
            if isinstance(item, dict) and item.get('type') == 'table' and 'data' in item:
                return item['data']
        
        return []
    
    def extract_course_prefix(self, course_id: str) -> str:
        """
        Extract course code prefix from courseID
        Examples: "BABA 3101" -> "BABA", "BABA3101" -> "BABA", "ACBA 1103" -> "ACBA"
        """
        # Remove leading/trailing spaces
        course_id = course_id.strip()
        
        # Split by space and take first part, or extract letters
        if ' ' in course_id:
            prefix = course_id.split()[0]
        else:
            # Extract leading letters
            match = re.match(r'^([A-Z]+)', course_id)
            if match:
                prefix = match.group(1)
            else:
                prefix = course_id
        
        return prefix
    
    def post_data(self, endpoint: str, data: Dict) -> Optional[Dict]:
        """POST data to API endpoint"""
        url = urljoin(self.base_url, endpoint)
        try:
            response = self.session.post(url, json=data, headers={'Content-Type': 'application/json'})
            if response.status_code in [200, 201]:
                return response.json()
            else:
                print(f"  Error: {response.status_code} - {response.text[:200]}")
                return None
        except Exception as e:
            print(f"  Exception: {str(e)}")
            return None
    
    def bulk_post_data(self, endpoint: str, data_list: List[Dict]) -> Dict:
        """POST bulk data to API endpoint"""
        url = urljoin(self.base_url, endpoint + '/bulk/')
        try:
            response = self.session.post(url, json=data_list, headers={'Content-Type': 'application/json'})
            if response.status_code in [200, 201]:
                return response.json()
            else:
                print(f"  Error: {response.status_code} - {response.text[:200]}")
                return {'successful': 0, 'failed': len(data_list), 'errors': []}
        except Exception as e:
            print(f"  Exception: {str(e)}")
            return {'successful': 0, 'failed': len(data_list), 'errors': []}
    
    def import_programs(self):
        """Import programs from acad_programme.json"""
        print("\n" + "="*60)
        print("STEP 1: Importing Programs")
        print("="*60)
        
        programmes = self.load_json_file('acad_programme.json')
        print(f"Found {len(programmes)} programmes")
        
        programs_data = []
        for prog in programmes:
            progcode = prog.get('progcode', '').strip()
            progname = prog.get('progname', '').strip()
            
            if not progcode or not progname:
                continue
            
            # Map faculty_code to faculty name (you may need to adjust this)
            faculty_code = prog.get('faculty_code', '').strip()
            faculty = f"Faculty {faculty_code}"  # Adjust based on your faculty mapping
            
            program_data = {
                'code': progcode,
                'name': progname,
                'description': f"Program {progname}",
                'duration': int(prog.get('couselength', 0)) or int(prog.get('maxduration', 0)) or 3,
                'faculty': faculty,
                'is_active': True
            }
            programs_data.append(program_data)
            self.program_code_map[progcode] = progcode
        
        # Bulk import programs
        if programs_data:
            print(f"\nImporting {len(programs_data)} programs...")
            result = self.bulk_post_data('programs', programs_data)
            self.stats['programs']['created'] = result.get('successful', 0)
            self.stats['programs']['failed'] = result.get('failed', 0)
            print(f"  Created: {self.stats['programs']['created']}")
            print(f"  Failed: {self.stats['programs']['failed']}")
        else:
            print("No programs to import")
    
    def import_courses(self):
        """Import courses from acad_programme.json"""
        print("\n" + "="*60)
        print("STEP 2: Importing Courses")
        print("="*60)
        
        programmes = self.load_json_file('acad_programme.json')
        print(f"Found {len(programmes)} programmes")
        
        courses_data = []
        for prog in programmes:
            progcode = prog.get('progcode', '').strip()
            progname = prog.get('progname', '').strip()
            abbrev = prog.get('abbrev', '').strip()
            
            if not progcode or not progname or not abbrev:
                continue
            
            # Skip "All" program
            if progcode == "00301" or abbrev == "ALL":
                continue
            
            # Determine level based on levelCode
            level_code = prog.get('levelCode', '0')
            level = 'POSTGRAD' if int(level_code) >= 4 else 'UNDERGRAD'
            
            course_data = {
                'code': abbrev,
                'name': progname,
                'description': f"Course: {progname}",
                'level': level,
                'duration': int(prog.get('couselength', 0)) or int(prog.get('maxduration', 0)) or 3,
                'program_code': progcode,  # Link to program
                'is_active': True
            }
            courses_data.append(course_data)
            self.course_code_map[abbrev] = abbrev
        
        # Bulk import courses
        if courses_data:
            print(f"\nImporting {len(courses_data)} courses...")
            result = self.bulk_post_data('courses', courses_data)
            self.stats['courses']['created'] = result.get('successful', 0)
            self.stats['courses']['failed'] = result.get('failed', 0)
            print(f"  Created: {self.stats['courses']['created']}")
            print(f"  Failed: {self.stats['courses']['failed']}")
        else:
            print("No courses to import")
    
    def import_course_units(self):
        """Import course units from acad_course.json"""
        print("\n" + "="*60)
        print("STEP 3: Importing Course Units")
        print("="*60)
        
        courses = self.load_json_file('acad_course.json')
        print(f"Found {len(courses)} course records")
        
        course_units_data = []
        failed_mappings = []
        
        for course in courses:
            course_id_raw = course.get('courseID')
            course_name_raw = course.get('courseName')
            
            # Handle None values
            course_id = (course_id_raw or '').strip()
            course_name = (course_name_raw or '').strip()
            
            if not course_id or not course_name:
                continue
            
            # Extract course code prefix from courseID
            course_prefix = self.extract_course_prefix(course_id)
            
            # Check if we have a matching course
            if course_prefix not in self.course_code_map:
                failed_mappings.append((course_id, course_prefix))
                continue
            
            # Get credit units
            try:
                credit_units = int(float(course.get('CreditUnit', 0) or 0))
            except (ValueError, TypeError):
                credit_units = 3  # Default
            
            # Extract semester from courseID if possible (e.g., "BABA 3101" -> semester 3)
            # This is a heuristic - adjust based on your numbering scheme
            semester_offered = 1
            try:
                # Try to extract semester from course number (first digit)
                match = re.search(r'\d+', course_id)
                if match:
                    num = int(match.group()[0])
                    semester_offered = min(max(num, 1), 8)
            except:
                pass
            
            course_unit_data = {
                'code': course_id.strip(),
                'title': course_name,
                'credit_units': credit_units,
                'description': (course.get('courseDescription') or '') or '',
                'department': 'General',  # Default - adjust if you have department info
                'semester_offered': semester_offered,
                'course_code': course_prefix,  # Link to course
                'is_active': (course.get('stat') or 'Active') == 'Active'
            }
            course_units_data.append(course_unit_data)
        
        # Bulk import course units
        if course_units_data:
            print(f"\nImporting {len(course_units_data)} course units...")
            if failed_mappings:
                print(f"  Warning: {len(failed_mappings)} course units could not be mapped to courses")
                print(f"  Sample unmapped: {failed_mappings[:5]}")
            
            result = self.bulk_post_data('course-units', course_units_data)
            self.stats['course_units']['created'] = result.get('successful', 0)
            self.stats['course_units']['failed'] = result.get('failed', 0)
            print(f"  Created: {self.stats['course_units']['created']}")
            print(f"  Failed: {self.stats['course_units']['failed']}")
        else:
            print("No course units to import")
    
    def import_students(self):
        """Import students from acad_student.json (only required fields)"""
        print("\n" + "="*60)
        print("STEP 4: Importing Students")
        print("="*60)
        
        students = self.load_json_file('acad_student.json')
        print(f"Found {len(students)} student records")
        
        students_data = []
        failed_mappings = []
        
        for student in students:
            regno_raw = student.get('regno')
            firstname_raw = student.get('firstname')
            othername_raw = student.get('othername')
            progid_raw = student.get('progid')
            
            # Handle None values
            regno = (regno_raw or '').strip()
            firstname = (firstname_raw or '').strip()
            othername = (othername_raw or '').strip()
            progid = (progid_raw or '').strip()
            
            if not regno or not firstname:
                continue
            
            # Combine firstname and othername (only add othername if it exists)
            if othername:
                name = f"{firstname} {othername}".strip()
            else:
                name = firstname
            
            # Map progid to program code (assuming progid is progcode)
            if progid not in self.program_code_map:
                failed_mappings.append((regno, progid))
                continue
            
            # Map session
            session_map = {
                'DAY': 'D',
                'EVENING': 'E',
                'WEEKEND': 'W',
                'D': 'D',
                'E': 'E',
                'W': 'W'
            }
            stud_session_raw = student.get('studsesion', 'DAY')
            stud_session = (stud_session_raw or 'DAY').strip().upper()
            session = session_map.get(stud_session, 'D')
            
            # Get admission year
            entryyear_raw = student.get('entryyear')
            entryyear = (entryyear_raw or '').strip()
            try:
                # Extract year (e.g., "2025" or "2510" -> 2025)
                if len(entryyear) == 4:
                    admission_year = int(entryyear)
                elif len(entryyear) > 4:
                    admission_year = int(entryyear[:4])
                else:
                    admission_year = 2024  # Default
            except (ValueError, TypeError):
                admission_year = 2024  # Default
            
            nationality_raw = student.get('nationality', 'UGANDAN')
            stud_phone_raw = student.get('studPhone')
            
            student_data = {
                'name': name,
                'program_code': progid,
                'nationality': (nationality_raw or 'UGANDAN').strip(),
                'student_contact': (stud_phone_raw or '').strip() or '0000000000',
                'admission_year': admission_year,
                'session': session,
                'registration_number': regno
            }
            students_data.append(student_data)
        
        # Bulk import students (in batches to avoid overwhelming the server)
        if students_data:
            print(f"\nImporting {len(students_data)} students...")
            if failed_mappings:
                print(f"  Warning: {len(failed_mappings)} students could not be mapped to programs")
                print(f"  Sample unmapped: {failed_mappings[:5]}")
            
            batch_size = 100
            total_created = 0
            total_failed = 0
            
            for i in range(0, len(students_data), batch_size):
                batch = students_data[i:i+batch_size]
                print(f"  Processing batch {i//batch_size + 1}/{(len(students_data)-1)//batch_size + 1} ({len(batch)} students)...")
                result = self.bulk_post_data('students', batch)
                total_created += result.get('successful', 0)
                total_failed += result.get('failed', 0)
            
            self.stats['students']['created'] = total_created
            self.stats['students']['failed'] = total_failed
            print(f"\n  Total Created: {total_created}")
            print(f"  Total Failed: {total_failed}")
        else:
            print("No students to import")
    
    def print_summary(self):
        """Print import summary"""
        print("\n" + "="*60)
        print("IMPORT SUMMARY")
        print("="*60)
        for entity, stats in self.stats.items():
            print(f"{entity.replace('_', ' ').title()}:")
            print(f"  Created: {stats['created']}")
            print(f"  Failed: {stats['failed']}")
            print(f"  Skipped: {stats['skipped']}")
        print("="*60)
    
    def run(self):
        """Run the import process"""
        print("Starting Academic Data Import")
        print(f"API Base URL: {self.base_url}")
        print(f"JSON Directory: {self.json_dir}")
        
        try:
            # Import in order
            self.import_programs()
            self.import_courses()
            self.import_course_units()
            self.import_students()
            
            self.print_summary()
            
        except Exception as e:
            print(f"\nError during import: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Import academic data from JSON files')
    parser.add_argument('--base-url', default='http://localhost:8000/passbook/api/rest/',
                        help='Base URL for the API (default: http://localhost:8000/passbook/api/rest/)')
    parser.add_argument('--json-dir', default='~/Downloads',
                        help='Directory containing JSON files (default: ~/Downloads)')
    
    args = parser.parse_args()
    
    importer = AcademicDataImporter(base_url=args.base_url, json_dir=args.json_dir)
    importer.run()


if __name__ == '__main__':
    main()


