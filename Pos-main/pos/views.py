# Standard library imports
import datetime
import json
from datetime import timedelta
from django.utils.timezone import now

# Third-party imports
from django.contrib import messages
from django.contrib.auth import logout, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db.models import Sum, F
from django.db.models.functions import TruncDay, TruncMonth, TruncDate
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.csrf import csrf_exempt
from xhtml2pdf import pisa

# Project imports
from . import models
from .forms import ProductForm, CategoryForm, CustomerForm, CustomUserCreationForm,ExpenseForm
from .models import Product, Sale, Customer, Category, SaleItem, UserProfile,Expense
from pos.decorators import role_required
from django.contrib.auth.decorators import login_required

@login_required
@role_required(['admin', 'manager'])
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            return redirect('expense_list')
    else:
        form = ExpenseForm()
    return render(request, 'pos/add_expense.html', {'form': form})

@login_required
@role_required(['admin', 'manager'])
def edit_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            return redirect('expense_list')
    else:
        form = ExpenseForm(instance=expense)
    return render(request, 'pos/edit_expense.html', {'form': form})

@login_required
@role_required(['admin', 'manager'])
def delete_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)
    expense.delete()
    return redirect('expense_list')


@login_required
@role_required(['admin', 'manager'])
def expense_list(request):
    expenses = Expense.objects.filter(user=request.user).order_by('-date')
    total = sum(e.amount for e in expenses)
    total_expenses = Expense.objects.filter(user=request.user).aggregate(total=Sum('amount'))['total'] or 0
    total_amount = Sale.objects.filter(user=request.user).aggregate(total=Sum('total_amount'))['total'] or 0
    total_sales = Sale.objects.filter(user=request.user).aggregate(total=Sum('total_amount'))['total'] or 0
    net_profit = total_amount - total_expenses
    return render(request, 'pos/expense_list.html',{
        'expenses': expenses,
        'total': total,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'total_sales': total_sales
        })

@login_required
@role_required(['admin'])
def admin_users_list(request):
    admin_user_profile = request.user.userprofile 
    users = UserProfile.objects.filter(
        role__in=['inventory', 'cashier', 'manager'],
        user__is_superuser=False,
        created_by=request.user 
    )

    return render(request, 'pos/admin_users_list.html', {'users': users})

@login_required
@role_required(['admin'])
def add_user_view(request, role):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('add_user', role=role)

        user = User.objects.create_user(username=username, password=password)
        user_profile = UserProfile.objects.create(
            user=user, 
            role=role,
            created_by=request.user  # Track which admin created this user
        )

        messages.success(request, f'{role.capitalize()} user added successfully.')
        return redirect('dashboard')

    return render(request, 'pos/add_user_form.html', {'role': role})

@login_required
def get_cart_data(request):
    cart = request.session.get('cart', {})
    cart_data = {}

    for product_id, item in cart.items():
        try:
            product = Product.objects.get(id=product_id, user=request.user)
            cart_data[product_id] = {
                'name': product.name,
                'price': item['price'],
                'quantity': item['quantity']
            }
        except Product.DoesNotExist:
            continue

    return JsonResponse({'cart': cart_data})

def logout_view(request):
    logout(request)
    return redirect('login')


def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user_profile = UserProfile.objects.create(user=user, role='admin') 
            login(request, user)
            return redirect('dashboard')  # Or your home page
    else:
        form = UserCreationForm()
    return render(request, 'pos/signup.html', {'form': form})

@login_required
@role_required(['admin']) 
def products_by_category_id(request, category_id):
    category = get_object_or_404(Category, id=category_id, user=request.user)
    products = Product.objects.filter(category=category, user=request.user)
    categories = Category.objects.filter(user=request.user)  # ✅ Fix here


    return render(request, 'pos/add_product_image_select.html', {
        'products': products,
        'categories': categories,
    })

@login_required
def get_product(request, pk):
    product = Product.objects.get(pk=pk)
    return JsonResponse({
        'name': product.name,
        'price': product.price,
    })

