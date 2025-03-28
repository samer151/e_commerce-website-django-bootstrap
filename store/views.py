from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import LoginView
from .models import Product, Cart, UserProfile, CartItem
import stripe
from django.db.models import Q  

from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.contrib import messages
# Set up Stripe API key (consider moving this to settings.py)
stripe.api_key = 'sk_test_51R5ooGGEljye7790a3v7NP6RaGrjq5solIavCYojHh1MB6zkVZHBKKTxGRWhqEMI2aUi6XhFM0MU56RJKJVgoW5e00luC3qgwR'
from .forms import CustomLoginForm,CustomUserCreationForm  # type: ignore

def home(request):
    products = Product.objects.all()  # Or filter(featured=True) if you want featured items
    return render(request, 'store/home.html', {'products': products})  # Add context
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')  # Redirect authenticated users away from login page

    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')  # Redirect to home after login
    else:
        form = CustomLoginForm()
    
    return render(request, 'store/login.html', {'form': form})
# Register view
def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)  
        if form.is_valid():
            # Save the user
            form.save()
            # Log the user in automatically
            username = form.cleaned_data.get('username')
            user = authenticate(username=username, password=form.cleaned_data.get('password1'))
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()  # Changed from UserCreationForm to CustomUserCreationForm

    return render(request, 'store/register.html', {'form': form})

# Custom login view
class CustomLoginView(LoginView):
    template_name = 'store/login.html'

def product_list(request):
    search_query = request.GET.get('q', '')
    
    # Base queryset
    products = Product.objects.all()
    
    # Filter by name or description if search query exists
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |  # Search product names
            Q(description__icontains=search_query)  # Search descriptions
        )
    
    return render(request, 'store/product_list.html', {
        'products': products,
        'search_query': search_query
    })

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'store/product_detail.html', {'product': product})

def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        return redirect('login')
    
    product = get_object_or_404(Product, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product
    )
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    messages.success(request, f"Added {product.name} to cart")
    return redirect('product_list')

def view_cart(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all()
        total = sum(item.product.price * item.quantity for item in cart_items)
    except Cart.DoesNotExist:
        cart_items = []
        total = 0
    
    return render(request, 'store/cart.html', {
        'cart_items': cart_items,
        'total': total
    })

def remove_from_cart(request, item_id):
    if request.method == 'POST':
        # Get the cart item and verify it belongs to the current user
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        cart_item.delete()
        messages.success(request, "Item removed from cart")
    return redirect('view_cart')
def checkout(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all()  # Get CartItem objects
        total = sum(item.product.price * item.quantity for item in cart_items)
    except Cart.DoesNotExist:
        cart_items = []
        total = 0

    if request.method == 'POST':
        try:
            # Create a PaymentIntent
            intent = stripe.PaymentIntent.create(
                amount=int(total * 100),  # Convert to cents
                currency='usd',
                payment_method_types=['card'],
            )

            # Clear the cart after successful payment
            cart.items.all().delete()
            messages.success(request, "Your payment was successful!")
            return redirect('thank_you')
            
        except stripe.error.StripeError as e:
            messages.error(request, f"Payment error: {e.user_message}")
            return redirect('checkout')

    return render(request, 'store/checkout.html', {
        'total': total,
        'STRIPE_PUBLIC_KEY': 'your_stripe_public_key_here'  # Add your actual key
    })

def thank_you(request):
    return render(request, 'store/thank_you.html')
