from django.db import models


class Analysis(models.Model):
    video = models.ForeignKey(
        "videos.Video",
        on_delete=models.CASCADE,
        related_name="analyses",
    )
    predicted_action = models.CharField(max_length=50)
    confidence = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.predicted_action} ({self.confidence:.2f})"