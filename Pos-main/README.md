
# 🛒 Django POS System

A role-based multi-user Point of Sale (POS) system built with Django. This system allows Admins, Managers, Cashiers, and Inventory Staff to manage products, sales, customers, and user accounts — all through a clean, Bootstrap-powered frontend interface.

---

## 📦 Features

- 🔐 User Authentication & Role Management (Admin, Manager, Cashier, Inventory)
- 🧾 Sales Management with Cart, Checkout & Receipt
- 📦 Product & Category Management (with image uploads)
- 👥 Customer Tracking
- 📊 Sales Reports (Daily, Product-based, Category-based)
- 🧑‍💼 Admin Panel for User Management
- 📸 Add Products via Image-Based Selection
- 📁 Fully Session-Managed Cart System

---

## 🚀 Getting Started

### 🔧 Requirements

- Python 3.8+
- Django 4+
- SQLite (default) or any preferred database
- pip / venv

---

### 📁 Project Structure

```
pos_system/
├── manage.py
├── db.sqlite3
├── pos/                  # Main POS app
│   ├── models.py
│   ├── views.py
│   ├── templates/pos/    # All user interfaces
│   └── ...
├── pos_system/           # Django project settings
│   └── settings.py
└── command.text          # Setup instructions
```

---

## ⚙️ Setup Instructions

```bash

# Step 3: Run migrations
python manage.py makemigrations
python manage.py migrate

# Step 4: Start the development server
python manage.py runserver
```

---

## 📄 PDF Support

To enable PDF receipt/report generation, install:

```bash
pip install xhtml2pdf
```

---

## 👥 Default Roles

| Role        | Access Level |
|-------------|--------------|
| Admin       | Full control (can manage users, sales, products, reports) |
| Manager     | Manage sales and reports |
| Cashier     | Access to POS, sales, and customers |
| Inventory   | Manage products and categories |

---


## 📸 Add Products via Image

After uploading a product with an image, you can browse products visually via the "Add Product via Image" feature — ideal for touchscreen sales systems.

---

## 🛠 Admin Account Creation

You can create an admin account using:

python manage.py createsuperuser

Or through the custom frontend admin panel after setup.

---

## 📄 License

This project is open-source and free to use for educational or commercial purposes.

---


