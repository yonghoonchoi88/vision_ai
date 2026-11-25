from django.db import models


class Video(models.Model):
    file = models.FileField(upload_to="videos/")
    created_at = models.DateTimeField(auto_now_add=True)