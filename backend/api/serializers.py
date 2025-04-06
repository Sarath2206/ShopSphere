from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, SearchQuery, ClothingItem, SearchHistory

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'phone')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'created_at']
        read_only_fields = ['id', 'created_at']

class ClothingItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClothingItem
        fields = ['id', 'title', 'price', 'image_url', 'product_url', 'source_website', 'created_at']
        read_only_fields = ['id', 'created_at']

class SearchQuerySerializer(serializers.ModelSerializer):
    items = ClothingItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = SearchQuery
        fields = ['id', 'query', 'filters', 'created_at', 'status', 'items']
        read_only_fields = ['id', 'status', 'created_at']

class SearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchHistory
        fields = ['id', 'query', 'created_at']
        read_only_fields = ['id', 'created_at'] 