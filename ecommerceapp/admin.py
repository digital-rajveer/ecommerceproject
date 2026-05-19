from django.contrib import admin

from .models import Cart, CartItem, Category, Order, OrderItem, Product, BillingAddress


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created', 'updated')
    inlines = [CartItemInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ('product', 'price', 'quantity')
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'paid', 'created')
    list_filter = ('paid', 'created')
    readonly_fields = ('created', 'updated')
    inlines = [OrderItemInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'available', 'created', 'updated')
    list_filter = ('available', 'created', 'updated', 'category')
    list_editable = ('price', 'available')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')


@admin.register(BillingAddress)
class BillingAddressAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'city', 'state', 'is_default')
    list_filter = ('is_default', 'country')
    search_fields = ('user__username', 'city', 'name')
    readonly_fields = ('user',)
