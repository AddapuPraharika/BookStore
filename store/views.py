from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from django.contrib import messages
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from .models import Book, Review, Wishlist, Order, OrderItem
from django.db.models import Avg
from django.http import HttpResponseForbidden

from collections import defaultdict

def home(request):
    return render(request, 'store/home.html')

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'store/login.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}. You are now logged in.')
            # Automatically log in the user after registration
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'store/register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('logout_page')

def logout_page(request):
    return render(request, 'store/logout.html')

def dashboard(request):
    query = request.GET.get('q', '')
    genre_filter = request.GET.get('genre', '')
    books = Book.objects.all()
    if query:
        books = books.filter(title__icontains=query)
    if genre_filter:
        books = books.filter(genre__iexact=genre_filter)
    not_found = not books.exists()
    genres = Book.objects.values_list('genre', flat=True).distinct()

    # Group books by genre
    books_by_genre = defaultdict(list)
    for book in books:
        genre = book.genre if book.genre else 'Other'
        books_by_genre[genre].append(book)

    return render(request, 'store/dashboard.html', {
        'books_by_genre': dict(books_by_genre),
        'query': query,
        'not_found': not_found,
        'genres': genres,
        'selected_genre': genre_filter
    })


def book_detail(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    reviews = book.reviews.all()
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    return render(request, 'store/book_detail.html', {'book': book, 'reviews': reviews, 'average_rating': average_rating})

@login_required
def add_review(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if request.method == 'POST':
        rating = int(request.POST.get('rating', 1))
        comment = request.POST.get('comment', '')
        Review.objects.create(book=book, user=request.user, rating=rating, comment=comment)
        messages.success(request, 'Your review has been added.')
        return redirect('book_detail', book_id=book.id)
    else:
        return HttpResponseForbidden()

@login_required
def wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('book')
    return render(request, 'store/wishlist.html', {'wishlist_items': wishlist_items})

@login_required
def add_to_wishlist(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    Wishlist.objects.get_or_create(user=request.user, book=book)
    messages.success(request, f'"{book.title}" added to your wishlist.')
    return redirect('wishlist')

@login_required
def remove_from_wishlist(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    Wishlist.objects.filter(user=request.user, book=book).delete()
    messages.success(request, f'"{book.title}" removed from your wishlist.')
    return redirect('wishlist')

@login_required
def profile(request):
    # For simplicity, just render a profile page with user info and order history
    orders = Order.objects.filter(user=request.user).prefetch_related('items__book')
    return render(request, 'store/profile.html', {'orders': orders})

@login_required
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, 'Your cart is empty.')
        return redirect('dashboard')
    books = Book.objects.filter(id__in=cart.keys())
    if request.method == 'POST':
        order = Order.objects.create(user=request.user)
        for book in books:
            quantity = cart.get(str(book.id), 0)
            if quantity > 0:
                OrderItem.objects.create(order=order, book=book, quantity=quantity)
        request.session['cart'] = {}
        messages.success(request, 'Order placed successfully.')
        return redirect('order_confirmation', order_id=order.id)
    books_with_quantity = []
    total_amount = 0
    for book in books:
        quantity = cart.get(str(book.id), 0)
        total_amount += book.price * quantity
        books_with_quantity.append({'book': book, 'quantity': quantity})
    return render(request, 'store/checkout.html', {'books_with_quantity': books_with_quantity, 'total_amount': total_amount})

@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/order_confirmation.html', {'order': order})

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items__book')
    return render(request, 'store/order_history.html', {'orders': orders})

from django.contrib import messages

from django.contrib import messages

from django.contrib import messages

def add_to_cart(request, book_id):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        if isinstance(cart, list):
            # Convert list to dict with quantity 1 for each book_id
            new_cart = {}
            for id in cart:
                new_cart[str(id)] = 1
            cart = new_cart
        book_id_str = str(book_id)
        if book_id_str in cart:
            cart[book_id_str] += 1
        else:
            cart[book_id_str] = 1
        request.session['cart'] = cart
        messages.success(request, 'Book added to cart successfully.')
        return redirect('dashboard')
    return redirect('dashboard')

def remove_from_cart(request, book_id):
    cart = request.session.get('cart', {})
    book_id_str = str(book_id)
    if book_id_str in cart:
        if cart[book_id_str] > 1:
            cart[book_id_str] -= 1
        else:
            del cart[book_id_str]
        request.session['cart'] = cart
    return redirect('cart')

def cart(request):
    cart = request.session.get('cart', {})
    book_ids = cart.keys()
    books = Book.objects.filter(id__in=book_ids)
    total_amount = 0
    books_with_quantity = []
    for book in books:
        quantity = cart.get(str(book.id), 0)
        total_amount += book.price * quantity
        books_with_quantity.append({'book': book, 'quantity': quantity})
    return render(request, 'store/cart.html', {
        'books_with_quantity': books_with_quantity,
        'total_amount': total_amount,
    })

def home(request):
    return render(request, 'store/home.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}. You can now log in.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'store/register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('logout_page')

def logout_page(request):
    return render(request, 'store/logout.html')

from collections import defaultdict

def dashboard(request):
    query = request.GET.get('q', '')
    genre_filter = request.GET.get('genre', '')
    books = Book.objects.all()
    if query:
        books = books.filter(title__icontains=query)
    if genre_filter:
        books = books.filter(genre__iexact=genre_filter)
    not_found = not books.exists()
    genres = Book.objects.values_list('genre', flat=True).distinct()

    # Group books by genre
    books_by_genre = defaultdict(list)
    for book in books:
        genre = book.genre if book.genre else 'Other'
        books_by_genre[genre].append(book)

    return render(request, 'store/dashboard.html', {
        'books_by_genre': dict(books_by_genre),
        'query': query,
        'not_found': not_found,
        'genres': genres,
        'selected_genre': genre_filter
    })

