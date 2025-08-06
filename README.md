#### 🚧 The full website is still in progress – stay tuned 🔥  
#### 📅 Expected release date: **8/8/2025**

# Advanced Product Review System

This project is a Django REST Framework-based backend API for managing products, reviews, user interactions, and analytics.

## Features

- JWT Authentication (login, logout, register)
- Role-based access control:
  - Superuser: Full access
  - Admin (is_staff): Manage products
  - Regular user: Add reviews, likes, and comments
- Product management (CRUD)
- Review system:
  - Create/update/delete reviews
  - Like/dislike reviews
  - Comment on reviews
- Review analytics (average rating, reaction counts)
- Fully tested with Django test cases

## Endpoints

Main API endpoints include:
- `/api/products/`
- `/api/reviews/`
- `/api/auth/register/`
- `/api/auth/login/`
- `/api/auth/logout/`

## Setup

```bash
git clone <https://github.com/rahafha1/advanced_product_review_system>
cd advanced_product_review_system
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

