from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework import viewsets, permissions ,status ,generics ,filters
from .models import Product, Review ,Notification ,Interaction ,Report , ReviewComment
from .serializers import RegisterSerializer,ProductSerializer, ReviewSerializer ,ReviewCommentSerializer,InteractionSerializer ,ReportSerializer , NotificationSerializer
from .permissions import IsOwnerOrReadOnly, IsAdminForApproval , IsAdminOrSuperUser
from django_filters.rest_framework import DjangoFilterBackend
# decorators and response
from rest_framework.decorators import action
from rest_framework.response import Response
# time and text analysis
from django.utils.timezone import now, timedelta
from collections import Counter
import re
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser ,IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from django.db.models import Count , Avg, Q


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

# View تسجيل دخول JWT (token obtain)
class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]

# View لتحديث التوكن
class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]

# View لتسجيل الخروج (عمل blacklist للتوكن)
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()  # blacklist للتوكن
            return Response({"detail": "Logged out successfully."}, status=status.HTTP_205_RESET_CONTENT)
        except KeyError:
            return Response({"error": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        except (TokenError, InvalidToken):
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)





class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrSuperUser]
    # Anyone can view products, only authenticated users can add/edit

    @action(detail=True, methods=['get'], url_path='analytics')
    def product_analytics(self, request, pk=None):
        # Get product by ID
        product = self.get_object()
    
        # Last 30 days range
        last_30_days = now() - timedelta(days=30)
    
        # Filter recent visible reviews for this product
        recent_reviews = Review.objects.filter(product=product, created_at__gte=last_30_days, is_visible=True)

        # Calculate average rating
        avg_rating = round(recent_reviews.aggregate(Avg('rating'))['rating__avg'] or 0, 2)


        # Count how many reviews
        review_count = recent_reviews.count()

        # Get highest rated review
        top_rating = recent_reviews.order_by('-rating').first()
        top_rating_value = top_rating.rating if top_rating else None

        # Count most common words in reviews
        words = []
        for review in recent_reviews:
            words += re.findall(r'\b\w+\b', review.review_text.lower())  # Extract words
        word_counts = Counter(words)
        most_common_words = word_counts.most_common(5)

        # Return analytics data
        return Response({
            'average_rating_last_30_days': avg_rating,
            'review_count_last_30_days': review_count,
            'top_recent_rating': top_rating_value,
            'common_words': most_common_words
        })


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend]  
    filterset_fields = ['product', 'rating']  
    ordering_fields = ['created_at', 'rating', 'likes_count']  
    ordering = ['-created_at'] 

    def get_permissions(self):
        # Set different permissions for different actions
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
        elif self.action == 'create':
            permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'approve_review':
            permission_classes = [permissions.IsAuthenticated, IsAdminForApproval]
        else:
            permission_classes = [permissions.IsAuthenticatedOrReadOnly]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        # Set current user as review author
        serializer.save(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        # Get review by ID
        instance = self.get_object()
    
        # Increase views count
        instance.views_count += 1
        instance.save(update_fields=['views_count'])

        # Return review data
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def approve_review(self, request, pk=None):
        # Set review as visible
        review = self.get_object()
        review.is_visible = True
        review.save()

        # Notify review author
        Notification.objects.create(
            user=review.user,
            message=f"Your review for the product '{review.product.name}' has been approved."
        )

        return Response({'status': 'Review approved and user notified ✅'})

    @action(detail=True, methods=['post'], url_path='react')
    def react_to_review(self, request, pk=None):
        # React to a review
        review = self.get_object()
    
        # Prepare reaction data
        data = {
            'review': review.id,
            'reaction': request.data.get('reaction')
            }

        # Validate and save reaction
        serializer = InteractionSerializer(data=data, context={'request': request})
    
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({'status': 'Reaction saved successfully!'}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='report')
    def report_review(self, request, pk=None):
        # Report a review
        review = self.get_object()

        # Prepare report data
        data = {
            'review': review.id,
            'reason': request.data.get('reason', '')
        }

        # Validate and save report
        serializer = ReportSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({'status': 'Report submitted successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
######### comments on reviews ##############
##urls ##
### GET /reviews/<review_id>/comments/ ##
### POST /reviews/<review_id>/add-comment/ ###

    @action(detail=True, methods=['get'], url_path='comments')
    def list_comments(self, request, pk=None):
        # عرض كل التعليقات المرتبطة بالمراجعة
        review = self.get_object()
        comments = review.comments.all().order_by('-created_at')
        serializer = ReviewCommentSerializer(comments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='add-comment', permission_classes=[IsAuthenticated])
    def add_comment(self, request, pk=None):
        # إضافة تعليق جديد على مراجعة
        review = self.get_object()
        serializer = ReviewCommentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(user=request.user, review=review)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class GeneralAnalyticsView(APIView):
    permission_classes = [IsAdminUser]  # Only admin access

    def get(self, request):
        # Last 30 days
        last_30_days = now() - timedelta(days=30)

        # Top reviewers in last 30 days
        top_reviewers = (
            User.objects
            .filter(reviews__created_at__gte=last_30_days)
            .annotate(review_count=Count('reviews'))
            .order_by('-review_count')[:5]
        )

        data = [
            {
                "username": user.username,
                "review_count": user.review_count
            }
            for user in top_reviewers
        ]

        # Top-rated products (avg rating) in last 30 days
        top_rated_products = (
            Product.objects
            .annotate(
                avg_rating = Avg(
                    'reviews__rating',
                    filter=Q(reviews__created_at__gte=last_30_days, reviews__is_visible=True)
                )
            )
            .filter(avg_rating__isnull=False)
            .order_by('-avg_rating')[:5]
        )

        top_products_data = [
            {
                "product_id": product.id,
                "product_name": product.name,
                "average_rating": round(product.avg_rating, 2)
            }
            for product in top_rated_products
        ]

        # Most liked review in last 30 days
        top_review_id = (
            Interaction.objects
            .filter(reaction='like', review__created_at__gte=last_30_days, review__is_visible=True)
            .values('review')
            .annotate(like_count=Count('id'))
            .order_by('-like_count')
            .first()
        )

        top_review_data = None

        if top_review_id:
            top_review_instance = Review.objects.get(id=top_review_id['review'])
            top_review_data = ReviewSerializer(top_review_instance, context={'request': request}).data
            top_review_data['like_count'] = top_review_id['like_count']

        return Response({
            "top_reviewers_last_30_days": data,
            "top_rated_products_last_30_days": top_products_data,
            "top_review_by_likes": top_review_data
        })


class AdminReportsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        from .models import Review
        from django.db.models import Q

        # Count not approved reviews
        not_approved = Review.objects.filter(is_visible=False).count()

        # Count low rated reviews (1 or 2 stars)
        low_rated = Review.objects.filter(rating__in=[1, 2], is_visible=True).count()

        # Count offensive reviews (match bad words)
        offensive_words = ['bad', 'stupid', 'poor', 'shit', 'disgusting']
        offensive_reviews = Review.objects.filter(
            is_visible=True,
            review_text__iregex=r'(' + '|'.join(offensive_words) + ')'
        ).count()

        return Response({
            "not_approved_reviews": not_approved,
            "low_rated_reviews": low_rated,
            "offensive_reviews": offensive_reviews
        })

# List notifications for user
class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')
