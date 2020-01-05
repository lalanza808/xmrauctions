from django.db import models
from django.contrib.auth.models import User


class UserShippingAddress(models.Model):
    user = models.ForeignKey(User, related_name='profile', on_delete=models.CASCADE)
    address1 = models.CharField(max_length=100)
    address2 = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=60)
    country = models.CharField(max_length=60)
    zip = models.PositiveIntegerField()

    def __str__(self):
        return self.user.username


# Enforce unique email addresses
User._meta.get_field('email')._unique = True
