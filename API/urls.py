from django.urls import path
from . import views

urlpatterns = [
    
    #login and signup routes
    
    path("login/",views.login,name="login"), #done
    path("signup/",views.signup,name="signup"), # done
    
    #College-admin's routes
    
    path("get-students/",views.get_students,name="get-students"), # done
    path("manage-student/<str:id>/",views.manage_student,name="manage-student"), # done
    path("get-timetable/",views.get_timetable,name="get-timetable"), # done
    path("manage-timetable/<str:id>/",views.manage_timetable,name="manage-timetable"), # done
    path("manage-timetable/",views.manage_timetable,name="manage-timetable"), # done
    path("get-required-timetable-details/",views.required_timetable_details,name="get-required-timetable-details"),
    
    # Faculty's routes
    path("correct-attendance/<str:id>/",views.correct_attendance,name="correct-attendance"), # done
    path("get-queries/",views.get_queries,name="get-queries"), # done
    path("get-queries/<str:id>/",views.get_queries,name="get-queries"), # done
    path("answer-query/<str:id>/",views.answer_query,name="answer-query"), # done

    # Get Attendance route 
    path("get-attendance/",views.get_attendance,name="get-attendance"), # done
    path("get-attendance/<str:id>/",views.get_attendance,name="get-attendance"), # done
    
    # Student Routes
    path("manage-biometrics/",views.manage_biometrics,name="manage-biometrics"), # done
    path("query/",views.query,name="query"), # done
    
    #attendance-system routes
    path("attendance/",views.attendance,name="attendance"), # done
    
    # Admin routes
    # path("manage-faculty",views.manage_faculty,name="manage-faculty"),
    # path("manage-college-admin",views.manage_college_admin,name="manage-college-admin")""
]   