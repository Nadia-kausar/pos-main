from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Product(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True , blank=True)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    price = models.FloatField()
    stock = models.IntegerField()
    barcode = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True) 
    def __str__(self):
        return self.name

class Customer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    loyalty_points = models.IntegerField(default=0)

    def __str__(self):
        return self.name

class Sale(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)  
    discount = models.FloatField(default=0)
    payment_method = models.CharField(max_length=50, choices=[('cash', 'Cash'), ('card', 'Card')])
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    change_due = models.DecimalField(max_digits=10, decimal_places=2, default=0)

class SaleItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.FloatField()  # Price per item at sale time



class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('cashier', 'Cashier'),
        ('manager', 'Manager'),
        ('inventory', 'Inventory'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    created_by = models.ForeignKey(User, related_name='created_users', on_delete=models.CASCADE,null=True)  # Track which admin created this user

    def __str__(self):
        return f"{self.user.username} - {self.role}"


class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('Rent', 'Rent'),
        ('Utilities', 'Utilities'),
        ('Salary', 'Salary'),
        ('Inventory', 'Inventory'),
        ('Other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.category} - {self.amount}"