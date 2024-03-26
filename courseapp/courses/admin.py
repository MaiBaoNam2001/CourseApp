from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django import forms
from django.contrib import admin
from django.contrib.auth.models import Permission
from django.db.models import Count
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.safestring import mark_safe

from . import models


# Register your models here.
class CourseAppAdminSite(admin.AdminSite):
    site_header = 'HỆ THỐNG KHÓA HỌC TRỰC TUYẾN'

    def get_urls(self):
        return [path('course-stats/', self.course_stats_view)] + super().get_urls()

    def course_stats_view(self, request):
        course_count = models.Course.objects.count()
        course_stats = models.Course.objects.annotate(lesson_count=Count('lesson__id')).values('id', 'subject',
                                                                                               'lesson_count')
        return TemplateResponse(request, 'admin/course_stats.html', {
            'course_count': course_count,
            'course_stats': course_stats
        })


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    list_filter = ['id', 'name']
    search_fields = ['name']

    class Media:
        css = {
            'all': ('/static/css/style.css',)
        }


class CourseForm(forms.ModelForm):
    description = forms.CharField(widget=CKEditorUploadingWidget)

    class Meta:
        model = models.Course
        fields = '__all__'


class CourseAdmin(admin.ModelAdmin):
    list_display = ['id', 'subject', 'description']
    list_filter = ['id', 'subject']
    search_fields = ['subject']
    form = CourseForm
    readonly_fields = ['img']

    class Media:
        css = {
            'all': ('/static/css/style.css',)
        }

    def img(self, obj):
        if obj:
            return mark_safe('<img src="/static/{url}" width="120" />'.format(url=obj.image.name))


class LessonTagInlineAdmin(admin.TabularInline):
    model = models.Lesson.tags.through


class LessonForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorUploadingWidget)

    class Meta:
        model = models.Lesson
        fields = '__all__'


class LessonAdmin(admin.ModelAdmin):
    list_display = ['id', 'subject', 'created_date', 'course']
    list_filter = ['id', 'subject', 'created_date']
    search_fields = ['subject']
    form = LessonForm
    readonly_fields = ['img']
    inlines = [LessonTagInlineAdmin]

    class Media:
        css = {
            'all': ('/static/css/style.css',)
        }

    def img(self, obj):
        if obj:
            return mark_safe('<img src="/static/{url}" width="120" />'.format(url=obj.image.name))


class TagAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    list_filter = ['id', 'name']
    search_fields = ['name']

    class Media:
        css = {
            'all': ('/static/css/style.css',)
        }


admin_site = CourseAppAdminSite(name='myadmin')

admin_site.register(models.Category, CategoryAdmin)
admin_site.register(models.Course, CourseAdmin)
admin_site.register(models.Lesson, LessonAdmin)
admin_site.register(models.Tag, TagAdmin)
admin_site.register(Permission)
