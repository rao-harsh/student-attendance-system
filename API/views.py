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
from deepface import DeepFace
import cv2
import numpy as np
import matplotlib.pyplot as plt
import json
# Create your views here.

class NumpyEncoder(json.JSONEncoder):
    def default(self,obj):
        if isinstance(obj,np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self,obj)



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
                    newData = database["Student"].find_one(filter={"_id":id})
                    print(newData)
                    return JsonResponse(data=newData)
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

@api_view(["POST"])
def register_face(request,id):
    if request.method == "POST":
        data = request.data if request.data is not None else {}
        image = request.FILES["face-image"]
        if data:
            del data['face-image']
            img = np.fromstring(image.read(),np.uint8)
            img = cv2.imdecode(img,cv2.IMREAD_UNCHANGED)
            image_json = json.dumps(img,cls=NumpyEncoder)
            # data["image"] = image_json
            # print(img)
            # img = np.reshape(img,(152,152))
            img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)  
            face_encodings = DeepFace.represent(img,enforce_detection=False,model_name="Facenet512")
            # data["face"] = json.dumps(face_encodings,cls=NumpyEncoder)
            data["face"] = face_encodings[0]["embedding"]
            student = database["Student"].find_one(filter={"gr_number":int(id)})
            face_data = {
                "_id":create_unique_object_id(),
                "student_id":student["_id"],
                "face_data":data["face"]
            }
            database["face_data"].insert_one(document=face_data)
            # print(face_encodings[0]["embedding"])
            # print(len(face_encodings[)
            
            return JsonResponse(data=data,safe=False)
        else:
            return JsonResponse(data={"message":"data is not sended"})