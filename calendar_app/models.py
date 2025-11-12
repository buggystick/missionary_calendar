from django.db import models


class Signup(models.Model):
    date_key = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = "signups"
        ordering = ["date_key"]
