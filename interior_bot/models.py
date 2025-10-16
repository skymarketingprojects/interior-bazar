from django.db import models

# Create your models here.

class MessageBot(models.Model):
    question = models.CharField(max_length=300)
    link = models.TextField(default="https://wa.me/<phone_number>")

    def __str__(self):
        return self.question