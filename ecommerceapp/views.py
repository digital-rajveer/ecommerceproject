from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

from .forms import SignUpForm, CustomAuthenticationForm
from .models import Cart, CartItem, Category, Order, OrderItem, Product, BillingAddress


def get_user_cart(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    return cart


def get_cart_items(request):
    cart = get_user_cart(request)
    items = [
        {
            'product': item.product,
            'quantity': item.quantity,
            'subtotal': item.subtotal,
            'cart_item': item,
        }
        for item in cart.items.select_related('product')
    ]
    return items, cart.total


def product_list(request):
    categories = Category.objects.filter(products__available=True).distinct().order_by('name')
    category_panels = []
    for category in categories:
        products = category.products.filter(available=True).order_by('name')[:4]
        if products:
            category_panels.append({'category': category, 'products': products})

    featured_products = Product.objects.filter(available=True).order_by('-created')[:8]
    return render(
        request,
        'ecommerceapp/product_list.html',
        {
            'category_panels': category_panels,
            'featured_products': featured_products,
        },
    )


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    related_products = Product.objects.filter(
        category=product.category,
        available=True,
    ).exclude(pk=product.pk)[:4]
    return render(
        request,
        'ecommerceapp/product_detail.html',
        {'product': product, 'related_products': related_products},
    )


@login_required
def cart_detail(request):
    cart_items, total = get_cart_items(request)
    return render(request, 'ecommerceapp/cart.html', {'cart_items': cart_items, 'total': total})


@login_required
def cart_add(request, product_id):
    cart = get_user_cart(request)
    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product_id=product_id,
        defaults={'quantity': 1},
    )
    if not created:
        item.quantity += 1
        item.save()
    return redirect('ecommerceapp:cart_detail')


@login_required
def cart_update(request, product_id):
    cart = get_user_cart(request)
    quantity = request.POST.get('quantity') or request.POST.get('manual_quantity')
    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        quantity = 1

    item = get_object_or_404(CartItem, cart=cart, product_id=product_id)
    if quantity <= 0:
        item.delete()
        item_subtotal = 0
    else:
        item.quantity = quantity
        item.save()
        item_subtotal = float(item.subtotal)

    total = float(cart.total)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'product_id': product_id,
            'quantity': max(quantity, 0),
            'item_subtotal': f"{item_subtotal:.2f}",
            'total': f"{total:.2f}",
        })

    return redirect('ecommerceapp:cart_detail')


@login_required
def cart_remove(request, product_id):
    cart = get_user_cart(request)
    CartItem.objects.filter(cart=cart, product_id=product_id).delete()
    return redirect('ecommerceapp:cart_detail')


@login_required
def checkout(request):
    cart_items, total = get_cart_items(request)
    if not cart_items:
        return redirect('ecommerceapp:cart_detail')

    if request.method == 'POST':
        billing_address = BillingAddress.objects.create(
            user=request.user,
            name=request.POST.get('full_name'),
            address_line_1=request.POST.get('address'),
            city=request.POST.get('city'),
            state=request.POST.get('state'),
            zipcode=request.POST.get('postal_code'),
            country=request.POST.get('country'),
            phone=request.POST.get('phone'),
            email=request.POST.get('email'),
        )
        order = Order.objects.create(
            user=request.user,
            billing_address=billing_address,
            total_amount=total,
            paid=True,
        )
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                price=item['product'].price,
                quantity=item['quantity'],
            )
        cart = get_user_cart(request)
        cart.items.all().delete()
        return render(request, 'ecommerceapp/order_success.html', {'order': order})

    return render(request, 'ecommerceapp/checkout.html', {'cart_items': cart_items, 'total': total})


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product').select_related('billing_address')
    return render(request, 'ecommerceapp/order_history.html', {'orders': orders})


@login_required
def order_invoice(request, order_id):
    order = get_object_or_404(Order.objects.select_related('billing_address').prefetch_related('items__product'), id=order_id, user=request.user)
    return render(request, 'ecommerceapp/order_invoice.html', {'order': order})


@login_required
def order_invoice_pdf(request, order_id):
    order = get_object_or_404(Order.objects.select_related('billing_address').prefetch_related('items__product'), id=order_id, user=request.user)
    
    # Create a file-like buffer to receive PDF data.
    buffer = BytesIO()

    # Create the PDF object, using the buffer as its "file."
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph(f"Invoice for Order #{order.id}", styles['Title']))
    story.append(Spacer(1, 12))

    # Order details
    story.append(Paragraph(f"Date: {order.created.strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    story.append(Paragraph(f"Customer: {order.user.username}", styles['Normal']))
    story.append(Spacer(1, 12))

    # Billing address
    if order.billing_address:
        story.append(Paragraph("Billing Address:", styles['Heading2']))
        story.append(Paragraph(order.billing_address.name, styles['Normal']))
        story.append(Paragraph(order.billing_address.address_line_1, styles['Normal']))
        if order.billing_address.address_line_2:
            story.append(Paragraph(order.billing_address.address_line_2, styles['Normal']))
        story.append(Paragraph(f"{order.billing_address.city}, {order.billing_address.state} {order.billing_address.zipcode}", styles['Normal']))
        story.append(Paragraph(order.billing_address.country, styles['Normal']))
        if order.billing_address.phone:
            story.append(Paragraph(f"Phone: {order.billing_address.phone}", styles['Normal']))
        if order.billing_address.email:
            story.append(Paragraph(f"Email: {order.billing_address.email}", styles['Normal']))
        story.append(Spacer(1, 12))

    # Items table
    data = [['Product', 'Quantity', 'Price', 'Subtotal']]
    for item in order.items.all():
        data.append([
            item.product.name if item.product else 'Removed item',
            str(item.quantity),
            f"Rs {item.price}",
            f"Rs {item.subtotal}"
        ])
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(table)
    story.append(Spacer(1, 12))

    # Total
    story.append(Paragraph(f"Total: Rs {order.total_amount}", styles['Heading1']))

    doc.build(story)

    # FileResponse sets the Content-Disposition header so that browsers
    # present the option to save the file.
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.pdf"'
    return response


def about(request):
    return render(request, 'ecommerceapp/about.html')


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('ecommerceapp:product_list')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    authentication_form = CustomAuthenticationForm


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('ecommerceapp:product_list')
    http_method_names = ['get', 'post', 'options']
    
    def get(self, request, *args, **kwargs):
        # Handle logout on GET request
        return super().post(request, *args, **kwargs)
