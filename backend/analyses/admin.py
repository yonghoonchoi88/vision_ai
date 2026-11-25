from django.contrib import admin

from .models import Analysis


@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = ["id", "video", "predicted_action", "confidence", "created_at"]