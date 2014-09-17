from django.db import models

######
# WR #
######

class Device(models.Model):
    model = models.CharField(max_length=32)


class SolarEntryTick(models.Model):
    time = models.DateTimeField()
    device = models.ForeignKey(Device)
    gV = models.DecimalField(max_digits=9, decimal_places=3)
    gA = models.DecimalField(max_digits=9, decimal_places=3)
    gW = models.DecimalField(max_digits=9, decimal_places=3)
    lV = models.DecimalField(max_digits=9, decimal_places=3)
    lA = models.DecimalField(max_digits=9, decimal_places=3)
    lW = models.DecimalField(max_digits=9, decimal_places=3)
    temp = models.DecimalField(max_digits=9, decimal_places=3)
    total = models.DecimalField(max_digits=9, decimal_places=3)
    
# going back to single tables stuff with postgres    
#class SolarEntryTickBackup(models.Model):
#    time = models.DateTimeField()
#    device = models.ForeignKey(Device)
#    gV = models.DecimalField(max_digits=9, decimal_places=3)
#    gA = models.DecimalField(max_digits=9, decimal_places=3)
#    gW = models.DecimalField(max_digits=9, decimal_places=3)
#    lV = models.DecimalField(max_digits=9, decimal_places=3)
#    lA = models.DecimalField(max_digits=9, decimal_places=3)
#    lW = models.DecimalField(max_digits=9, decimal_places=3)
#    temp = models.DecimalField(max_digits=9, decimal_places=3)
#    total = models.DecimalField(max_digits=9, decimal_places=3)

class SolarEntryMinute(models.Model):
    time = models.DateTimeField()
    exacttime = models.DateTimeField(null = True)
    device = models.ForeignKey(Device)
    lW = models.DecimalField(max_digits=9, decimal_places=3)

    class Meta:
        unique_together = (("time", "device"))

#class SolarEntryMinuteBackup(models.Model):
#    time = models.DateTimeField()
#    exacttime = models.DateTimeField(null = True)
#    device = models.ForeignKey(Device)
#    lW = models.DecimalField(max_digits=9, decimal_places=3)
#
#    class Meta:
#        unique_together = (("time", "device"))
        

class SolarEntryHour(models.Model):
    time = models.DateTimeField()
    device = models.ForeignKey(Device)
    lW = models.DecimalField(max_digits=9, decimal_places=3)

    class Meta:
        unique_together = (("time", "device"))


#day can be directly updated from the RS485 data
class SolarEntryDay(models.Model):
    time = models.DateField()
    device = models.ForeignKey(Device)
    lW = models.DecimalField(max_digits=9, decimal_places=3)

    class Meta:
        unique_together = (("time", "device"))


class SolarEntryMonth(models.Model):
    time = models.DateField()
    device = models.ForeignKey(Device)
    lW = models.DecimalField(max_digits=9, decimal_places=3)

    class Meta:
        unique_together = (("time", "device"))


class SolarEntryYear(models.Model):
    time = models.DateField()
    device = models.ForeignKey(Device)
    lW = models.DecimalField(max_digits=9, decimal_places=3)

    class Meta:
        unique_together = (("time", "device"))


class SolarDailyMaxima(models.Model):
  time = models.DateField()
  device = models.ForeignKey(Device)
  lW = models.DecimalField(max_digits=9, decimal_places=3)
  exacttime = models.DateTimeField()
  class Meta:
        unique_together = (("time", "device"))

##############
# SmartMeter #
##############

class SmartMeterEntryTick(models.Model):
    time = models.DateTimeField()
    reading = models.DecimalField(max_digits=9, decimal_places=3)
    phase1 = models.DecimalField(max_digits=9, decimal_places=3)
    phase2 = models.DecimalField(max_digits=9, decimal_places=3)
    phase3 = models.DecimalField(max_digits=9, decimal_places=3)
    
    
#class SmartMeterEntryTickBackup(models.Model):
#    time = models.DateTimeField()
#    reading = models.DecimalField(max_digits=9, decimal_places=3)
#    phase1 = models.DecimalField(max_digits=9, decimal_places=3)
#    phase2 = models.DecimalField(max_digits=9, decimal_places=3)
#    phase3 = models.DecimalField(max_digits=9, decimal_places=3)


class SmartMeterEntryMinute(models.Model):
    time = models.DateTimeField(primary_key=True)
    exacttime = models.DateTimeField(null = True)
    reading = models.DecimalField(max_digits=9, decimal_places=3)
    phase1 = models.DecimalField(max_digits=9, decimal_places=3)
    phase2 = models.DecimalField(max_digits=9, decimal_places=3)
    phase3 = models.DecimalField(max_digits=9, decimal_places=3)

#class SmartMeterEntryMinuteBackup(models.Model):
#    time = models.DateTimeField(primary_key=True)
#    exacttime = models.DateTimeField(null = True)
#    reading = models.DecimalField(max_digits=9, decimal_places=3)
#    phase1 = models.DecimalField(max_digits=9, decimal_places=3)
#    phase2 = models.DecimalField(max_digits=9, decimal_places=3)
#    phase3 = models.DecimalField(max_digits=9, decimal_places=3)
        

class SmartMeterEntryHour(models.Model):
    time = models.DateTimeField(primary_key=True)
    reading = models.DecimalField(max_digits=9, decimal_places=3)
    phase1 = models.DecimalField(max_digits=9, decimal_places=3)
    phase2 = models.DecimalField(max_digits=9, decimal_places=3)
    phase3 = models.DecimalField(max_digits=9, decimal_places=3)


class SmartMeterEntryDay(models.Model):
    time = models.DateField(primary_key=True)
    reading = models.DecimalField(max_digits=9, decimal_places=3)
    phase1 = models.DecimalField(max_digits=9, decimal_places=3)
    phase2 = models.DecimalField(max_digits=9, decimal_places=3)
    phase3 = models.DecimalField(max_digits=9, decimal_places=3)


class SmartMeterEntryMonth(models.Model):
    time = models.DateField(primary_key=True)
    reading = models.DecimalField(max_digits=9, decimal_places=3)
    phase1 = models.DecimalField(max_digits=9, decimal_places=3)
    phase2 = models.DecimalField(max_digits=9, decimal_places=3)
    phase3 = models.DecimalField(max_digits=9, decimal_places=3)


class SmartMeterEntryYear(models.Model):
    time = models.DateField(primary_key=True)
    reading = models.DecimalField(max_digits=9, decimal_places=3)
    phase1 = models.DecimalField(max_digits=9, decimal_places=3)
    phase2 = models.DecimalField(max_digits=9, decimal_places=3)
    phase3 = models.DecimalField(max_digits=9, decimal_places=3)


class SmartMeterDailyMaxima(models.Model):
    time = models.DateField(primary_key=True)
    exacttime = models.DateTimeField()
    maximum = models.DecimalField(max_digits=9, decimal_places=3)
               
                
###############
# other stuff #
###############

class EigenVerbrauch(models.Model):
    time = models.DateField(primary_key=True)
    eigenverbrauch = models.DecimalField(max_digits=9, decimal_places=3) 
  
class Reward(models.Model):
	time = models.DateTimeField()
	value = models.DecimalField(max_digits=5, decimal_places=2)


class Settings(models.Model):
	active = models.BooleanField()
	kwhforsound = models.DecimalField(max_digits=9, decimal_places=3)
	soundfile = models.TextField()
