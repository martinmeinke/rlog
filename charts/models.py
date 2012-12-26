from django.db import models

class SolarEntryTick(models.Model):
    time = models.DateTimeField()
    device = models.IntegerField()
    gV = models.DecimalField(max_digits=9, decimal_places=3)
    gA = models.DecimalField(max_digits=9, decimal_places=3)
    gW = models.DecimalField(max_digits=9, decimal_places=3)
    lV = models.DecimalField(max_digits=9, decimal_places=3)
    lA = models.DecimalField(max_digits=9, decimal_places=3)
    lW = models.DecimalField(max_digits=9, decimal_places=3)
    temp = models.DecimalField(max_digits=9, decimal_places=3)
    total = models.DecimalField(max_digits=9, decimal_places=3)

class SolarEntryHour(models.Model):
    time = models.DateTimeField(primary_key=True)
    device = models.IntegerField()
    lW = models.DecimalField(max_digits=9, decimal_places=3)

#day can be directly updated from the RS485 data
class SolarEntryDay(models.Model):
    time = models.DateField(primary_key=True)
    device = models.IntegerField()
    lW = models.DecimalField(max_digits=9, decimal_places=3)

class SolarEntryMonth(models.Model):
    time = models.DateField(primary_key=True)
    device = models.IntegerField()
    lW = models.DecimalField(max_digits=9, decimal_places=3)

class SolarEntryYear(models.Model):
    time = models.DateField(primary_key=True)
    device = models.IntegerField()
    lW = models.DecimalField(max_digits=9, decimal_places=3)

class Reward(models.Model):
	time = models.DateTimeField()
	value = models.DecimalField(max_digits=5, decimal_places=2)

class Settings(models.Model):
	active = models.BooleanField()
	kwhforsound = models.DecimalField(max_digits=9, decimal_places=3)
	soundfile = models.TextField()