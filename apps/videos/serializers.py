from rest_framework import serializers
from .models import Video, CourseCategory, Lesson, VideoPurchase, LessonProgress, VideoReview

class CourseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseCategory
        fields = ('id', 'name', 'slug', 'icon')

class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ('id', 'title', 'order', 'description', 'duration', 'is_preview', 'created_at')

class VideoSerializer(serializers.ModelSerializer):
    category = CourseCategorySerializer(read_only=True)
    rating = serializers.FloatField(read_only=True)

    class Meta:
        model = Video
        fields = ('id', 'title', 'slug', 'description', 'price', 'discount_price', 'thumbnail', 'category', 'seller', 'views', 'purchases_count', 'rating', 'is_active', 'created_at')

class VideoPurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoPurchase
        fields = ('id', 'user', 'video', 'amount', 'payment_status', 'purchased_at')

class VideoReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoReview
        fields = ('id', 'user', 'video', 'rating', 'comment', 'created_at')

class LessonProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonProgress
        fields = ('id', 'user', 'lesson', 'last_watched_time', 'is_completed', 'updated_at')
