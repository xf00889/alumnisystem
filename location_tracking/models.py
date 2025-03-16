from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class LocationData(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='locations')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} - {self.timestamp}"
