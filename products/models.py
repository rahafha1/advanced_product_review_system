from django.db import models
from django.contrib.auth.models import User

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name  # show product name in admin


class Review(models.Model):
    STAR_CHOICES = [
        (1, '⭐'),
        (2, '⭐⭐'),
        (3, '⭐⭐⭐'),
        (4, '⭐⭐⭐⭐'),
        (5, '⭐⭐⭐⭐⭐'),
    ]

    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)  # product related to this review
    user = models.ForeignKey(User, related_name='reviews', on_delete=models.CASCADE)  # user who wrote the review
    rating = models.IntegerField(choices=STAR_CHOICES)  # rating with stars
    review_text = models.TextField()
    is_visible = models.BooleanField(default=False)  # visible after approval
    created_at = models.DateTimeField(auto_now_add=True)
    views_count = models.PositiveIntegerField(default=0)  # how many times this review was viewed



    def __str__(self):
        return f"{self.product.name} - {self.rating} Stars by {self.user.username}"


class ReviewComment(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="comments")  # المرتبط بالمراجعة
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="review_comments")  # من كتب الرد
    comment_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on review {self.review.id}"



class Interaction(models.Model):
    REVIEW_REACTION_CHOICES = [
        ('like', 'Helpful'),
        ('dislike', 'Not Helpful'),
    ]

    review = models.ForeignKey(Review, related_name='interactions', on_delete=models.CASCADE)  # target review
    user = models.ForeignKey(User, related_name='review_interactions', on_delete=models.CASCADE)  # user who reacted
    reaction = models.CharField(max_length=10, choices=REVIEW_REACTION_CHOICES)  # like/dislike
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('review', 'user')  # prevent same user from reacting twice to same review

    def __str__(self):
        return f"{self.user.username} - {self.reaction} - {self.review.id}"


class Report(models.Model):
    review = models.ForeignKey(Review, related_name='reports', on_delete=models.CASCADE)  # reported review
    user = models.ForeignKey(User, related_name='review_reports', on_delete=models.CASCADE)  # user who reported
    reason = models.TextField()  # reason of report
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('review', 'user')  # prevent duplicate reports by same user

    def __str__(self):
        return f"Report by {self.user.username} on review {self.review.id}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')  # user to notify
    message = models.CharField(max_length=255)  # notification content
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)  # mark if read

    def __str__(self):
        return f"To {self.user.username}: {self.message}"


