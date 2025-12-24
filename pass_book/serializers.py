from rest_framework import serializers
from .models import Program, Course, CourseUnit, Student


class ProgramSerializer(serializers.ModelSerializer):
    """Serializer for Program model"""
    class Meta:
        model = Program
        fields = ['id', 'code', 'name', 'description', 'duration', 'faculty', 'is_active']
        extra_kwargs = {
            'code': {'required': True},
            'name': {'required': True},
            'duration': {'required': True},
            'faculty': {'required': True},
        }


class CourseSerializer(serializers.ModelSerializer):
    """Serializer for Course model"""
    program_code = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = Course
        fields = ['id', 'code', 'name', 'description', 'level', 'duration', 'program', 'program_code', 'is_active']
        extra_kwargs = {
            'code': {'required': True},
            'name': {'required': True},
            'duration': {'required': True},
            'program': {'required': False},
        }
    
    def create(self, validated_data):
        program_code = validated_data.pop('program_code', None)
        if program_code:
            try:
                program = Program.objects.get(code=program_code)
                validated_data['program'] = program
            except Program.DoesNotExist:
                raise serializers.ValidationError(f"Program with code '{program_code}' does not exist")
        elif 'program' not in validated_data:
            raise serializers.ValidationError("Either 'program' or 'program_code' must be provided")
        
        return super().create(validated_data)


class CourseUnitSerializer(serializers.ModelSerializer):
    """Serializer for CourseUnit model"""
    course_code = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = CourseUnit
        fields = ['id', 'code', 'title', 'credit_units', 'description', 'department', 
                  'semester_offered', 'course', 'course_code', 'is_active']
        extra_kwargs = {
            'code': {'required': True},
            'title': {'required': True},
            'credit_units': {'required': True},
            'department': {'required': True},
            'semester_offered': {'required': True},
            'course': {'required': False},
        }
    
    def create(self, validated_data):
        course_code = validated_data.pop('course_code', None)
        if course_code:
            try:
                course = Course.objects.get(code=course_code)
                validated_data['course'] = course
            except Course.DoesNotExist:
                raise serializers.ValidationError(f"Course with code '{course_code}' does not exist")
        elif 'course' not in validated_data:
            raise serializers.ValidationError("Either 'course' or 'course_code' must be provided")
        
        return super().create(validated_data)


class StudentSerializer(serializers.ModelSerializer):
    """Serializer for Student model - only required fields"""
    program_code = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = Student
        fields = [
            'id', 'name', 'program', 'program_code', 'nationality', 'student_contact',
            'admission_year', 'session', 'registration_number'
        ]
        extra_kwargs = {
            'name': {'required': True},
            'nationality': {'required': True},
            'student_contact': {'required': True},
            'admission_year': {'required': True},
            'session': {'required': True},
            'registration_number': {'required': True},
            'program': {'required': False},
        }
        read_only_fields = ['id']
    
    def create(self, validated_data):
        program_code = validated_data.pop('program_code')
        try:
            program = Program.objects.get(code=program_code)
            validated_data['program'] = program
        except Program.DoesNotExist:
            raise serializers.ValidationError(f"Program with code '{program_code}' does not exist")
        
        return super().create(validated_data)


