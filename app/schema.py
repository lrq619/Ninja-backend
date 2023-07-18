from drf_spectacular.utils import inline_serializer
from rest_framework import serializers

plain_text_schema = inline_serializer(
                name="Plain text message schema",
                fields={
                    "message": serializers.CharField(),
                }
)

int_code_schema = inline_serializer(
    name="Int code schema",
    fields={
        "code":serializers.IntegerField(),
    }
)

user_name_schema = inline_serializer(
    name="User name schema",
    fields={
                "username": serializers.CharField(),
            }
)

username_roomid_schema = inline_serializer(
    name="Username roomid schema",
    fields={
                "username": serializers.CharField(),
                "room_id": serializers.IntegerField()
    }
)