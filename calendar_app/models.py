from django.db import models


class Signup(models.Model):
    date_key = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=50)

    class Meta:
        db_table = "signups"
        verbose_name = "Signup"
        verbose_name_plural = "Signups"

    def __str__(self) -> str:
        return f"{self.date_key}: {self.name}"
