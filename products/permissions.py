from rest_framework import permissions
from rest_framework.permissions import BasePermission

class IsOwnerOrReadOnly(permissions.BasePermission):
    # Only the owner of the review can edit or delete it

    def has_object_permission(self, request, view, obj):
        # Allow read-only permissions for safe methods (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True

        # Only the review owner can edit or delete
        return obj.user == request.user
 


class IsAdminForApproval(permissions.BasePermission):
    # Only admin user can change the 'is_visible' status

    def has_permission(self, request, view):
        # Allow only if user is admin (staff)
        return request.user and request.user.is_staff
    
class IsAdminOrSuperUser(BasePermission):
    """
    يسمح فقط للمستخدمين الذين لديهم is_staff أو is_superuser بإنشاء أو تعديل المنتجات
    """
    def has_permission(self, request, view):
        # إذا كانت العملية قراءة فقط -> السماح
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        
        # باقي العمليات (POST, PUT, DELETE) تتطلب أن يكون المستخدم مسؤول أو سوبر يوزر
        return request.user and (request.user.is_staff or request.user.is_superuser)
