from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, ReviewViewSet , RegisterView, CustomTokenObtainPairView, CustomTokenRefreshView, LogoutView

from .views import GeneralAnalyticsView
from .views import AdminReportsView
from .views import NotificationListView

router = DefaultRouter()
router.register('products', ProductViewSet, basename='product')
router.register('reviews', ReviewViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('analytics/general/', GeneralAnalyticsView.as_view(), name='general-analytics'),
    path('admin/reports/', AdminReportsView.as_view(), name='admin-reports'),
    path('notifications/', NotificationListView.as_view(), name='notifications'),
]
 
 ##add endpoint /products/<id>/analytics/