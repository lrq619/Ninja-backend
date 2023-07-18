from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.db import connection
from django.views.decorators.csrf import csrf_exempt

from rest_framework.decorators import api_view
from rest_framework import serializers
from drf_spectacular.utils import extend_schema, inline_serializer

from .schema import plain_text_schema, user_name_schema, username_roomid_schema, int_code_schema
from app.models import Gesture, NinjaUser
import sys
# from .room import Room
# sys.path.append("..") 
# from config import WS_PORT
# from app import GAME_HALL


# Create your views here.
# GAME_HALL : Hall = Hall()
 

@extend_schema(
        request=user_name_schema,
        responses={
            200 : inline_serializer(
            name="getLatestGesture-Rsp-200",
            fields={
                "gesture_type": serializers.CharField(),
            }),
            400: plain_text_schema
            },
        description="Obtain latest gesture of a user",
)
@api_view(['POST'])
@csrf_exempt
def getLatestsGesture(request):
    if request.method != 'POST':
        return HttpResponse(status=404)
    response = {}
    try:
        username = request.data['username']
        gesture_type = Gesture.objects.filter(username=username).order_by("-timestamp")[0].gesture_type
        response['gestures_type'] = gesture_type
        return JsonResponse(response, status=200)
    except:
        response['message'] = 'Fail to get latest gesture!'
        return JsonResponse(response, status=400)
    


@extend_schema(
        request=inline_serializer(
            name="postgestures-Req",
            fields={
                "username": serializers.CharField(),
                "gesturetype": serializers.CharField()
            }
        ),
        responses={
            200 : plain_text_schema,
            400: plain_text_schema},
        description="Post a gesture to the user specified by username",
)
@api_view(['POST'])  
@csrf_exempt
def postgestures(request):
    if request.method != 'POST':
        return HttpResponse(status=404)
    response = {}
    try:
        username = request.data['username']
        gesturetype = request.data['gesturetype']   
        gesture = Gesture(username=username, gesture_type=gesturetype)
        gesture.save()
        response["message"] = "Gesture add success"
        return JsonResponse(response, status=200)  
    except:
        response["message"] = "post gesture failed!"
        return JsonResponse(response, status=400)


@extend_schema(
        request=user_name_schema,
        responses={200 : plain_text_schema, 400: plain_text_schema},
        description="Check if the user specified by username exist in db",
)
@api_view(['POST']) 
@csrf_exempt
def checkUserValid(request):
    if request.method != 'POST':
        return HttpResponse(status=404)
    username = request.data['username']
    
    users = NinjaUser.objects.filter(username=username)
    response = {}
    if len(users) == 1:  
        # 如果 users 表中存在 username 字段，返回 HTTP 200 OK
        response['message'] = 'Username found.'
        return JsonResponse(response, status=200)  
    elif len(users) > 1:  
        # 如果 users 表中不存在 username 字段，返回 HTTP 400 Bad Request
        response['message'] =  'Has multiple users with username=%s.'%username
        return JsonResponse(response, status=400)
    else:
        response['message'] = 'Not have such user with username=%s.'%username
        return JsonResponse(response, status=400)
    

@extend_schema(
        request=user_name_schema,
        responses={200 : int_code_schema, 400: int_code_schema},
        description="Check the user status, 0 for offline, 1 for online, 2 for inplay, -1 for user not exist",
)
@api_view(['POST']) 
@csrf_exempt
def checkUserStatus(request):
    username = request.data['username']
    try:
        ninja_user = NinjaUser.objects.get(username=username)
        status_code = 0 if ninja_user.status == 'offline' else 1 if ninja_user.status == 'online' else 2
        response = {'status': status_code}
    except NinjaUser.DoesNotExist:
        response = {'status': -1}  # Return -1 if the user doesn't exist
        return JsonResponse(response,status=400)

    return JsonResponse(response,status=200)


@extend_schema(
        request=user_name_schema,
        responses={200 : plain_text_schema, 400 : plain_text_schema},
        description="Log in the user only if it's offline and username exists in db"
)
@api_view(['POST']) 
@csrf_exempt
def loginUser(request):
    if request.method != 'POST':
        return HttpResponse(status=404)
    username = request.data['username']
    response = {}
    try:
        user = NinjaUser.objects.get(username=username)
        if user.status != 'offline':
            response['message'] = "User is currently logged in!"
            return JsonResponse(response,status=400)
        user.status = 'online'
        user.save()
        response['message'] = "User %s successfully logged in!"%username
        return JsonResponse(response,status=200)
        
    except:
        response['message'] = "User doesn't exist in db!"
        return JsonResponse(response,status=400)

