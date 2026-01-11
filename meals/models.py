from django.db import models

class MealSignUp(models.Model):
    date = models.DateField(unique=True)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.date}: {self.name}"