@login_required
@role_required(['admin','cashier','inventory','manager'])
def dashboard(request):
    profile = None
    if request.user.is_authenticated:
        try:
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
        except:
            profile = None

    # Filter data for the logged-in user only
    total_amount = Sale.objects.filter(user=request.user).aggregate(total=Sum('total_amount'))['total'] or 0
    total_customers = Customer.objects.filter(user=request.user).count()
    total_products = Product.objects.filter(user=request.user).count()
    todays_orders = Sale.objects.filter(user=request.user, date__date=now().date()).count()
    recent_sales = Sale.objects.filter(user=request.user).order_by('-date')[:5]
    low_stock = Product.objects.filter(user=request.user, stock__lt=5)

    category_sales = (
        SaleItem.objects.filter(user=request.user)
        .values('product__category__name')
        .annotate(total=Sum('price'))
        .order_by('-total')
    )

    category_sales_data = []

    for row in category_sales:
        category_name = row['product__category__name']
        customers = (
            SaleItem.objects
            .filter(user=request.user, product__category__name=category_name, sale__customer__isnull=False)
            .values_list('sale__customer__name', flat=True)
            .distinct()
        )
    
        row['customers'] = ', '.join(customers) if customers else 'Walk-in Only'
        category_sales_data.append(row)
    return render(request, 'pos/dashboard.html', {
        'profile': profile,
        'total_sales': total_amount,
        'total_customers': total_customers,
        'total_products': total_products,
        'todays_orders': todays_orders,
        'recent_sales': recent_sales,
        'low_stock': low_stock,
        'category_sales_data': category_sales_data,
        
    })

@login_required
@role_required(['admin', 'inventory'])
def product_list(request):
    temp_product_ids = request.session.get('temp_products')

    if temp_product_ids:
        products = Product.objects.filter(id__in=temp_product_ids, user=request.user)
    else:
        products = Product.objects.filter(user=request.user)

    for product in products:
        product.quantity_range = range(1, product.stock + 1)

    return render(request, 'pos/product_list.html', {'products': products})


@login_required
@role_required(['cashier', 'admin'])
def cart_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0
    out_of_stock_items = []

    for product_id, item in cart.items():
        try:
            product = Product.objects.get(id=product_id, user=request.user)

            # Check: If item is a dict, continue. If not, skip it (to avoid error)
            if not isinstance(item, dict):
                continue

            quantity = int(item.get('quantity', 1))
            price = float(item.get('price', product.price))  # fallback to DB price
            subtotal = quantity * price
            total += subtotal

            cart_items.append({
                'id': product.id,
                'name': product.name,
                'price': price,
                'quantity': quantity,
                'subtotal': subtotal,
                'stock_available': product.stock
            })

            if product.stock < quantity:
                out_of_stock_items.append(product)

        except Product.DoesNotExist:
            continue

    return render(request, 'pos/cart.html', {
        'cart_items': cart_items,
        'total': total,
        'out_of_stock_items': out_of_stock_items
    })


@csrf_exempt
@login_required
@role_required(['cashier', 'admin'])
def add_to_cart(request, product_id):
    product = Product.objects.get(id=product_id, user=request.user)
    cart = request.session.get('cart', {})

    product_id_str = str(product_id)

    if product_id_str in cart:
        # 🛠 Make sure the existing item is a dictionary
        if isinstance(cart[product_id_str], dict):
            cart[product_id_str]['quantity'] += 1
        else:
            # Fallback if it's just an integer or wrong format
            cart[product_id_str] = {
                'name': product.name,
                'price': product.price,
                'quantity': 1
            }
    else:
        cart[product_id_str] = {
            'name': product.name,
            'price': product.price,
            'quantity': 1
        }

    request.session['cart'] = cart
    return JsonResponse({'status': 'success', 'message': 'Added to cart'})


@login_required
@role_required(['cashier','admin'])
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect('all_products')

    total_amount = 0
    sale_items = []

    for product_id, item in cart.items():
        try:
            product = Product.objects.get(id=product_id, user=request.user)
            quantity = int(item['quantity'])
            price = float(item['price'])
            total_amount += price * quantity

            sale_items.append({
                'product': product,
                'quantity': quantity,
                'price': price
            })
        except Product.DoesNotExist:
            continue

    # ✅ Get current user's customers
    customers = Customer.objects.filter(user=request.user)

    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        payment_method = request.POST.get('payment_method', 'cash')
        amount_paid = float(request.POST.get('amount_paid', '0'))

        customer = None
        if customer_id:
            try:
                customer = Customer.objects.get(id=customer_id, user=request.user)
            except Customer.DoesNotExist:
                customer = None

        change_due = amount_paid - total_amount  # 💰 Calculate change

        # 🧾 Create sale with extra data
        sale = Sale.objects.create(
            user=request.user,
            customer=customer,
            total_amount=total_amount,
            payment_method=payment_method,
            amount_paid=amount_paid,
            change_due=change_due
        )

        for item in sale_items:
            SaleItem.objects.create(
                sale=sale,
                product=item['product'],
                quantity=item['quantity'],
                price=item['price']
            )

        request.session.pop('cart', None)
        
        messages.success(request, "✅ Sale completed successfully!")
        response = redirect('all_products')

        return response


    return render(request, 'pos/checkout.html', {
        'sale_items': sale_items,
        'total_amount': total_amount,
        'customers': customers  # 👈 Send customers to template
    })



