from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from videos.views import upload_video          # 팀원이 추가한 import (위쪽에 이미 있을 거예요)

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/videos/", upload_video),          # 팀원: 영상 업로드 API
    # 임시: analyses 앱의 view가 생기기 전까지 화면 확인용
    path('', TemplateView.as_view(template_name='analyses/index.html')),
    path("api/analyses/", 분석_함수),
]