from django.urls import path
from . import views
# url config
urlpatterns = [
    path('api/hello', views.say_hello, name='hello'),
]