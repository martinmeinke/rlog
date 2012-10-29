from django.db import models

class SolarEntry(models.Model):
    time = models.DateTimeField()
    device = models.IntegerField()
    gV = models.DecimalField(max_digits=9, decimal_places=3)
    gA = models.DecimalField(max_digits=9, decimal_places=3)
    gW = models.DecimalField(max_digits=9, decimal_places=3)
    lV = models.DecimalField(max_digits=9, decimal_places=3)
    lA = models.DecimalField(max_digits=9, decimal_places=3)
    lW = models.DecimalField(max_digits=9, decimal_places=3)
    temp = models.DecimalField(max_digits=9, decimal_places=3)

class Reward(models.Model):
	time = models.DateTimeField()
	value = models.DecimalField(max_digits=5, decimal_places=2)

class Settings(models.Model):
	active = models.BooleanField()
	kwhforsound = models.DecimalField(max_digits=9, decimal_places=3)
	soundfile = models.TextField()