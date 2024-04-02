from rest_framework import viewsets, generics, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from . import models, serializers, paginators, perms


# Create your views here.
class CategoryViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = models.Category.objects.filter(active=True)
    serializer_class = serializers.CategorySerializer


class CourseViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = models.Course.objects.filter(active=True)
    serializer_class = serializers.CourseSerializer
    pagination_class = paginators.CoursePaginator

    def filter_queryset(self, queryset):
        q = self.request.query_params.get('q')
        if q:
            queryset = queryset.filter(subject__icontains=q)
        cate_id = self.request.query_params.get('category_id')
        if cate_id:
            queryset = queryset.filter(category_id=cate_id)
        return queryset

    @action(methods=['GET'], detail=True, url_path='lessons')
    def lessons(self, request, pk):
        lessons = self.get_object().lesson_set.filter(active=True)
        lesson = request.query_params.get('lesson')
        if lesson:
            lessons = lessons.filter(subject__icontains=lesson)
        return Response(serializers.LessonSerializer(lessons, many=True, context={'request': request}).data)


class LessonViewSet(viewsets.ViewSet, generics.RetrieveAPIView):
    queryset = models.Lesson.objects.filter(active=True)
    serializer_class = serializers.LessonDetailSerializer

    def get_serializer_class(self):
        if self.request.user.is_authenticated:
            return serializers.AuthorizedLessonDetailSerializer
        return serializers.LessonDetailSerializer

    def get_permissions(self):
        if self.action in ['assign_tags', 'comments', 'like', 'rating']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    @action(methods=['POST'], detail=True, url_path='tags')
    def assign_tags(self, request, pk):
        lesson = self.get_object()
        tags = request.data.get('tags')
        for t in tags:
            tag, _ = models.Tag.objects.get_or_create(name=t)
            lesson.tags.add(tag)
        lesson.save()
        return Response(serializers.LessonDetailSerializer(lesson, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)

    @action(methods=['POST', 'GET'], detail=True, url_path='comments')
    def comments(self, request, pk):
        if request.method.__eq__('POST'):
            comment = models.Comment(content=request.data.get('content'), lesson=self.get_object(), user=request.user)
            comment.save()
            return Response(serializers.CommentSerializer(comment, context={'request': request}).data,
                            status=status.HTTP_201_CREATED)
        comments = self.get_object().comment_set.filter(active=True)
        return Response(serializers.CommentSerializer(comments, many=True, context={'request': request}).data)

    @action(methods=['POST'], detail=True, url_path='like')
    def like(self, request, pk):
        like, created = models.Like.objects.get_or_create(lesson=self.get_object(), user=request.user)
        if not created:
            like.liked = not like.liked
        like.save()
        return Response(status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=True, url_path='rating')
    def rating(self, request, pk):
        rating, _ = models.Rating.objects.get_or_create(lesson=self.get_object(), user=request.user)
        rating.rate = request.data.get('rating')
        rating.save()
        return Response(serializers.RatingSerializer(rating).data, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ViewSet, generics.CreateAPIView):
    queryset = models.User.objects.filter(is_active=True)
    serializer_class = serializers.UserSerializer

    def get_permissions(self):
        if self.action in ['current_user']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    @action(methods=['GET', 'PUT'], detail=False, url_path='current-user')
    def current_user(self, request):
        user = request.user
        if request.method.__eq__('PUT'):
            for key, value in request.data.items():
                if key.__eq__('password'):
                    user.set_password(value)
                else:
                    setattr(user, key, value)
            user.save()
        return Response(serializers.UserSerializer(user).data)


class CommentViewSet(viewsets.ViewSet, generics.DestroyAPIView, generics.UpdateAPIView):
    queryset = models.Comment.objects.filter(active=True)
    serializer_class = serializers.CommentSerializer
    permission_classes = [perms.CommentOwner]
