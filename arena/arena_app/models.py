from django.db import models
from datetime import datetime
from django.contrib.auth.models import User


    
class Sessions(models.Model):
    sport_type = models.CharField(max_length=100)
    time = models.DateTimeField()
    location = models.CharField(max_length=50)
    game_size = models.IntegerField()
    # price = models.FloatField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    slots_taken = models.IntegerField(default=0)
    
class Quiz(models.Model):
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=100)
    gender = models.CharField(max_length=100)
    dob = models.DateField()
    location = models.CharField(max_length=100)
    fav_sport = models.CharField(max_length=10000)

class Booking(models.Model):
    userid = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='bookings')
    sessionid = models.ForeignKey(Sessions, on_delete=models.SET_NULL, null=True, related_name='bookings')
    
