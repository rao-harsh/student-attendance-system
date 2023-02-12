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
from mtcnn import MTCNN
# Create your views here.


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


@api_view(["POST"])
def signup(request):
    data = request.data if request.data is not None else {}
    print(data)
    all_fields = fields + ("first_name", "last_name", "date_of_birth", "gender",
                           "contact_number", "address_line_1", "address_line_2", "landmark", "pincode", "role")
    if data != {}:
        data["_id"] = create_unique_object_id()
        for field in all_fields:
            if field in data:
                continue
            else:
                return JsonResponse(data={"message": "Wrong data provided!"}, status=status.HTTP_400_BAD_REQUEST)
        data["password"] = pwd_context.hash(data["password"])
        if database[auth_collection].find_one({"email": data["email"]}) is None:
            try:
                database[auth_collection].insert_one(data)
                return JsonResponse(data=data, status=status.HTTP_201_CREATED)
            except:
                return JsonResponse(data={"message": "User not Sign up"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return JsonResponse(data={"message": "User Already Exists"}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return JsonResponse(data={"message": "Didn't receive signup data"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def login(request):
    data = request.data if request.data is not None else {}
    if data != {}:
        email = data["email"]
        password = data["password"]

        if "@" in email:
            user = database[auth_collection].find_one({"email": email})
        else:
            return JsonResponse(data={"message": "Wrong Email Format"}, status=status.HTTP_400_BAD_REQUEST)

        if user is not None:
            if pwd_context.verify(password, user["password"]):
                token = jwt.encode({
                    "id": {
                        "id": user["_id"],
                        "role": user["role"]
                    },
                    "exp": datetime.datetime.now() + datetime.timedelta(days=jwt_life)
                },
                    jwt_secret,
                    algorithm="HS256"
                )
                if type(token) == str:
                    return JsonResponse(data={"message": "Successfully Logged In", "token": token}, status=status.HTTP_200_OK)
                else:
                    return JsonResponse(data={"message": "Token not created"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return JsonResponse(data={"message": "Incorrect Password"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return JsonResponse(data={"message":"User not found"},status=status.HTTP_404_NOT_FOUND)
    else:
        return JsonResponse(data={"message": "Didn't Receive Login Data"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST", "GET", "PATCH"])
def manage_student(request, id):
    if request.method == "POST":
        college_admin = database["User"].find_one(
            filter={"_id": request.id, "role": request.role})

        if college_admin["role"] == "college-admin" and college_admin["_id"] == request.id:
            data = request.data if request.data is not None else {}
            if id is not None:
                print(id)
                user = database["User"].find_one(
                    filter={"_id": id, "role": "Student"})
                data["_id"] = create_unique_object_id()
                data["User_ID"] = id
                student_fields = (
                    "gr_number", "roll_number", "admission_date", "admission_valid_date", "division_id")
                for field in student_fields:
                    if field in data:
                        continue
                    else:
                        return JsonResponse(data={"message": "Wrong Data Provided"}, status=status.HTTP_400_BAD_REQUEST)
                database["Student"].insert_one(data)
                return JsonResponse(data={"user": user}, status=status.HTTP_201_CREATED)
            else:
                return JsonResponse(data={"message": "Didn't receive student data"})
    elif request.method == "PATCH":
        college_admin = database["User"].find_one(
            filter={"_id": request.id, "role": request.role})
        if college_admin["role"] == "college-admin" and college_admin["_id"] == request.id:
            data = request.data if request.data is not None else {}
            if id is not None and data is not None:
                print(id)
                user = database["Student"].find_one(filter={"_id": id})
                if user:
                    newValues = {"$set": data}
                    print(newValues)
                    database["Student"].update_one(
                        filter={"_id": id}, update=newValues)
                    newData = database["Student"].find_one(filter={"_id": id})
                    print(newData)
                    return JsonResponse(data=newData)
                else:
                    return JsonResponse(data={"message": "Student Not found"})
    elif request.method == "GET":
        user = database["User"].find_one(
            filter={"_id": request.id, "role": request.role})

        if user["role"] == "college-admin" and user["_id"] == request.id:
            data = database["User"].find(filter={"role": "Student"})
            data = [i for i in data]
            return JsonResponse(data=data, status=status.HTTP_200_OK, safe=False)


def get_students(request):
    user = database["User"].find_one(
        filter={"_id": request.id, "role": request.role})

    if user["role"] == "college-admin" and user["_id"] == request.id:
        data = database["User"].find(filter={"role": "Student"})
        data = [i for i in data]
        return JsonResponse(data=data, status=status.HTTP_200_OK, safe=False)
    else:
        return JsonResponse(data={"message": "User not Authorized"}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(["POST"])
def register_face(request, id):
    if request.method == "POST":
        data = request.data if request.data is not None else {}
        image = request.FILES["face-image"]
        if data:
            del data['face-image']
            img = np.fromstring(image.read(), np.uint8)
            img = cv2.imdecode(img, cv2.IMREAD_UNCHANGED)
            image_json = json.dumps(img, cls=NumpyEncoder)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            face_encodings = DeepFace.represent(
                img, enforce_detection=False, model_name="Facenet512")
            data["face"] = face_encodings[0]["embedding"]
            student = database["Student"].find_one(
                filter={"gr_number": int(id)})
            face_data = {
                "_id": create_unique_object_id(),
                "student_id": student["_id"],
                "face_data": data["face"]
            }
            database["face_data"].insert_one(document=face_data)
            return JsonResponse(data=data, safe=False)
        else:
            return JsonResponse(data={"message": "data is not sended"})


@api_view(["POST"])
def attendance(request):
    if request.method == "POST":
        data = request.data if request.data is not None else {}
        image = request.FILES["class-frames"]
        if data:
            face_data = []
            del data["class-frames"]
            img = np.fromstring(image.read(), np.uint8)
            img = cv2.imdecode(img, cv2.IMREAD_UNCHANGED)
            detector = MTCNN()
            faces = detector.detect_faces(img)
            print(len(faces))
            embeddings = []
            for face in faces:
                x, y, w, h = face["box"]
                crop = img[y:y+h, x:x+w]
                target_embedding = DeepFace.represent(crop,enforce_detection=False,model_name="Facenet512")
                # return JsonResponse(data=face_data)
                embeddings.append(target_embedding)
            
            
            for embedding in embeddings:
                
                #to find cosine similarity between to faces
                pipeline = [
                    {
                        "$addFields":{
                            "target_embedding":embedding[0]["embedding"]
                        }
                    },
                    {
                        "$project":{
                            "student_id":1,
                            "cos_sim_params":{
                                "$reduce":{
                                    "input":{"$range":[0,{"$size":"$face_data"}]},
                                    "initialValue":{
                                        "dot_product":0,
                                        "doc_2_sum":0,
                                        "target_2_sum":0
                                    },
                                    "in":{
                                        "$let":{
                                            "vars":{
                                                "doc_elem":{"$arrayElemAt":["$face_data","$$this"]},
                                                "target_elem":{"$arrayElemAt":["$target_embedding","$$this"]}
                                            },
                                            "in":{
                                                "dot_product":{
                                                    "$add":[
                                                        "$$value.dot_product",
                                                        {"$multiply":["$$doc_elem","$$target_elem"]}
                                                    ]
                                                },
                                                "doc_2_sum":{
                                                    "$add":[
                                                        "$$value.doc_2_sum",
                                                        {"$pow":["$$doc_elem",2]}
                                                    ]
                                                },
                                                "target_2_sum":{
                                                    "$add":[
                                                        "$$value.target_2_sum",
                                                        {"$pow":["$$target_elem",2]}
                                                    ]
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    {
                        "$project":{
                            "_id":1,
                            "student_id":1,
                            "cos_sim":{
                                "$divide":[
                                    "$cos_sim_params.dot_product",
                                    {
                                        "$sqrt":{
                                            "$multiply":[
                                                "$cos_sim_params.doc_2_sum",
                                                "$cos_sim_params.target_2_sum"
                                            ]
                                        }
                                    }
                                ]
                            },
                        },
                    },
                    {
                        "$match":{
                            "cos_sim":{
                                "$gte":0.5
                            }
                        }
                    },
                    {
                        "$sort":{
                            "cos_sim":-1
                        }
                    },
                    {
                        "$limit":1
                    }
                ]
                student_details = database["face_data"].aggregate(pipeline=pipeline)
                face_data.append(list(student_details))
            all_present = []
            all_student = database["Student"].find()
            for face in face_data:
                if face != []:
                    student = database["Student"].find_one(filter={"_id":face[0]["student_id"]})
                    all_present.append(student)
            present_ids = [i["_id"] for i in all_present]
            # print(_ids)
            all_student = list(all_student)
            for student in all_student:
                if student["_id"] in present_ids:
                    all_student.remove(student)
            present_student = all_present
            absent_student = all_student
            # for face in face_data:
            #     for student in all_students:
            #         instance = {}
            #         instance["roll_number"] = student["roll_number"]
            #         instance["_id"] = create_unique_object_id()
            #         if face[0]["student_id"] == student["_id"]:
            #             instance["attendance"] = True
            #             present_student.append(instance)
            absent_ids = [i["_id"] for i in absent_student]
            absent_student = []
            # for i in absent_ids:
            #     if i in present_ids:
            #         absent_ids.remove(i)
            
            present_ids = set(present_ids)
            absent_ids = set(absent_ids)
            
            absent_ids = list(absent_ids - present_ids)
            for absent in absent_ids:
                # absent_student.append(list(database["Student"].find_one({"_id":absent},{"_id":1,"roll_number":1})))
                student = database["Student"].find_one({"_id":absent},{"_id":1,"roll_number":1})
                absent_student.append(student)
            present_student = []
            for present in present_ids:
                student = database["Student"].find_one({"_id":present},{"_id":1,"roll_number":1})
                present_student.append(student)
            # present_absent_data = present_student + absent_student
            print(all_present)
            return JsonResponse(data={"present":present_student,"absent":absent_student})
