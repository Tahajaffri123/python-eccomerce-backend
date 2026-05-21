from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

    def validate_age(self, value):
        if value < 0:
            raise serializers.ValidationError("Age cannot be negative")
        return value