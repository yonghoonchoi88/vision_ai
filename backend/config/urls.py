from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView

from analyses.views import create_analysis, list_analyses   # 분석(=자동 저장)·기록 API
from videos.views import upload_video                        # 영상 업로드 API

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/videos/", upload_video),                # ① 영상 업로드
    path("api/analyses/", create_analysis),           # ② 분석 + 자동 저장
    path("api/analyses/history/", list_analyses),     # ③ 검사 기록 목록
    # 임시: analyses 앱의 화면 view가 생기기 전까지 TemplateView로 표시
    path("", TemplateView.as_view(template_name="analyses/index.html")),
]