from django.contrib import admin
from django.utils.html import format_html

from .models import Category, DailyContent


class CategoryChildInline(admin.TabularInline):
    """카테고리 하위 카테고리 인라인"""
    model = Category
    extra = 1
    fk_name = 'parent'
    fields = ('name', 'slug', 'order', 'is_active')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """카테고리 관리자 설정"""
    list_display = ('name', 'parent', 'is_active', 'created_at')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'description')
    ordering = ('parent__name', 'name')

    def get_inlines(self, request, obj=None):
        """부모 카테고리인 경우만 인라인 표시"""
        if obj and obj.parent is None:  # 루트 카테고리인 경우
            return [CategoryChildInline]
        return []


@admin.register(DailyContent)
class DailyContentAdmin(admin.ModelAdmin):
    """일일 콘텐츠 관리자 설정"""
    list_display = ('title', 'category', 'scheduled_date', 'is_sent', 'preview_content')
    list_filter = ('category', 'is_sent', 'scheduled_date')
    search_fields = ('title', 'content', 'additional_info')
    date_hierarchy = 'scheduled_date'
    ordering = ('-scheduled_date',)
    readonly_fields = ('is_sent',)

    fieldsets = (
        (None, {
            'fields': ('title', 'category', 'scheduled_date')
        }),
        ('콘텐츠', {
            'fields': ('content', 'additional_info')
        }),
        ('출처 정보', {
            'fields': ('source', 'url'),
            'classes': ('collapse',)
        }),
        ('상태', {
            'fields': ('is_sent',)
        }),
    )

    def preview_content(self, obj):
        """콘텐츠 미리보기"""
        return format_html('<span title="{}">{}</span>',
                           obj.content,
                           obj.content[:50] + '...' if len(obj.content) > 50 else obj.content)

    preview_content.short_description = '콘텐츠 미리보기'
