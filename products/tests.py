## common tests
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
## products tests
from products.models import Product
from rest_framework_simplejwt.tokens import RefreshToken
## reviews tests :


##### tests for register ,login , logout #####
class AuthTests(APITestCase):

    def setUp(self):
        # مستخدم جاهز لاختبارات تسجيل الدخول والخروج
        self.test_user = User.objects.create_user(username='testuser', password='testpass123')

    def test_register_user(self):
        url = reverse('register')
        data = {
            'username': 'newuser',
            'password': 'newpass123',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_login_user(self):
        url = reverse('token_obtain_pair')
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        # حفظ التوكنات لاستخدامها في اختبار تسجيل الخروج
        self.access_token = response.data['access']
        self.refresh_token = response.data['refresh']

    def test_logout_user(self):
        # تسجيل الدخول للحصول على التوكنات
        login_url = reverse('token_obtain_pair')
        login_data = {'username': 'testuser', 'password': 'testpass123'}
        login_response = self.client.post(login_url, login_data, format='json')
        refresh_token = login_response.data['refresh']
        access_token = login_response.data['access']

        logout_url = reverse('logout')
        logout_data = {'refresh': refresh_token}

        # إضافة هيدر Authorization مع توكن الوصول
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.post(logout_url, logout_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        self.assertEqual(response.data['detail'], "Logged out successfully.")


    def test_logout_without_refresh_token(self):
        login_url = reverse('token_obtain_pair')
        login_data = {'username': 'testuser', 'password': 'testpass123'}
        login_response = self.client.post(login_url, login_data, format='json')
        access_token = login_response.data['access']

        logout_url = reverse('logout')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.post(logout_url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


    def test_login_invalid_credentials(self):
        url = reverse('token_obtain_pair')
        data = {
            'username': 'wronguser',
            'password': 'wrongpass'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        

#### tests for products ####

class ProductTests(APITestCase):
    def setUp(self):
        # Create admin user
        self.admin_user = User.objects.create_user(username='admin', password='adminpass', is_staff=True)
        self.admin_token = RefreshToken.for_user(self.admin_user).access_token

        # Create normal user
        self.normal_user = User.objects.create_user(username='user', password='userpass')
        self.normal_token = RefreshToken.for_user(self.normal_user).access_token

        # Sample product
        self.product = Product.objects.create(
            name="Test Product",
            description="This is a test product",
            price=9.99
        )

        self.create_url = reverse('product-list')
        self.list_url = reverse('product-list')   
        self.detail_url = reverse('product-detail', kwargs={'pk': self.product.pk})


## view all products test :
    def test_list_products(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

## view product details test :
    def test_product_detail(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.product.name)

### create new product by admin :
    def test_create_product_as_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(self.admin_token))
        data = {
            "name": "New Product",
            "description": "Created by admin",
            "price": 19.99
        }
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

### try to create product by normal user :
    def test_create_product_as_user_forbidden(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(self.normal_token))
        data = {
            "name": "Hacked Product",
            "description": "Trying to bypass permissions",
            "price": 15.99
        }
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

### delete & update products tests :
    def test_update_product_as_admin_success(self):
        self.admin_user = User.objects.create_user(username='admin2', password='adminpass', is_staff=True)
        self.client.force_authenticate(user=self.admin_user)

        product = Product.objects.create(
            name="Product to Edit",
            description="Old description",
            price=20.00
        )

        url = reverse('product-detail', args=[product.id])
        data = {
            "name": "Edited Product",
            "description": "Updated description",
            "price": 25.00
        }

        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Edited Product")

    def test_delete_product_as_admin_success(self):
        self.admin_user = User.objects.create_user(username='admin3', password='adminpass', is_staff=True)
        self.client.force_authenticate(user=self.admin_user)

        product = Product.objects.create(
            name="Product to Delete",
            description="Desc",
            price=15.00
        )

        url = reverse('product-detail', args=[product.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


## failuer to update & delete by regular user test :
    def test_update_product_as_user_forbidden(self):
        self.client.force_authenticate(user=self.normal_user)

        product = Product.objects.create(
            name="Product",
            description="Desc",
            price=12.00
        )

        url = reverse('product-detail', args=[product.id])
        data = {"name": "New Name"}

        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_product_as_user_forbidden(self):
        self.client.force_authenticate(user=self.normal_user)

        product = Product.objects.create(
            name="Product",
            description="Desc",
            price=13.00
        )

        url = reverse('product-detail', args=[product.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


### tests for reviews ####






### tests for comments ##
### tests on reactions ###
## tests for notifications ##


