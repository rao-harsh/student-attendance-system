import uuid
import jwt
from passlib.context import CryptContext
from .db import jwt_secret, auth_collection
from .db import database
from rest.settings import FIREBASECONFIG, MAIL_SERVICE_CONFIGS
from django.core.files.storage import default_storage
import pyrebase
import smtplib
from email.mime.text import MIMEText

def create_unique_object_id():
    unique_object_id = "ID-{uuid}".format(uuid=uuid.uuid4())
    return unique_object_id

pwd_context = CryptContext(
    default="django_pbkdf2_sha256",
    schemes=["django_argon2", "django_bcrypt", "django_bcrypt_sha256",
             "django_pbkdf2_sha256", "django_pbkdf2_sha1",
             "django_disabled"])

# Check if user if already logged in
def login_status(request):
    token = request.META.get('HTTP_AUTHORIZATION',b"").replace("Bearer ","")
    data = jwt.decode(token, jwt_secret, algorithms=['HS256'])
    user_obj = None
    flag = False
    user_filter = database[auth_collection].find({"_id": data["id"]["id"]}, {"_id": 0, "password": 0})
    if user_filter.count():
        flag = True
        user_obj = list(user_filter)[0]
    return flag, user_obj

#for formatting output in json response
def output_format(status=200, message='', data={}):
    response = {"status" : status, "message":message, "data" : data}
    return response

# for sending mails
def send_email(subject, body, recipients):
    print(body)
    msg = MIMEText(body, _subtype='html')
    print(msg)
    msg['Subject'] = subject
    msg['From'] = MAIL_SERVICE_CONFIGS['sender']
    msg['To'] = ', '.join(recipients)
    smtp_server = smtplib.SMTP_SSL(MAIL_SERVICE_CONFIGS['smtp_server'], MAIL_SERVICE_CONFIGS['smtp_port'])
    smtp_server.login(MAIL_SERVICE_CONFIGS['sender'], MAIL_SERVICE_CONFIGS['password'])
    smtp_server.sendmail(MAIL_SERVICE_CONFIGS['sender'], recipients, msg.as_string())
    smtp_server.quit()

def firebase_image_upload(request, id):
    
    #setting up firebase connection
    firebase = pyrebase.initialize_app(FIREBASECONFIG)
    storage = firebase.storage()
    for i in request.FILES.values():
        pass

