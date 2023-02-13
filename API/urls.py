from django.urls import path
from . import views

urlpatterns = [
    
    #login and signup routes
    
    path("login/",views.login,name="login"),
    path("signup/",views.signup,name="signup"),
    
    #College-admin's routes
    
    path("get-students/",views.get_students,name="get-students"),
    path("manage-student/<str:id>/",views.manage_student,name="manage-student"),
    path("get-timetable/",views.get_timetable,name="get-timetable"),
    # path("manage-timetable/<str:id>/",views.manage_timetable,name="manage-timetable"),
    
    # Faculty's routes
    # path("correct-attendance/<str:id>/",views.correct_attendance,name="correct-attendance"),
    path("get-queries/",views.get_queries,name="get-queries"),
    # path("answer-query/<str:id>/",views.answer_query,name="answer-query"),

    # Get Attendance route 
    # path("get-attendance/",views.get_attendance,name="get-attendance"),
    
    # Student Routes
    path("manage-biometrics/<str:id>/",views.manage_biometrics,name="manage-biometrics"),
    # path("query/",views.query,name="query"),
    
    #attendance-system routes
    path("attendance/",views.attendance,name="attendance"),
    
    # Admin routes
    # path("manage-faculty",views.manage_faculty,name="manage-faculty"),
    # path("manage-college-admin",views.manage_college_admin,name="manage-college-admin")
]