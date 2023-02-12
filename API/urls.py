from django.urls import path
from . import views

urlpatterns = [
    
    #login and signup routes
    
    path("login/",views.login,name="login"),
    path("signup/",views.signup,name="signup"),
    
    #College-admin's routes
    
    path("get-students/",views.get_students,name="get-students"),
    path("manage-student/<str:id>/",views.manage_student,name="manage-student"),
    
    
    
    # Student Routes
    path("register-face/<str:id>/",views.register_face,name="register-face"),
    
    #attendance-system routes
    path("attendance/",views.attendance,name="attendance")
]