@login_required
def checkout_success(request):
    return render(request, 'pos/checkout_success.html')

@login_required
@role_required(['admin', 'cashier'])
def generate_receipt_pdf(request, sale_id):
    # Ensure the sale belongs to the current user
    sale = get_object_or_404(Sale, id=sale_id, user=request.user)
    items = SaleItem.objects.filter(sale=sale)

    # Calculate the subtotal for each item
    items_with_subtotal = []
    for item in items:
        subtotal = item.price * item.quantity
        items_with_subtotal.append({
            'product': item.product,
            'quantity': item.quantity,
            'price': item.price,
            'subtotal': subtotal
        })
    total = sum(item.price * item.quantity for item in items)
    # Prepare the HTML content for the receipt
    html = render_to_string('pos/receipt.html', {
        'sale': sale,
        'items': items_with_subtotal,
        'total': total,
    })

    # Create the PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receipt_{sale.id}.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)

    # Check if PDF creation was successful
    if pisa_status.err:
        return HttpResponse('We had some problems generating the PDF. Please try again later.')

    return response


@login_required
@role_required(['admin', 'inventory'])
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.user = request.user
            product.save()  # Only this one save is needed
            messages.success(request, "Product added successfully.")
            return redirect('product_list')
    else:
        form = ProductForm()

    return render(request, 'pos/add_product.html', {'form': form})

@login_required
@role_required(['admin', 'inventory'])
def edit_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id, user=request.user)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated successfully.")
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'pos/edit_product.html', {'form': form})

@login_required
@role_required(['admin', 'inventory'])
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk, user=request.user)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted!')
        return redirect('product_list')
    return render(request, 'pos/delete_product.html', {'product': product})


@login_required
@role_required(['admin', 'inventory'])
def category_list(request):
    # Show only the categories created by this user
    categories = Category.objects.filter(user=request.user)
    return render(request, 'pos/category_list.html', {'categories': categories})

@login_required
@role_required(['admin', 'inventory'])
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            # Create category but don’t save yet
            category = form.save(commit=False)
            category.user = request.user  # Assign the logged-in user
            category.save()
            messages.success(request, 'Category added!')
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'pos/add_category.html', {'form': form})

@login_required
@role_required(['admin', 'inventory'])
def edit_category(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated!')
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'pos/edit_category.html', {'form': form})

@login_required
@role_required(['admin'])
def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted!')
        return redirect('category_list')
    return render(request, 'pos/delete_category.html', {'category': category})

@login_required
@role_required(['admin', 'cashier'])
def customer_list(request):
    customers = Customer.objects.filter(user=request.user)  # Filter by user
    return render(request, 'pos/customer_list.html', {'customers': customers})

@login_required
@role_required(['admin', 'cashier'])
def add_customer(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.user = request.user  # Assign the logged-in user
            customer.save()
            messages.success(request, 'Customer added!')
            return redirect('customer_list')
    else:
        form = CustomerForm()
    return render(request, 'pos/add_customer.html', {'form': form})

@login_required
@role_required(['admin', 'cashier'])
def edit_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk, user=request.user)  # Own data only
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer updated!')
            return redirect('customer_list')
    else:
        form = CustomerForm(instance=customer)
    return render(request, 'pos/edit_customer.html', {'form': form})

@login_required
@role_required(['admin'])
def delete_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk, user=request.user)  # Own data only
    if request.method == 'POST':
        customer.delete()
        messages.success(request, 'Customer deleted!')
        return redirect('customer_list')
    return render(request, 'pos/delete_customer.html', {'customer': customer})


def increase_quantity(request, product_id):
    cart = request.session.get('cart', {})
    product_key = str(product_id)

    if product_key in cart:
        cart[product_key]['quantity'] += 1
    else:
        # If product not in cart, you may want to add with quantity 1 and dummy data
        cart[product_key] = {'quantity': 1, 'name': 'Unknown', 'price': 0}

    request.session['cart'] = cart
    return JsonResponse({'status': 'success', 'product_id': product_id, 'quantity': cart[product_key]['quantity']})


