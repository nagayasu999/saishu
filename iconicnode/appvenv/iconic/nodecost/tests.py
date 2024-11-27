from django.db import models

class Node(models.Model):
    title = models.CharField(max_length=100)
    weight = models.DecimalField(max_digits=4, decimal_places=1, default=1.0)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)  # ここでコストフィールドを追加