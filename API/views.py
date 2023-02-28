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
from deepface import DeepFace
import cv2
import numpy as np
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
                return JsonResponse(data={"message": "User Registered"}, status=status.HTTP_201_CREATED)
            except:
                return JsonResponse(data={"message": "User not Sign up"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return JsonResponse(data={"message": "User Already Exists"}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return JsonResponse(data={"message": "Didn't receive signup data"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def login(request):
    data = request.data if request.data is not None else {}
    if data:
        email = data["email"]
        password = data["password"]

        if "@" in email:
            user = database[auth_collection].find_one({"email": email})
        else:
            return JsonResponse(data={"message": "Wrong Email Format"}, status=status.HTTP_400_BAD_REQUEST)

        if user is not None:
            if pwd_context.verify(password, user["password"]):
                payload = {
                    "id": user["_id"],
                    "role": user["role"],
                    "exp": datetime.datetime.now() + datetime.timedelta(days=jwt_life)
                }
                token = jwt.encode(payload, jwt_secret, algorithm="HS256")
                if type(token) == str:
                    return JsonResponse(data={"message": "Successfully Logged In", "token": token, "role": user["role"]}, status=status.HTTP_200_OK)
                else:
                    return JsonResponse(data={"message": "Token not created"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return JsonResponse(data={"message": "Incorrect Password"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return JsonResponse(data={"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    else:
        return JsonResponse(data={"message": "Didn't Receive Login Data"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST", "GET", "PATCH", "DELETE"])
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
                user = database["Student"].find_one(filter={"User_ID": id})
                if user:
                    newValues = {"$set": data}
                    print(newValues)
                    try:
                        database["Student"].update_one(
                            filter={"User_ID": id}, update=newValues)
                        return JsonResponse(data={"message": "Student Updated Successfully"}, status=status.HTTP_200_OK)
                    except:
                        return JsonResponse(data={"message": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                else:
                    return JsonResponse(data={"message": "Student Not found"}, status=status.HTTP_404_NOT_FOUND)
    elif request.method == "GET":
        user = database["User"].find_one(
            filter={"_id": request.id, "role": request.role})

        if user["role"] == "college-admin" and user["_id"] == request.id:
            data = database["User"].find(filter={"role": "Student"})
            data = [i for i in data]
            return JsonResponse(data=data, status=status.HTTP_200_OK, safe=False)
        else:
            return JsonResponse(data={"message": "User not Authorized"}, status=status.HTTP_401_UNAUTHORIZED)
    elif request.method == "DELETE":
        user = database["User"].find_one(
            filter={"_id": request.id, "role": request.role})

        if user["role"] == "college-admin" and user["_id"] == request.id:
            database["Student"].update_one(filter={"User_ID": id}, update={
                                           "$set": {"is_deleted": True}})
            return JsonResponse(data={"message": "User deleted"}, status=status.HTTP_200_OK)
        else:
            return JsonResponse(data={"message": "User not Authorized"}, status=status.HTTP_401_UNAUTHORIZED)


def get_students(request):
    user = database["User"].find_one(
        filter={"_id": request.id, "role": request.role})

    if user["role"] == "college-admin" and user["_id"] == request.id:
        pipeline = [
            {
                "$lookup": {
                    "from": "User",
                    "localField": "User_ID",
                    "foreignField": "_id",
                    "as": "user"
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "gr_number": 1,
                    "roll_number": 1,
                    "user.first_name": 1,
                    "user.last_name": 1,
                    "user.contact_number": 1,
                    "user.email": 1,
                    "user._id": 1,
                    "is_deleted": 1
                }
            },
            {
                "$match": {
                    "is_deleted": {
                        "$ne": True
                    }
                }
            }
        ]
        data = database["Student"].aggregate(pipeline)
        data = list(data)
        return JsonResponse(data=data, status=status.HTTP_200_OK, safe=False)
    else:
        return JsonResponse(data={"message": "User not Authorized"}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(["POST", "PATCH"])
def manage_biometrics(request):
    user = database[auth_collection].find_one(
        filter={"_id": request.id, "role": request.role})

    if user["role"] == "Student" and user["_id"] == request.id:
        data = request.data if request.data is not None else {}
        image = request.FILES["face-image"]
        if data:
            del data['face-image']
            img = np.fromstring(image.read(), np.uint8)
            img = cv2.imdecode(img, cv2.IMREAD_UNCHANGED)
            print(img)
            image_json = json.dumps(img, cls=NumpyEncoder)
            print(image_json)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            print(img)
            detector = MTCNN()
            face = detector.detect_faces(img)
            print(face)
            if len(face) == 0:
                return JsonResponse(data={"message": "Face not found please upload proper image"}, status=status.HTTP_400_BAD_REQUEST)
            face_embedding = DeepFace.represent(
                img, enforce_detection=False, model_name="Facenet512")
            data["face"] = face_embedding[0]["embedding"]
            student = database["Student"].find_one(
                filter={"User_ID": request.id})
            print(request.id)
            if request.method == "POST":
                face_data = {
                    "_id": create_unique_object_id(),
                    "student_id": student["_id"],
                    "face_data": data["face"]
                }
                database["face_data"].insert_one(document=face_data)
                return JsonResponse(data={"message": "Successfully Uploaded"}, status=status.HTTP_201_CREATED)
            elif request.method == "PATCH":
                update = {
                    "$set": {
                        "face_data": data["face"]
                    }
                }
                face_data = database["face_data"].find_one_and_update(
                    filter={"gr_number": student["_id"]}, update=update)
                return JsonResponse(data={"message": "Successfully Updated"}, status=status.HTTP_200_OK)
        else:
            return JsonResponse(data={"message": "data is not sended"})
    else:
        return JsonResponse(data={"message": "User is not Authorized"}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(["POST"])
def attendance(request):
    if request.method == "POST":
        image = request.FILES["class-frames"]
        # image = data["class-frames"]
        if image:
            face_data = []
            img = np.fromstring(image.read(), np.uint8)
            img = cv2.imdecode(img, cv2.IMREAD_UNCHANGED)
            detector = MTCNN()
            faces = detector.detect_faces(img)
            print(len(faces))
            embeddings = []
            for face in faces:
                x, y, w, h = face["box"]
                crop = img[y:y+h, x:x+w]
                target_embedding = DeepFace.represent(
                    crop, enforce_detection=False, model_name="Facenet512")
                # return JsonResponse(data=face_data)
                embeddings.append(target_embedding)

            for embedding in embeddings:

                # to find cosine similarity between to faces
                pipeline = [
                    {
                        "$addFields": {
                            "target_embedding": embedding[0]["embedding"]
                        }
                    },
                    {
                        "$project": {
                            "student_id": 1,
                            "cos_sim_params": {
                                "$reduce": {
                                    "input": {"$range": [0, {"$size": "$face_data"}]},
                                    "initialValue": {
                                        "dot_product": 0,
                                        "doc_2_sum": 0,
                                        "target_2_sum": 0
                                    },
                                    "in": {
                                        "$let": {
                                            "vars": {
                                                "doc_elem": {"$arrayElemAt": ["$face_data", "$$this"]},
                                                "target_elem":{"$arrayElemAt": ["$target_embedding", "$$this"]}
                                            },
                                            "in":{
                                                "dot_product": {
                                                    "$add": [
                                                        "$$value.dot_product",
                                                        {"$multiply": [
                                                            "$$doc_elem", "$$target_elem"]}
                                                    ]
                                                },
                                                "doc_2_sum":{
                                                    "$add": [
                                                        "$$value.doc_2_sum",
                                                        {"$pow": [
                                                            "$$doc_elem", 2]}
                                                    ]
                                                },
                                                "target_2_sum":{
                                                    "$add": [
                                                        "$$value.target_2_sum",
                                                        {"$pow": [
                                                            "$$target_elem", 2]}
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
                        "$project": {
                            "_id": 1,
                            "student_id": 1,
                            "cos_sim": {
                                "$divide": [
                                    "$cos_sim_params.dot_product",
                                    {
                                        "$sqrt": {
                                            "$multiply": [
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
                        "$match": {
                            "cos_sim": {
                                "$gte": 0.5
                            }
                        }
                    },
                    {
                        "$sort": {
                            "cos_sim": -1
                        }
                    },
                    {
                        "$limit": 1
                    }
                ]
                student_details = database["face_data"].aggregate(
                    pipeline=pipeline)
                face_data.append(list(student_details))
            all_present = []
            all_student = database["Student"].find()
            for face in face_data:
                if face != []:
                    student = database["Student"].find_one(
                        filter={"_id": face[0]["student_id"]})
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
                student = database["Student"].find_one(
                    {"_id": absent}, {"_id": 1, "roll_number": 1, 'User_ID': 1})
                absent_student.append(student)
            present_student = []
            for present in present_ids:
                student = database["Student"].find_one(
                    {"_id": present}, {"_id": 1, "roll_number": 1, 'User_ID': 1})
                present_student.append(student)
            # present_absent_data = present_student + absent_student
            print(all_present)
            instances = []
            for present in present_student:
                instance = {}
                instance["_id"] = create_unique_object_id()
                instance["student_id"] = present["_id"]
                instance["roll_number"] = present["roll_number"]
                instance["attendance"] = True
                instances.append(instance)
            for absent in absent_student:
                instance = {}
                instance["_id"] = create_unique_object_id()
                instance["student_id"] = absent["_id"]
                instance["roll_number"] = absent["roll_number"]
                instance["attendance"] = False
                instances.append(instance)

            try:
                database["attendance"].insert_many(instances)
                return JsonResponse(data={"present": present_student, "absent": absent_student}, status=status.HTTP_200_OK)
            except:
                return JsonResponse(data={"message": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return JsonResponse(data={"message": "Image not Found"}, status=status.HTTP_400_BAD_REQUEST)

def get_timetable(request):
    user = database["User"].find_one(
        filter={"_id": request.id, "role": request.role})
    if user["role"] == "college-admin" and user["_id"] == request.id:
        pipeline = [
            {
                "$lookup": {
                    "from": "subject",
                    "localField": "subject_id",
                    "foreignField": "_id",
                    "as": "subject"
                }
            },
            {
                "$lookup": {
                    "from": "User",
                    "localField": "faculty_id",
                    "foreignField": "_id",
                    "as": "faculty"
                }
            },
            {
                "$lookup": {
                    "from": "semester",
                    "localField": "semester_id",
                    "foreignField": "_id",
                    "as": "semester"
                }
            },
            {
                "$lookup": {
                    "from": "division",
                    "localField": "division",
                    "foreignField": "_id",
                    "as": "division"
                }
            },
            {"$unwind": "$subject"},
            {"$unwind": "$faculty"},
            {"$unwind": "$division"},
            {"$unwind": "$semester"},
            {
                "$project": {
                    "_id": 1,
                    "remarks": 1,
                    "room_number": 1,
                    "start_time": 1,
                    "end_time": 1,
                    "faculty.first_name": 1,
                    "faculty.last_name": 1,
                    "semester.semester_name": 1,
                    "division.division_name": 1,
                    "subject.subject_name": 1
                }
            }
        ]
        data = database["timetable"].aggregate(pipeline)
        data = list(data)
        return JsonResponse(data=data, status=status.HTTP_200_OK, safe=False)
    else:
        return JsonResponse(data={"message": "User not Authorized"}, status=status.HTTP_401_UNAUTHORIZED)


def get_queries(request,id=None):
    user = database["User"].find_one(
        filter={"_id": request.id, "role": request.role})
    if user["role"] == "Faculty" and user["_id"] == request.id:
        
        if id is not None:
            query = database["query"].find_one({"_id":id},{"query":1})
            query = dict(query)
            print(query)
            return JsonResponse(query,status= status.HTTP_200_OK,safe=False)
        
        pipeline = [
            {
                "$lookup": {
                    "from": "Student",
                    "localField": "student_id",
                    "foreignField": "_id",
                    "as": "student"
                }
            },
            {"$unwind": "$student"},
            {
                "$lookup": {
                    "from": "User",
                    "localField": "student.User_ID",
                    "foreignField": "_id",
                    "as": "user"
                }
            },
            {"$unwind": "$user"},
            {
                "$project": {
                    "_id": 1,
                    "query":1,
                    "query_raised_date":1,
                    "student.gr_number": 1,
                    "student.roll_number": 1,
                    "user.first_name": 1,
                    "user.last_name": 1,
                    "user.email":1
                }
            }
        ]
        data = database["query"].aggregate(pipeline)
        data = [i for i in data]
        return JsonResponse(data=data, status=status.HTTP_200_OK, safe=False)
    else:
        return JsonResponse(data={"message": "User not Authorized"}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(["POST"])
def query(request):
    user = database["User"].find_one(
        filter={"_id": request.id, "role": request.role})

    if user["role"] == "Student" and user["_id"] == request.id:
        data = request.data if request.data else {}
        if data:
            if "query" not in data:
                return JsonResponse(data={"message": "Wrong Data Provided!"}, status=status.HTTP_400_BAD_REQUEST)
            date = datetime.datetime.now()
            student_details = database["Student"].find_one({"User_ID":user["_id"]},{"_id":1})
            query_data = {
                "_id": create_unique_object_id(),
                "student_id": student_details["_id"],
                "query": data["query"],
                "query_raised_date": f"{date.day}-{date.month}-{date.year}"
            }
            print(query_data)
            try:
                database["query"].insert_one(query_data)
                return JsonResponse(data={"message": "Query Successfully Submitted"}, status=status.HTTP_200_OK)
            except:
                return JsonResponse(data={"message": "Internal Server Erorr"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return JsonResponse(data={"message": "No Data Provided"}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return JsonResponse(data={"message": "User Not Authorized"}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(["POST"])
def answer_query(request, id):
    user = database[auth_collection].find_one(
        filter={"_id": request.id, "role": request.role})

    if user["role"] == "Faculty" and user["_id"] == request.id:
        data = request.data if request.data else {}
        if data:
            if "answer" not in data:
                return JsonResponse(data={"message": "Wrong Data Provided!"}, status=status.HTTP_400_BAD_REQUEST)
            date = datetime.datetime.now()
            answer_data = {
                "_id": create_unique_object_id(),
                "query_id": id,
                "faculty_id": user["_id"],
                "answer_of_query": data["answer"],
                "query_resolved_data": f"{date.day}-{date.month}-{date.year}"
            }
            try:
                database["query_answer"].insert_one(answer_data)
                return JsonResponse(data={"message": "Answer Successfully Submitted!"}, status=status.HTTP_201_CREATED)
            except:
                return JsonResponse(data={"message": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return JsonResponse(data={"message": "No Data Provided"}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return JsonResponse(data={"message": "User Not Authorized"}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(["POST", "PATCH", "DELETE"])
def manage_timetable(request, id=None):
    user = database[auth_collection].find_one(
        filter={"_id": request.id, "role": request.role})
    all_fields = ("subject_id", "faculty_id", "division",
                  "semester_id", "remarks", "room_number", "start_time", "end_time")
    if user["role"] == "college-admin" and user["_id"] == request.id:
        data = request.data if request.data else {}

        if request.method == "DELETE":
            try:
                database["timetable"].update_one(
                    filter={"_id": id}, update={"$set": {"is_deleted": True}})
                return JsonResponse(data={"message": "Successfully Deleted"}, status=status.HTTP_200_OK)
            except:
                return JsonResponse(data={"message": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if data:
            for field in data.keys():
                if field not in all_fields:
                    return JsonResponse(data={"message": "Wrong Data Provided"}, status=status.HTTP_400_BAD_REQUEST)

            if request.method == "POST":
                # required for all fields
                for field in all_fields:
                    if field not in data:
                        return JsonResponse(data={"message": "Wrong Data Provided"}, status=status.HTTP_400_BAD_REQUEST)

                timetable_data = {
                    "_id": create_unique_object_id(),
                    "subject_id": data["subject_id"],
                    "faculty_id": data["faculty_id"],
                    "semester_id": data["semester_id"],
                    "division": data["division"],
                    "remarks": data["remarks"],
                    "room_number": data["room_number"],
                    "start_time": data["start_time"],
                    "end_time": data["end_time"]
                }

                try:
                    database["timetable"].insert_one(timetable_data)
                    return JsonResponse(data={"message": "Timetable Successfully Created"}, status=status.HTTP_201_CREATED)
                except:
                    return JsonResponse(data={"message": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            elif request.method == "PATCH":

                try:
                    database["timetable"].find_one_and_update(
                        filter={"_id": id}, update={"$set": data})
                    return JsonResponse(data={"message": "Timetable Successfully Updated"}, status=status.HTTP_201_CREATED)
                except:
                    return JsonResponse(data={"message": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return JsonResponse(data={"message": "No Data Provided"}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return JsonResponse(data={"message": "User Not Authorized"}, status=status.HTTP_401_UNAUTHORIZED)


def get_attendance(request, id=None):
    user = database[auth_collection].find_one(
        filter={"_id": request.id, "role": request.role})
    if user["role"] == "Faculty" and user["_id"] == request.id:
        pipeline = [
            {
                "$lookup": {
                    'from': 'Student',
                    'localField': 'student_id',
                    'foreignField': '_id',
                    'as': 'student_details'
                }
            },
            {"$unwind": "$student_details"},
            {
                "$lookup": {
                    'from': 'User',
                    'localField': 'student_details.User_ID',
                    'foreignField': '_id',
                    'as': 'user'
                }
            },
            {"$unwind": "$user"},
            {
                "$project": {
                    "_id": 1,
                    "roll_number": 1,
                    "attendance": 1,
                    "student_details.gr_number": 1,
                    "student_details.roll_number": 1,
                    "user.first_name": 1,
                    "user.last_name": 1
                }
            },
            {
                "$match": {
                    "attendance": {
                        "$eq": False
                    }
                }
            },
            {
                "$sort": {
                    "roll_number": 1
                }
            }
        ]

        attendance_details = database["attendance"].aggregate(pipeline)
        attendance_details = list(attendance_details)
        return JsonResponse(data=attendance_details, status=status.HTTP_200_OK, safe=False)
    elif user["role"] == "Student":
        attendance_details = database["attendance"].find(
            filter={"student_id": id})
        attendance_details = [i for i in attendance_details]
        return JsonResponse(data=attendance_details, status=status.HTTP_200_OK, safe=False)
    else:
        return JsonResponse(data={"message": "User Not Authorized"}, status=status.HTTP_400_BAD_REQUEST)


def correct_attendance(request, id):
    user = database[auth_collection].find_one(
        filter={"_id": request.id, "role": request.role})
    if user["role"] == "Faculty" and user["_id"] == request.id:
        if id:
            database["attendance"].update_one(
                filter={"_id": id, "attendance": False}, update={"$set": {"attendance": True}})
            return JsonResponse(data={"message": "Attendance Updated Successfully"}, status=status.HTTP_200_OK)
        else:
            return JsonResponse(data={"message": "ID not provided"}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return JsonResponse(data={"message": "User Not Authorized"}, status=status.HTTP_401_UNAUTHORIZED)


def required_timetable_details(request):
    user = database[auth_collection].find_one(
        filter={"_id": request.id, "role": request.role})

    if user["role"] == "college-admin" and user["_id"] == request.id:
        semester_details = list(database["semester"].find())
        faculty_details = list(database["User"].find({"role": "Faculty"}, {
                               "_id": 1, "first_name": 1, "last_name": 1}))
        subject_details = list(database["subject"].find(
            {}, {"_id": 1, "subject_name": 1, "subject_type": 1}))
        division_details = list(database["division"].find())
        data = {
            "semester_details": semester_details,
            "faculty_details": faculty_details,
            "subject_details": subject_details,
            "division_details": division_details
        }
        return JsonResponse(data=data, status=status.HTTP_200_OK)
    else:
        return JsonResponse(data={"message": "User not Authorized"}, status=status.HTTP_401_UNAUTHORIZED)
