from django.db import models

# Create your models here.
class person(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email_add = models.EmailField(max_length=100)
    department = models.CharField(max_length=50)
    project_role = models.CharField(max_length=30)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"