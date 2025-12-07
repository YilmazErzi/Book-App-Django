from django.db import models

# Create your models here.
class Book(models.Model):
    title = models.CharField(max_length=150)
    author = models.CharField(max_length=100)
    publish_date = models.IntegerField(max_length=4)
    summary = models.TextField()

    def __str__(self):
        return f"{self.title}"