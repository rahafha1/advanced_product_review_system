from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Product, Review , Notification ,ReviewComment
from django.db.models import Avg, Count
from .models import Interaction
from .models import Report


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'first_name', 'last_name')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        return user




class ProductSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()  # show product's average rating
    reviews_count = serializers.SerializerMethodField()   # show number of reviews

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'average_rating', 'reviews_count']

    def get_average_rating(self, obj):
        # calculate average rating for this product (visible reviews only)
        avg = Review.objects.filter(product=obj, is_visible=True).aggregate(Avg('rating'))['rating__avg']
        return round(avg, 2) if avg else 0.0

    def get_reviews_count(self, obj):
        # count visible reviews for this product
        return Review.objects.filter(product=obj, is_visible=True).count()


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)  # show username of review owner
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    likes_count = serializers.SerializerMethodField()       # number of likes
    dislikes_count = serializers.SerializerMethodField()    # number of dislikes
    user_reaction = serializers.SerializerMethodField()     # current user's reaction
    views_count = serializers.IntegerField(read_only=True)  # how many times this review was viewed
    is_reported_by_user = serializers.SerializerMethodField()  # has the current user reported this?

    class Meta:
        model = Review
        fields = ['id', 'product', 'user', 'rating', 'review_text', 'is_visible', 'created_at', 'views_count',
          'likes_count', 'dislikes_count', 'user_reaction', 'is_reported_by_user']
        read_only_fields = ('created_at', 'is_visible')

    def validate_rating(self, value):
        # rating must be between 1 and 5
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def get_likes_count(self, obj):
        # count how many users liked this review
        return obj.interactions.filter(reaction='like').count()

    def get_dislikes_count(self, obj):
        # count how many users disliked this review
        return obj.interactions.filter(reaction='dislike').count()

    def get_user_reaction(self, obj):
        # return current user's reaction (if exists)
        user = self.context['request'].user
        if user.is_authenticated:
            interaction = obj.interactions.filter(user=user).first()
            if interaction:
                return interaction.reaction
        return None

    def get_is_reported_by_user(self, obj):
        # return True if current user has already reported this review
        user = self.context['request'].user
        if user.is_authenticated:
            return obj.reports.filter(user=user).exists()
        return False



class ReviewCommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)  # Show username
    review = serializers.PrimaryKeyRelatedField(queryset=Review.objects.all())  # Review ID

    class Meta:
        model = ReviewComment
        fields = '__all__'
        read_only_fields = ['created_at', 'user']  # Auto-filled


class InteractionSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)  # show username only
    review = serializers.PrimaryKeyRelatedField(queryset=Review.objects.all())  # review ID input only

    class Meta:
        model = Interaction
        fields = '__all__'
        read_only_fields = ['created_at', 'user']  # user and created_at are handled automatically

    def validate(self, data):
        # prevent same user from reacting more than once on same review
        user = self.context['request'].user
        review = data.get('review')
        if Interaction.objects.filter(user=user, review=review).exists():
            raise serializers.ValidationError("You have already reacted to this review.")
        return data


class ReportSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)  # show username only
    review = serializers.PrimaryKeyRelatedField(queryset=Review.objects.all())  # review ID

    class Meta:
        model = Report
        fields = '__all__'
        read_only_fields = ['created_at', 'user']  # handled by system

    def validate(self, data):
        # prevent duplicate reports from same user on same review
        user = self.context['request'].user
        review = data.get('review')
        if Report.objects.filter(user=user, review=review).exists():
            raise serializers.ValidationError("You have already reported this review.")
        return data


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
