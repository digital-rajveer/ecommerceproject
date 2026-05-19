from django.urls import path

from . import views

app_name = 'ecommerceapp'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('about/', views.about, name='about'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/update/<int:product_id>/', views.cart_update, name='cart_update'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.order_history, name='order_history'),

    path('order/<int:order_id>/invoice/', views.order_invoice, name='order_invoice'),
    path('order/<int:order_id>/invoice/pdf/', views.order_invoice_pdf, name='order_invoice_pdf'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
]
