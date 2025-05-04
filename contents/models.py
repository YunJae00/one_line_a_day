from django.db import models


class Category(models.Model):
    """
    콘텐츠 카테고리 모델 - 자기참조
    """
    name = models.CharField(max_length=50, verbose_name="카테고리명")
    description = models.TextField(blank=True, verbose_name="설명")

    # 자기참조 관계 (상위 카테고리)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="상위 카테고리"
    )

    is_active = models.BooleanField(default=True, verbose_name="활성화 여부")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")

    class Meta:
        verbose_name = "카테고리"
        db_table = "categories"

    def __str__(self):
        if self.parent:
            return f"{self.name}"
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    @property
    def is_root(self):
        """루트 카테고리 여부"""
        return self.parent is None

    @property
    def has_children(self):
        """하위 카테고리 존재 여부"""
        return self.children.exists()


class DailyContent(models.Model):
    """
    매일 제공할 한 줄 콘텐츠 모델
    """
    title = models.CharField(max_length=100, verbose_name="제목")
    content = models.TextField(verbose_name="내용")
    additional_info = models.TextField(blank=True, verbose_name="추가 설명")

    # 카테고리
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='daily_contents',
        verbose_name="카테고리"
    )

    # 일정 관리
    scheduled_date = models.DateField(verbose_name="예약일")
    is_sent = models.BooleanField(default=False, verbose_name="발송 여부")

    # todo: 이거 굳이 필요한가..?
    # 출처 정보
    source = models.CharField(max_length=255, blank=True, verbose_name="출처")
    url = models.URLField(blank=True, verbose_name="참조 URL")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")

    class Meta:
        verbose_name = "일일 콘텐츠"
        ordering = ['-scheduled_date']
        db_table = "daily_contents"

    def __str__(self):
        return f"{self.category} ({self.scheduled_date}): {self.title}"

    def mark_as_sent(self):
        """콘텐츠를 발송됨으로 표시"""
        self.is_sent = True
        self.save(update_fields=['is_sent'])
