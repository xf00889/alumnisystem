"""Campus scope for an Alumni Coordinator. Never used to grant additional roles."""
from django.conf import settings
from django.db import models

class CoordinatorCampus(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='coordinator_campus_assignments')
    campus = models.CharField(max_length=10)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'campus'], name='coordinator_unique_campus')]
        ordering = ['campus']
    def __str__(self):
        return f'{self.user_id}: {self.campus}'
