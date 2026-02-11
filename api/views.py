from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view

# Create your views here.
def say_hello(request):
    return JsonResponse({"message": "Hello world from Django 🚀"})
    # return JsonResponse({
    #     "name":"hello"
    # })
