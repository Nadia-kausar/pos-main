from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from pos.views import signup_view
from .views import logout_view
from .views import add_expense, expense_list
from .views import add_user_view


urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='pos/login.html'), name='login'),
    path('logout/', logout_view, name='logout'),
    path('signup/', signup_view, name='signup'),

    # Product Views
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('products/delete/<int:pk>/', views.delete_product, name='delete_product'),
    path('products/category/<int:category_id>/', views.products_by_category_id, name='products_by_category_id'),
    path('products/image-add/', views.add_product_image_view, name='all_products'),
    path('add/product/form/', views.add_product_form_view, name='add_product_form'),
    path('add-product-image-select/', views.add_product_image_view, name='add_product_image_select'),  # ✅ Fix for missing route

    # Category Views
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.add_category, name='add_category'),
    path('categories/edit/<int:pk>/', views.edit_category, name='edit_category'),
    path('categories/delete/<int:pk>/', views.delete_category, name='delete_category'),

    # Customer Views
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/add/', views.add_customer, name='add_customer'),
    path('customers/edit/<int:pk>/', views.edit_customer, name='edit_customer'),
    path('customers/delete/<int:pk>/', views.delete_customer, name='delete_customer'),

    # Cart & Checkout
    path('cart/', views.cart_view, name='cart'),
    path('cart/increase/<int:product_id>/', views.increase_quantity, name='increase_quantity'),
    path('cart/decrease/<int:product_id>/', views.decrease_quantity, name='decrease_quantity'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('get-product/<int:pk>/', views.get_product, name='get_product'),
    path('get-cart/', views.get_cart_data, name='get_cart_data'),
    path('checkout/', views.checkout, name='checkout'),
    path('checkout-success/', views.checkout_success, name='checkout_success'),
    path('receipt/<int:sale_id>/', views.generate_receipt_pdf, name='receipt_pdf'),
    path('sales/', views.sales_list, name='sales_list'),  # Page showing recent sales

    # Reports
    path('sales-report/', views.sales_report, name='sales_report'),
    path('product-sales-report/', views.product_sales_report, name='product_sales_report'),
    path('daily-revenue-report/', views.daily_revenue_report, name='daily_revenue_report'),
    
    #Ajax
    path('increase-quantity/<int:product_id>/', views.increase_quantity, name='increase_quantity'),
    path('decrease-quantity/<int:product_id>/', views.decrease_quantity, name='decrease_quantity'),

    #Expense
    path('expenses/add/', add_expense, name='add_expense'),
    path('expenses/', expense_list, name='expense_list'),
    path('expenses/<int:expense_id>/edit/', views.edit_expense, name='edit_expense'),
    path('expenses/<int:expense_id>/delete/', views.delete_expense, name='delete_expense'),

    path('add-user/<str:role>/', views.add_user_view, name='add_user'),
    path('admin-users/', views.admin_users_list, name='admin_users_list'),

    
]