from django.urls import path
from . import views

urlpatterns = [
    path("login/",views.login,name="login"),
    path("signup/",views.signup,name="signup"),
    path("get-students/",views.get_students,name="get-students"),
    path("manage-student/<str:id>",views.manage_student,name="manage-student"),
]