@extend_schema(
        request=user_name_schema,
        responses={200 : plain_text_schema, 400 : plain_text_schema},
        description="Log out the user only if it's not offline and username exists in db"
)
@api_view(['POST']) 
@csrf_exempt
def logoutUser(request):
    if request.method != 'POST':
        return HttpResponse(status=404)
    username = request.data['username']
    response = {}
    try:
        user = NinjaUser.objects.get(username=username)
        if user.status == 'offline':
            response['message'] = "User is currently not logged in!"
            return JsonResponse(response,status=400)
        user.status = 'offline'
        user.save()
        response['message'] = "User %s successfully logged out!"%username
        return JsonResponse(response,status=200)
    except:
        response['message'] = "User doesn't exist in db!"
        return JsonResponse(response,status=400)

    



@extend_schema(
        request=user_name_schema,
        responses={200: plain_text_schema,400: plain_text_schema},
        description="Add a user to db",
)
@api_view(['POST']) 
@csrf_exempt
def postUser(request):  
   if request.method != 'POST':  
       return HttpResponse('Invalid request method. This view expects a POST request.', status=400)
   # 查询 users 表中的 username 字段是否存在  
   username = request.data['username']
   users = NinjaUser.objects.filter(username=username)
   response = {}
   if len(users) != 0:
       response["message"] = 'Username already exists.'
       return JsonResponse(response, status=400)
   else:
       user = NinjaUser(username=username, status='online')
       user.save()
       response['message'] = 'Username added successfully.'
       return JsonResponse(response, status=200)
   
@extend_schema(
        request=user_name_schema,
        responses={
            200 : inline_serializer(
            name="createRoom-Rsp-200",
            fields={
                'room_id': serializers.IntegerField(),
                'port': serializers.IntegerField()
            }),
            400: plain_text_schema
            },
        description="Create a room, return the room_id just created and the port number for ws server",
)
@api_view(['POST']) 
@csrf_exempt
def createRoom(request):
    if request.method != 'POST':  
       return HttpResponse('Invalid request method. This view expects a POST request.', status=400)
    response = {}
    try:
        username = request.data['username']
        global GAME_HALL
        room_id = GAME_HALL.create_room(username)
        
        
        return JsonResponse({
            'room_id': room_id,
            'port': 8765
        }, status=200)
    except:
        response['message'] = "create room failed!"
        return JsonResponse(response, status=400)        

@extend_schema(
        request=username_roomid_schema,
        responses={
            200 : plain_text_schema,
            400: plain_text_schema
            },
        description="Join a room",
)
@api_view(['POST']) 
@csrf_exempt
def joinRoom(request):
    if request.method != 'POST':  
       return HttpResponse('Invalid request method. This view expects a POST request.', status=400)
    username = request.data['username']
    room_id = request.data['room_id']
    response = {}
    room = GAME_HALL.join_room(room_id, username)
    if room != None:
        response['message'] = 'Join Room: %d success!'%room_id
        return JsonResponse(response, status=200)
    else:
        response['message'] = 'Join Room: %d failed!'%room_id
        return JsonResponse(response, status=400)
    

    



@extend_schema(
        request=user_name_schema,
        responses={
            200 : plain_text_schema,
            400: plain_text_schema
            },
        description="Join a room",
)
@api_view(['POST']) 
@csrf_exempt
def quitRoom(request):
    if request.method != 'POST':  
       return HttpResponse('Invalid request method. This view expects a POST request.', status=400)
    username = request.data['username']
    response = {}
    if GAME_HALL.quit_room(username):
        response['message'] = "user: %s quit room success"%username
        return JsonResponse(response,status=200)
    else:
        response['message'] = "user: %s quit room failed"%username
        return JsonResponse(response,status=400)
    

@extend_schema(
        request=username_roomid_schema,
        responses={
            200 : int_code_schema,
            400: plain_text_schema
            },
        description="Join a room",
)
@api_view(['POST']) 
@csrf_exempt
def checkRoomNum(request):
    if request.method != 'POST':  
       return HttpResponse('Invalid request method. This view expects a POST request.', status=400)
    username = request.data['username']
    room_id = request.data['room_id']
    num = GAME_HALL.check_room_num(room_id)
    response = {}
    if num == -1:
        response['message'] = "room_id %d doesn't exist" %room_id
        return JsonResponse(response,status=400)
    response['code'] = num
    return JsonResponse(response, status=200)

    
   

   
    