from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, CartViewSet, CategoryViewSet, signup, login

router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'categories', CategoryViewSet)

urlpatterns = [
    path('users/signup', signup),
    path('users/login', login),
    path('', include(router.urls)),
]
