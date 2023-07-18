from django.db import models
# from .room import Hall

USERNAME_LEN = 255
GESTURE_TYPE_LEN = 255
# Create your models here.
class Gesture(models.Model):
    username = models.CharField(max_length=USERNAME_LEN)
    gesture_type = models.CharField(max_length=GESTURE_TYPE_LEN)
    timestamp = models.DateTimeField(auto_now_add=True)

class NinjaUser(models.Model):
    STATUS_CHOICES = (
        ('offline', 'Offline'),
        ('online', 'Online'),
        ('inplay', 'In Play'),
    )

    username = models.CharField(max_length=USERNAME_LEN)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    def __str__(self):
        return self.username

class Room(models.Model):
    room_id = models.IntegerField()
    owner = models.CharField(max_length=USERNAME_LEN)
    guest = models.CharField(max_length=USERNAME_LEN)

ROOM_LIST : list[Room]= []
ROOM_ID:int = 0