def decrease_quantity(request, product_id):
    cart = request.session.get('cart', {})
    product_key = str(product_id)

    if product_key in cart:
        quantity = cart[product_key].get('quantity', 0)

        if quantity > 1:
            cart[product_key]['quantity'] = quantity - 1
        else:
            del cart[product_key]

    request.session['cart'] = cart
    return JsonResponse({'status': 'success', 'product_id': product_id, 'quantity': cart.get(product_key, {}).get('quantity', 0)})


@login_required
@role_required(['admin', 'manager'])
def sales_report(request):
    categories = Category.objects.filter(user=request.user)
    selected_category = request.GET.get('category')
    selected_date = request.GET.get('date')
    results = []
    chart_data = {'labels': [], 'quantities': []}

    if selected_category and selected_date:
        selected_date = parse_date(selected_date)

        sale_items = SaleItem.objects.filter(
            sale__user=request.user,
            product__category__id=selected_category,
            sale__date__date=selected_date
        )

        total_sales = sale_items.aggregate(total=Sum('price'))['total'] or 0
        total_qty = sale_items.aggregate(qty=Sum('quantity'))['qty'] or 0
        customers = (
            sale_items
            .filter(sale__customer__isnull=False)
            .values_list('sale__customer__name', flat=True)
            .distinct()
        )
        product_sales = (
            sale_items
            .values('product__name')
            .annotate(qty=Sum('quantity'))
        )

        chart_data = {
            'labels': [item['product__name'] for item in product_sales],
            'quantities': [item['qty'] for item in product_sales],
        }

        results = {
            'total_sales': total_sales,
            'total_qty': total_qty,
            'customers': customers
        }

    return render(request, 'pos/sales_report.html', {
        'categories': categories,
        'selected_category': int(selected_category) if selected_category else None,
        'selected_date': selected_date,
        'results': results,
        'chart_data': chart_data
    })

@login_required
@role_required(['admin', 'manager'])
def product_sales_report(request):
    report = (
        SaleItem.objects
        .filter(sale__user=request.user)
        .values('product__name')
        .annotate(
            total_quantity=Sum('quantity'),
            total_earned=Sum('price')
        )
        .order_by('-total_quantity')
    )

    return render(request, 'pos/product_sales_report.html', {'report': report})

@login_required
@role_required(['admin', 'manager'])
def daily_revenue_report(request):
    today = now().date()
    last_30_days = today - timedelta(days=30)

    revenue = (
        Sale.objects
        .filter(user=request.user, date__date__gte=last_30_days)
        .annotate(day=TruncDate('date'))
        .values('day')
        .annotate(total=Sum('total_amount'))
        .order_by('-day')
    )

    return render(request, 'pos/daily_revenue_report.html', {'revenue': revenue})



@login_required
@role_required(['admin', 'inventory','cashier'])
def add_product_image_view(request):
    products = Product.objects.filter(user=request.user)
    categories = Category.objects.filter(user=request.user)

    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        stock = request.POST.get('stock')

        if product_id and stock:
            try:
                stock = int(stock)
                product = Product.objects.get(id=product_id, user=request.user)
                product.stock += stock
                product.save()

                temp_products = request.session.get('temp_products', [])
                if product.id not in temp_products:
                    temp_products.append(product.id)
                    request.session['temp_products'] = temp_products

                messages.success(request, f"{product.name} stock updated by {stock}")
                return redirect('product_list')

            except (Product.DoesNotExist, ValueError):
                messages.error(request, "Invalid product or stock value.")
        else:
            messages.error(request, "Please select product and enter valid stock.")

    return render(request, 'pos/add_product_image_select.html', {
        'products': products,
        'categories': categories
    })



@login_required
@role_required(['admin', 'inventory','cashier'])
def add_product_form_view(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.user = request.user
            product.save()
            messages.success(request, "✅ Product added successfully!")
            return redirect('all_products')  # go back to image section
    else:
        form = ProductForm()

    return render(request, 'pos/add_product_form.html', {'form': form})

@login_required
@role_required(['admin', 'cashier'])
def sales_list(request):
    # Get recent sales for the user
    sales = Sale.objects.filter(user=request.user).order_by('-date')[:10]  # Top 10 recent sales
    return render(request, 'pos/sales_list.html', {'sales': sales})