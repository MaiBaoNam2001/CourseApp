from rest_framework import serializers
from . import models


class ImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField(source='image')

    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            return request.build_absolute_uri('/static/%s' % obj.image.name) if request else ''


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Category
        fields = ['id', 'name']


class CourseSerializer(ImageSerializer):
    class Meta:
        model = models.Course
        fields = ['id', 'subject', 'image', 'created_date', 'category_id']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tag
        fields = ['id', 'name']


class LessonSerializer(ImageSerializer):
    tags = TagSerializer(many=True)

    class Meta:
        model = models.Lesson
        fields = ['id', 'subject', 'image', 'course_id', 'created_date', 'updated_date', 'tags']


class LessonDetailSerializer(LessonSerializer):
    class Meta:
        model = LessonSerializer.Meta.model
        fields = LessonSerializer.Meta.fields + ['content']


class AuthorizedLessonDetailSerializer(LessonDetailSerializer):
    liked = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()

    def get_liked(self, lesson):
        request = self.context.get('request')
        return lesson.like_set.filter(user=request.user, liked=True).exists() if request else False

    def get_rating(self, lesson):
        request = self.context.get('request')
        rating = lesson.rating_set.filter(user=request.user).first()
        return rating.rate if rating else 0

    class Meta:
        model = LessonDetailSerializer.Meta.model
        fields = LessonDetailSerializer.Meta.fields + ['liked', 'rating']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = ['first_name', 'last_name', 'username', 'password', 'email', 'avatar']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        data = validated_data.copy()
        user = models.User(**data)
        user.set_password(user.password)
        user.save()
        return user


class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = models.Comment
        fields = ['id', 'content', 'created_date', 'updated_date', 'user']


class RatingSerializer(serializers.ModelSerializer):
    rating = serializers.SerializerMethodField(source='rate')

    def get_rating(self, obj):
        return obj.rate if obj.rate else 0

    class Meta:
        model = models.Rating
        fields = ['rating']
