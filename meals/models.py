from django.db import models

class MealSignUp(models.Model):
    date = models.DateField(unique=True)
    name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_unavailable = models.BooleanField(default=False)

    def __str__(self):
        if self.is_unavailable:
            return f"{self.date}: Unavailable"
        return f"{self.date}: {self.name}"
