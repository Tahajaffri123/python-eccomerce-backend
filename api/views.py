from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Product, CartItem, Category
from .serializers import UserSerializer, ProductSerializer, CartItemSerializer, CategorySerializer

# Custom Permission for Admin Only Write Operations
class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

# Auth Views
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def signup(request):
    email = request.data.get('email')
    password = request.data.get('password')
    name = request.data.get('name', '')
    role = request.data.get('role', 'user') # 'user' or 'admin'

    if not email or not password:
        return Response({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=email).exists():
        return Response({'error': 'User already exists'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=email, email=email, password=password)
    user.first_name = name
    
    # Set admin role if requested
    if role == 'admin':
        user.is_staff = True
        
    user.save()
    
    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        'token': token.key,
        'user': {
            'id': user.id,
            'name': user.first_name,
            'email': user.email,
            'role': 'admin' if user.is_staff else 'user'
        }
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login(request):
    email = request.data.get('email')
    password = request.data.get('password')

    user = authenticate(username=email, password=password)
    if not user:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        'token': token.key,
        'user': {
            'id': user.id,
            'name': user.first_name,
            'email': user.email,
            'role': 'admin' if user.is_staff else 'user'
        }
    })

# Category ViewSet
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]

# Product ViewSet
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]

# Cart ViewSet
class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.AllowAny] 

    def list(self, request, *args, **kwargs):
        user_id = request.query_params.get('userId')
        if not user_id:
            return Response({'error': 'userId is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        total_price = sum(item.product.price * item.quantity for item in queryset)
        
        return Response({
            'items': serializer.data,
            'total_price': float(total_price)
        })

    def get_queryset(self):
        # For list view, filter by userId
        if self.action == 'list':
            user_id = self.request.query_params.get('userId')
            if user_id:
                return CartItem.objects.filter(user_id=user_id)
            return CartItem.objects.none()
        # For detail views (retrieve, update, delete), allow access to all to find by ID
        return CartItem.objects.all()

    def create(self, request, *args, **kwargs):
        user_id = request.data.get('userId')
        product_id = request.data.get('productId')
        quantity = int(request.data.get('quantity', 1))

        try:
            user = User.objects.get(id=user_id)
            if user.is_staff:
                return Response({'error': 'Admins cannot add items to cart'}, status=status.HTTP_403_FORBIDDEN)
            product = Product.objects.get(id=product_id)
        except (User.DoesNotExist, Product.DoesNotExist):
            return Response({'error': 'User or Product not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check stock before creating/updating
        cart_item = CartItem.objects.filter(user=user, product=product).first()
        current_quantity = cart_item.quantity if cart_item else 0
        new_total_quantity = current_quantity + quantity

        if new_total_quantity > product.available_quantity:
            return Response({
                'error': f'Only {product.available_quantity} items are available. Please wait for the owner to add more quantity in his warehouse.'
            }, status=status.HTTP_400_BAD_REQUEST)

        if cart_item:
            cart_item.quantity = new_total_quantity
            cart_item.save()
        else:
            cart_item = CartItem.objects.create(user=user, product=product, quantity=quantity)

        serializer = self.get_serializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        new_quantity = int(request.data.get('quantity', instance.quantity))
        
        if new_quantity > instance.product.available_quantity:
            return Response({
                'error': f'Only {instance.product.available_quantity} items are available. Please wait for the owner to add more quantity in his warehouse.'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        return super().partial_update(request, *args, **kwargs)
