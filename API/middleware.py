# User defined middleware for checking user tokens
from django.http import JsonResponse
import jwt
import datetime
from API.db import database,jwt_secret
from django.urls import resolve
from .utils import output_format
import base64
from rest_framework import status

class JWTAuthenticateMiddleware:
    def __init__(self,get_response) -> None:
        self.get_response = get_response
        
        # APIs going through middleware
        self.allowed_apis = [
            "manage-timetable",
            "manage-student",
            "get-students",
            "manage-biometrics",
            "get-timetable",
            "correct-attendance",
            "get-queries",
            "answer-query",
            "get-attendance",
            "query",
            "manage-faculty",
            "manage-college-admin",
            "get-required-timetable-details"
        ]
    
    def __call__(self,request):
        
        # getting name of the view
        
        url = resolve(request.path_info)
        view_name = url.view_name
        
        print("view name : ",view_name)
        
        if view_name in self.allowed_apis:
            
            try:
                token = request.headers["Authorization"].split()[1].strip('\"')
            except:
                return JsonResponse(data={"message":"Token not found!"},status=status.HTTP_401_UNAUTHORIZED)
            
            result = JWTAuthenticateMiddleware.has_key(token)
            
            if type(result) == JsonResponse:
                return result
            
            if result is not None:
                print("has_key : ", result)
                #checking if expired
                if datetime.datetime.fromtimestamp(result['exp']) > datetime.datetime.now():
                    request.id = result['id']
                    request.role = result['role']
            else:
                return JsonResponse(data={"message":"Token Expired!\nLogin Again"},status=status.HTTP_400_BAD_REQUEST)
        
        response = self.get_response(request)
        return response
    
    def has_key(token:str):
        try:
            return jwt.decode(token, jwt_secret, algorithms="HS256")
        except jwt.exceptions.ExpiredSignatureError as exp_err:
            return None
        except Exception:
            return JsonResponse(data={"message":"Token Corrupted!"},status=status.HTTP_400_BAD_REQUEST)