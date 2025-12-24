from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import Program, Course, CourseUnit, Student
from .serializers import ProgramSerializer, CourseSerializer, CourseUnitSerializer, StudentSerializer


class ProgramViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Programs
    """
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer
    lookup_field = 'code'
    
    def get_object(self):
        """Override to allow lookup by code"""
        lookup_value = self.kwargs.get(self.lookup_field)
        if lookup_value:
            return get_object_or_404(self.queryset, code=lookup_value)
        return super().get_object()


class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Courses
    """
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    lookup_field = 'code'
    
    def get_object(self):
        """Override to allow lookup by code"""
        lookup_value = self.kwargs.get(self.lookup_field)
        if lookup_value:
            return get_object_or_404(self.queryset, code=lookup_value)
        return super().get_object()


class CourseUnitViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Course Units
    """
    queryset = CourseUnit.objects.all()
    serializer_class = CourseUnitSerializer
    lookup_field = 'code'
    
    def get_object(self):
        """Override to allow lookup by code"""
        lookup_value = self.kwargs.get(self.lookup_field)
        if lookup_value:
            return get_object_or_404(self.queryset, code=lookup_value)
        return super().get_object()


class StudentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Students - only required fields
    """
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    lookup_field = 'registration_number'
    
    def get_object(self):
        """Override to allow lookup by registration_number"""
        lookup_value = self.kwargs.get(self.lookup_field)
        if lookup_value:
            return get_object_or_404(self.queryset, registration_number=lookup_value)
        return super().get_object()


# Bulk create views for easier data import
@method_decorator(csrf_exempt, name='dispatch')
class BulkCreateAPIView(APIView):
    """Base class for bulk create operations"""
    authentication_classes = []  # Allow unauthenticated access for import
    permission_classes = []  # Allow unauthenticated access for import
    
    def post(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        data = request.data
        
        # Handle both single object and list of objects
        if not isinstance(data, list):
            data = [data]
        
        results = []
        errors = []
        
        for item in data:
            serializer = serializer_class(data=item)
            if serializer.is_valid():
                try:
                    instance = serializer.save()
                    results.append({
                        'success': True,
                        'data': serializer_class(instance).data
                    })
                except Exception as e:
                    errors.append({
                        'item': item,
                        'error': str(e)
                    })
            else:
                errors.append({
                    'item': item,
                    'error': serializer.errors
                })
        
        return Response({
            'successful': len(results),
            'failed': len(errors),
            'results': results,
            'errors': errors
        }, status=status.HTTP_201_CREATED if results else status.HTTP_400_BAD_REQUEST)


class BulkProgramCreateAPIView(BulkCreateAPIView):
    """Bulk create programs"""
    def get_serializer_class(self):
        return ProgramSerializer


class BulkCourseCreateAPIView(BulkCreateAPIView):
    """Bulk create courses"""
    def get_serializer_class(self):
        return CourseSerializer


class BulkCourseUnitCreateAPIView(BulkCreateAPIView):
    """Bulk create course units"""
    def get_serializer_class(self):
        return CourseUnitSerializer


class BulkStudentCreateAPIView(BulkCreateAPIView):
    """Bulk create students"""
    def get_serializer_class(self):
        return StudentSerializer


