from django.contrib import admin
from .models import Book, Review, Wishlist, Order, OrderItem

class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'genre', 'price', 'stock')
    search_fields = ('title', 'author', 'genre')
    list_filter = ('genre',)
    fields = ('title', 'author', 'description', 'price', 'cover_image', 'genre', 'stock')

admin.site.register(Book, BookAdmin)
admin.site.register(Review)
admin.site.register(Wishlist)
admin.site.register(Order)
admin.site.register(OrderItem)
