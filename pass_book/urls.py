
# pass_book/urls.py
from django.urls import path
from . import views
from . import api_views
from django.conf import settings
from django.conf.urls.static import static
app_name = 'pass_book'


urlpatterns = [
    # Dashboard
    path('', views.dashboard_view, name='dashboard-passbook'),
    
    # Program URLs
    path('programs/', views.ProgramListView.as_view(), name='program_list'),
    path('programs/new/', views.ProgramCreateView.as_view(), name='program_create'),
    path('programs/<int:pk>/edit/', views.ProgramUpdateView.as_view(), name='program_update'),
    path('programs/<int:pk>/delete/', views.ProgramDeleteView.as_view(), name='program_delete'),
    
    # Course URLs (hierarchical courses)
    path('courses/', views.CourseListView.as_view(), name='course_list'),
    path('courses/new/', views.CourseCreateView.as_view(), name='course_create'),
    path('courses/<int:pk>/edit/', views.CourseUpdateView.as_view(), name='course_update'),
    path('courses/<int:pk>/delete/', views.CourseDeleteView.as_view(), name='course_delete'),

    #Student URLS
    path('students/', views.StudentListView.as_view(), name='student_list'),
    path('students/new/', views.student_create, name='student_create'),
    path('students/<uuid:pk>/', views.StudentDetailView.as_view(), name='student_detail'),
    path('students/<uuid:pk>/edit/', views.StudentUpdateView.as_view(), name='student_update'),
    path('students/<uuid:pk>/delete/', views.StudentDeleteView.as_view(), name='student_delete'),
    # Academic Year URLs
    path('academic-years/', views.AcademicYearListView.as_view(), name='academic_year_list'),
    path('academic-years/new/', views.AcademicYearCreateView.as_view(), name='academic_year_create'),
    path('academic-years/<int:pk>/edit/', views.AcademicYearUpdateView.as_view(), name='academic_year_update'),
    path('academic-years/<int:pk>/delete/', views.AcademicYearDeleteView.as_view(), name='academic_year_delete'),
    path('academic-years/<int:pk>/set-active/', views.academic_year_set_active, name='academic_year_set_active'),
    
    # Semester URLs
    path('semesters/', views.SemesterListView.as_view(), name='semester_list'),
    path('semesters/new/', views.SemesterCreateView.as_view(), name='semester_create'),
    path('semesters/<int:pk>/edit/', views.SemesterUpdateView.as_view(), name='semester_update'),
    path('semesters/<int:pk>/delete/', views.SemesterDeleteView.as_view(), name='semester_delete'),
    path('semesters/<int:pk>/set-active/', views.semester_set_active, name='semester_set_active'),
    
    # Access Number URLs
    #path('access-numbers/', views.AccessNumberListView.as_view(), name='access_number_list'),
    #path('access-numbers/new/', views.AccessNumberCreateView.as_view(), name='access_number_create'),
    #path('access-numbers/<str:access_number>/', views.AccessNumberDetailView.as_view(), name='access_number_detail'),
    #path('access-numbers/<str:access_number>/update/', views.AccessNumberUpdateView.as_view(), name='access_number_update'),
    #path('access-numbers/<str:access_number>/deactivate/', views.AccessNumberDeactivateView.as_view(), name='access_number_deactivate'),
    path('access-numbers/', views.access_number_list, name='list'),
    path('generate/<uuid:student_id>/', views.generate_access_number, name='generate_single'),
    path('bulk-generate/', views.bulk_generate_access_numbers, name='bulk_generate'), 
    path('detail/<str:access_number>/', views.access_number_detail, name='detail'),
    path('deactivate/<str:access_number>/', views.deactivate_access_number, name='deactivate'),
    path(
    'access-numbers/edit/<str:access_number>/',
    views.edit_access_number_status,
    name='edit_status'
    ),
    # Semester Registration
    path('access/<str:access_number>/register/', views.semester_registration_view, name='semester_registration'),
    
    # Course Unit URLs
    path('course-units/', views.CourseUnitListView.as_view(), name='course_unit_list'),
    path('course-units/create/', views.CourseUnitCreateView.as_view(), name='course_unit_create'),
    path('course-units/<int:pk>/edit/', views.CourseUnitUpdateView.as_view(), name='course_unit_update'),
    path('course-units/<int:pk>/delete/', views.CourseUnitDeleteView.as_view(), name='course_unit_delete'),

    # Student Course Units Management

    path(
        'access-numbers/<str:access_number>/course-units/',
        views.StudentCourseUnitManageView.as_view(),
        name='student_course_units'
    ),
    #path('access-numbers/<str:access_number>/course-units/', views.student_course_units_view, name='student_course_units'),
  
    path('student-course-unit/<int:pk>/edit/', views.StudentCourseUnitUpdateView.as_view(), name='edit_student_course_unit'),
    # urls.py
    path('course-units/select-student/', views.select_student_for_course_units, name='select_student_for_course_units'),
      
    # Student Course Unit Management
    path('select-student/', views.select_student_for_course_units, name='select_student'),
    path('access/<str:access_number>/course-units/', views.StudentCourseUnitManageView.as_view(), name='student_course_units'),
    path('access/<int:access_num_id>/course-units/bulk/', views.StudentCourseUnitBulkCreateView.as_view(), name='student_course_units_bulk'),
    path('access/<str:access_num_id>/course-units/list/', views.StudentCourseUnitListView.as_view(), name='student_course_units_list'),
    path('access/<int:access_num_id>/course-units/add/', views.StudentCourseUnitCreateView.as_view(), name='student_course_unit_add'),
    path('student-course-units/<int:pk>/edit/', views.StudentCourseUnitUpdateView.as_view(), name='student_course_unit_update'),
    path('access/<str:access_number>/course-units/manage/', views.student_course_units_view, name='student_course_units_manage'),
    
    # Course Work URLs
    path('course-works/', views.CourseWorkListView.as_view(), name='course_work_list'),
    path('course-works/new/', views.CourseWorkCreateView.as_view(), name='course_work_create'),
    path('course-works/<int:pk>/edit/', views.CourseWorkUpdateView.as_view(), name='course_work_update'),
    path('course-works/<int:pk>/delete/', views.CourseWorkDeleteView.as_view(), name='course_work_delete'),
    path('course-works/<int:course_work_id>/assign/', views.assign_coursework_view, name='assign_coursework'),
    path('course-works/delete-assignment/<int:assignment_id>/', views.delete_assignment, name='delete_assignment'),
    
    # Student Course Work Management
    path('student-course-works/', views.StudentCourseWorkListView.as_view(), name='student_course_work_list'),
    path('student-course-works/<int:student_id>/access-numbers/', views.AccessNumberCourseWorkListView.as_view(), name='access_number_course_work_list'),
    path('access/<str:access_number>/course-works/', views.StudentCourseWorkCreateUpdateView.as_view(), name='course_work_manage'),
    path('access/<str:access_number>/course-works/detail/', views.StudentCourseWorkDetailView.as_view(), name='course_work_detail'),
    path('student-course-works/<int:pk>/delete/', views.StudentCourseWorkDeleteView.as_view(), name='student_course_work_delete'),
    path('access/<str:access_number>/course-works/view/', views.student_course_works_view, name='student_course_works_view'),
    
    # Association URLs
    #path('associations/', views.AssociationListView.as_view(), name='association_list'),
     path('associations/new/', views.AssociationCreateView.as_view(), name='association_create'),
    #path('access/<str:access_number>/associations/', views.student_associations_view, name='student_associations'),
     path('associations/',
         views.AssociationListView.as_view(),
         name='association_list'),

    path('associations/create/',
         views.AssociationCreateView.as_view(),
         name='association_create'),

     # urls.py

path('associations/select-student/',
     views.select_student_for_association_view,
     name='select_student_for_association'),

    # Student Association Management
    path('student/<str:access_number>/associations/',
         views.student_associations_view,
         name='student_associations'),

     path('student/association/<str:access_number>/',
         views.AccessAssociationNumberDetailView.as_view(),  # 🚨 Assumed — see note below
         name='association_access_number_detail'),
    


    # urls.py — add these
    path('associations/<int:pk>/edit/',
         views.AssociationUpdateView.as_view(),
         name='association_update'),

    path('associations/<int:pk>/delete/',
         views.AssociationDeleteView.as_view(),
         name='association_delete'),     
    # Dead Semester Application URLs
    path('dead-semester-applications/', views.DeadSemesterApplicationListView.as_view(), name='dead_semester_applications'),
    #path('students/<int:student_pk>/dead-semester/', views.dead_semester_application_create_view, name='dead_semester_create'),
    path('dead-semester-applications/<int:pk>/', views.DeadSemesterApplicationDetailView.as_view(), name='dead_semester_detail'),
    path('dead-semester-applications/<int:dead_app_pk>/resumption/create', views.resumption_application_create_view, name='resumption_create'),
    path('dead-semester/select-student/', 
     views.select_student_for_dead_semester_view, 
     name='select_student_for_dead_semester'),

    path('dead-semester/create/<uuid:student_pk>/', 
     views.dead_semester_application_create_view, 
     name='dead_semester_create'),
    path(
    'dead-semester/<int:pk>/recommend/hod/',
    views.hod_recommend_view,
    name='hod_recommend_dead_semester'
    ),
    path(
    'dead-semester/<int:pk>/recommend/faculty/',
    views.faculty_recommend_view,
    name='faculty_recommend_dead_semester'
    ),
    path(
    'dead-semester/<int:pk>/recommend/registrar/',
    views.registrar_recommend_view,
    name='registrar_recommend_dead_semester'
    ),
    # Bbala Laptop Scheme URLs
    path('laptop-scheme/', views.BbalaLaptopSchemeListView.as_view(), name='laptop_scheme_list'),
    path('students/laptop/<uuid:student_pk>/laptop-scheme/', views.laptop_scheme_create_view, name='laptop_scheme_create'),
    path('laptop-scheme/<int:pk>/edit/', views.laptop_scheme_update_view, name='laptop_scheme_update'),
    path('laptop-scheme/select-student/',
     views.select_student_for_laptop_scheme_view,
     name='select_student_for_laptop_scheme'),
    # Medical and NCHE Registration
    
        # Existing URL pattern
    path('medical-registration/<str:access_number>/', views.medical_registration_view, name='medical_registration_view'),
    
    # New URL patterns for medical registration
    path('medical-registrations/', views.medical_registration_list, name='medical_registration_list'),
    path('medical-registrations/select-student/', views.select_student_for_medical, name='select_student_for_medical'),
    path('medical-registrations/create/<str:access_number>/', views.medical_registration_create, name='medical_registration_create'),
    path('medical-registrations/detail/<str:access_number>/', views.medical_registration_detail, name='medical_registration_detail'),

    #path('access/<str:access_number>/nche/', views.nche_registration_view, name='nche_registration'),
    
     # nche_registration
    path('nche-registration/student/<str:access_number>/', 
         views.nche_registration_view, 
         name='nche_registration'),

    path('nche-registration/select-student/', 
         views.student_selection_view, 
         name='student_selection'),

    path('nche-registration/<str:access_number>/delete/', 
         views.NCHERegistrationDeleteView.as_view(), 
         name='nche_registration_delete'),
    
    path('nche-registrations/', 
         views.NCHERegistrationListView.as_view(), 
         name='nche_registration_list'),

    path('student/detail/<uuid:student_id>/', views.StudentDetailsView.as_view(), name='student_details'),
    # Alternative if you want to support both UUID and registration number
    path('student/detail/<str:student_id>/', views.StudentDetailsView.as_view(), name='student_detailss'),
    # Internship
    #path('access/<str:access_number>/internship/', views.internship_view, name='internship'),
    path('internship/dashboard/', views.internship_dashboard, name='dashboard'),
    
    # Student search and selection
    path('students/internship/', views.student_search, name='student_search'),
    path('students/ajax-search/internship/', views.student_ajax_search, name='student_ajax_search'),
    
    # Internship CRUD operations
    path('internship/<str:access_number>/', views.internship_detail, name='internship_detail'),
    path('internship/<str:access_number>/edit/', views.internship_view, name='internship_edit'),
    path('internship/<str:access_number>/delete/', views.internship_delete, name='internship_delete'),
    
    # Internship list
    path('list/internship/', views.internship_list, name='internship_list'),

    # Semester clearance
    path('semester-clearance/select-student/', views.select_student_for_clearance, name='select_student_for_clearance'),
    path('semester-clearance/finance/<str:access_number>/', views.finance_clearance_view, name='finance_clearance'),
    path('semester-clearance/academic/<str:access_number>/', views.academic_clearance_view, name='academic_clearance'),
    path('semester-clearance/detail/<str:access_number>/', views.clearance_detail_view, name='clearance_detail'),
    path('semester-clearance/delete/<str:access_number>/', views.delete_clearance_view, name='delete_clearance'),
    # urls.py
    path('semester-clearance-list/', views.clearance_list_view, name='clearance_list'),
    path('semester/access/<str:access_number>/clearance/', views.semester_clearance_view, name='semester_clearance'),
    ###Graduation clearance
    path('students/<int:student_pk>/graduation-clearance/', views.graduation_clearance_view, name='graduation_clearance'),
     ##############   # Student selection and clearance list
    path('students/graduation/', views.student_selection_view, name='student_selection_view'),
    path('clearances/graduation/', views.graduation_clearance_list, name='graduation_clearance_list'),
    
    # CRUD operations for graduation clearance
    path('student/graduation/<uuid:student_pk>/clearance/create/', views.graduation_clearance_create, name='graduation_clearance_create'),
    path('student/graduation/<uuid:student_pk>/clearance/edit/', views.graduation_clearance_edit, name='graduation_clearance_edit'),
    path('student/graduation/<uuid:student_pk>/clearance/', views.graduation_clearance_detail, name='graduation_clearance_detail'),
    path('student/graduation/<uuid:student_pk>/clearance/delete/', views.graduation_clearance_delete, name='graduation_clearance_delete'),
    
    # Certificate generation
    path('student/graduation/<uuid:student_pk>/certificate/', views.graduation_certificate_view, name='graduation_certificate_view'),
    
    # Bulk actions
    path('bulk-action/graduation/', views.bulk_clearance_action, name='bulk_clearance_action'),






    # Reports
    path('reports/', views.reports_dashboard_view, name='reports'),
     # ... your existing URLs ...
    path('reports/students/', views.StudentReportView.as_view(), name='student_report'),
    path('reports/program-enrollment/', views.ProgramEnrollmentReportView.as_view(), name='program_enrollment_report'),
    
    #path('reports/semester-clearance/', views.semester_clearance_report, name='semester_clearance_report'),
    path('reports/semester-clearance/', views.semester_clearance_view, name='semester_clearance_report'),
    path('reports/semester-clearance/<int:academic_year_id>/<int:semester_id>/', 
         views.semester_clearance_view, name='semester_clearance_filtered'),
    path('reports/update-clearance-status/<str:access_number>/', 
         views.update_clearance_status, name='update_clearance_status'),
    path('reports/clearance-summary/<int:academic_year_id>/<int:semester_id>/', 
         views.clearance_summary_report, name='clearance_summary_report'),
    path('reports/course-units/', views.StudentCourseUnitReportView.as_view(), name='student_course_unit_report'),
    path('reports/finance-receivables/', views.FinanceReceivablesReportView.as_view(), name='finance_receivables_report'),
    path('reports/graduation-eligibility/', views.GraduationEligibilityReportView.as_view(), name='graduation_eligibility_report'),
    path('reports/dead-semester-applications/', views.DeadSemesterApplicationsReportView.as_view(), name='dead_semester_applications_report'),

    
    # API endpoints
    path('api/student-search/', views.student_search_api, name='student_search_api'),
    path('api/access-number-check/', views.access_number_check_api, name='access_number_check_api'),
    path('api/student-statistics/<int:student_pk>/', views.student_statistics_api, name='student_statistics_api'),
    
    # DRF API endpoints
    # Note: bulk endpoints must come before parameterized routes to avoid URL conflicts
    path('api/rest/programs/bulk/', api_views.BulkProgramCreateAPIView.as_view(), name='api_program_bulk'),
    path('api/rest/programs/', api_views.ProgramViewSet.as_view({'get': 'list', 'post': 'create'}), name='api_program_list'),
    path('api/rest/programs/<str:code>/', api_views.ProgramViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='api_program_detail'),
    
    path('api/rest/courses/bulk/', api_views.BulkCourseCreateAPIView.as_view(), name='api_course_bulk'),
    path('api/rest/courses/', api_views.CourseViewSet.as_view({'get': 'list', 'post': 'create'}), name='api_course_list'),
    path('api/rest/courses/<str:code>/', api_views.CourseViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='api_course_detail'),
    
    path('api/rest/course-units/bulk/', api_views.BulkCourseUnitCreateAPIView.as_view(), name='api_courseunit_bulk'),
    path('api/rest/course-units/', api_views.CourseUnitViewSet.as_view({'get': 'list', 'post': 'create'}), name='api_courseunit_list'),
    path('api/rest/course-units/<str:code>/', api_views.CourseUnitViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='api_courseunit_detail'),
    
    path('api/rest/students/bulk/', api_views.BulkStudentCreateAPIView.as_view(), name='api_student_bulk'),
    path('api/rest/students/', api_views.StudentViewSet.as_view({'get': 'list', 'post': 'create'}), name='api_student_list'),
    path('api/rest/students/<str:registration_number>/', api_views.StudentViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='api_student_detail'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


