from django.shortcuts import render
from .utils import create_unique_object_id, pwd_context, output_format
from .db import auth_collection, database, fields, jwt_life, jwt_secret
import jwt
import datetime
from rest_framework.response import Response
from django.http import HttpResponse, JsonResponse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import api_view
from rest_framework import status
import time

# Create your views here.


@api_view(["POST"])
def signup(request):
    data = request.data if request.data is not None else {}
    print(data)
    all_fields = fields + ("first_name","last_name","date_of_birth","gender","contact_number","address_line_1","address_line_2","landmark","pincode","role")
    if data != {}:
        data["_id"] = create_unique_object_id()
        for field in all_fields:
            if field in data:
                continue
            else:
                return JsonResponse(data={"message":"Wrong data provided!"},status = status.HTTP_400_BAD_REQUEST)
        data["password"] = pwd_context.hash(data["password"])
        if database[auth_collection].find_one({"email":data["email"]}) is None:
            try:
                database[auth_collection].insert_one(data)
                return JsonResponse(data=data,status=status.HTTP_201_CREATED)
            except:
                return JsonResponse(data={"message":"User not Sign up"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return JsonResponse(data={"message":"User Already Exists"},status=status.HTTP_400_BAD_REQUEST)
    else:
        return JsonResponse(data={"message":"Didn't receive signup data"},status=status.HTTP_400_BAD_REQUEST)



@api_view(["POST"])
def login(request):
    data = request.data if request.data is not None else {}
    if data != {}:
        email = data["email"]
        password = data["password"]
        
        if "@" in email:
            user = database[auth_collection].find_one({"email":email})
        else:
            return JsonResponse(data={"message":"Wrong Email Format"},status = status.HTTP_400_BAD_REQUEST)
        
        if user is not None:
            if pwd_context.verify(password,user["password"]):
                token = jwt.encode({
                        "id":{
                            "id":user["_id"],
                            "role":user["role"]
                        },
                        "exp":datetime.datetime.now() + datetime.timedelta(days=jwt_life)
                    },
                    jwt_secret,
                    algorithm="HS256"
                )
                if type(token) == str:
                    return JsonResponse(data={"message":"Successfully Logged In","token":token},status=status.HTTP_200_OK)
                else:
                    return JsonResponse(data={"message":"Token not created"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return JsonResponse(data={"message":"Incorrect Password"},status=status.HTTP_400_BAD_REQUEST)
    else:
        return JsonResponse(data={"message":"Didn't Receive Login Data"},status = status.HTTP_400_BAD_REQUEST)

@api_view(["POST","GET","PATCH"])
def manage_student(request,id):
    if request.method == "POST":
        college_admin = database["User"].find_one(filter={"_id":request.id,"role":request.role})
        
        if college_admin["role"] == "college-admin" and college_admin["_id"] == request.id:
            data = request.data if request.data is not None else {}
            if id is not None:
                print(id)
                user = database["User"].find_one(filter={"_id":id,"role":"Student"})
                data["_id"] = create_unique_object_id()
                data["User_ID"] = id
                student_fields = ("gr_number","roll_number","admission_date","admission_valid_date","division_id")
                for field in student_fields:
                    if field in data:
                        continue
                    else:
                        return JsonResponse(data={"message":"Wrong Data Provided"},status=status.HTTP_400_BAD_REQUEST)
                database["Student"].insert_one(data)
                return JsonResponse(data={"user":user},status=status.HTTP_201_CREATED)
            else:
                return JsonResponse(data={"message":"Didn't receive student data"})
            return JsonResponse(data=data,status=status.HTTP_200_OK)
        pass
    elif request.method == "PATCH":
        college_admin = database["User"].find_one(filter={"_id":request.id,"role":request.role})
        if college_admin["role"] == "college-admin" and college_admin["_id"] == request.id:
            data = request.data if request.data is not None else {}
            if id is not None and data is not None:
                print(id)
                user = database["Student"].find_one(filter={"_id":id})
                if user:
                    newValues = {"$set":data}
                    print(newValues)
                    database["Student"].update_one(filter={"_id":id},update=newValues)
                    return JsonResponse(data=user)
                else:
                    return JsonResponse(data={"message":"Student Not found"})
    elif request.method == "GET":
        user = database["User"].find_one(filter={"_id":request.id,"role":request.role})
        
        if user["role"] == "college-admin" and user["_id"] == request.id:
            data = database["User"].find(filter={"role":"Student"})
            data = [i for i in data]
            return JsonResponse(data=data,status=status.HTTP_200_OK,safe=False)

def get_students(request):
    user = database["User"].find_one(filter={"_id":request.id,"role":request.role})

    if user["role"] == "college-admin" and user["_id"] == request.id:
        data = database["User"].find(filter={"role":"Student"})
        data = [i for i in data]
        return JsonResponse(data=data,status=status.HTTP_200_OK,safe=False)
    else:
        return JsonResponse(data={"message":"User not Authorized"},status=status.HTTP_401_UNAUTHORIZED)
    