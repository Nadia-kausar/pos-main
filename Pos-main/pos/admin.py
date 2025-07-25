from django.contrib import admin
from .models import *
from .models import UserProfile

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Customer)
admin.site.register(Sale)
admin.site.register(SaleItem)
admin.site.register(UserProfile)

