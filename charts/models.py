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
    
    
class SolarEntryTickBackup(models.Model):
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


class SolarEntryMinute(models.Model):
    time = models.DateTimeField()
    exacttime = models.DateTimeField(null = True)
    device = models.ForeignKey(Device)
    lW = models.DecimalField(max_digits=9, decimal_places=3)

    class Meta:
        unique_together = (("time", "device"))

class SolarEntryMinuteBackup(models.Model):
    time = models.DateTimeField()
    exacttime = models.DateTimeField(null = True)
    device = models.ForeignKey(Device)
    lW = models.DecimalField(max_digits=9, decimal_places=3)

    class Meta:
        unique_together = (("time", "device"))
        

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

class SmartMeter(models.Model):
    model = models.CharField(max_length=32)


class SmartMeterEntryTick(models.Model):
    time = models.DateTimeField()
    device = models.ForeignKey(SmartMeter)
    gV = models.DecimalField(max_digits=9, decimal_places=3)
    gA = models.DecimalField(max_digits=9, decimal_places=3)
    gW = models.DecimalField(max_digits=9, decimal_places=3)
    lV = models.DecimalField(max_digits=9, decimal_places=3)
    lA = models.DecimalField(max_digits=9, decimal_places=3)
    lW = models.DecimalField(max_digits=9, decimal_places=3)
    temp = models.DecimalField(max_digits=9, decimal_places=3)
    total = models.DecimalField(max_digits=9, decimal_places=3)
    
    
class SmartMeterEntryTickBackup(models.Model):
    time = models.DateTimeField()
    device = models.ForeignKey(SmartMeter)
    gV = models.DecimalField(max_digits=9, decimal_places=3)
    gA = models.DecimalField(max_digits=9, decimal_places=3)
    gW = models.DecimalField(max_digits=9, decimal_places=3)
    lV = models.DecimalField(max_digits=9, decimal_places=3)
    lA = models.DecimalField(max_digits=9, decimal_places=3)
    lW = models.DecimalField(max_digits=9, decimal_places=3)
    temp = models.DecimalField(max_digits=9, decimal_places=3)
    total = models.DecimalField(max_digits=9, decimal_places=3)


class SmartMeterEntryMinute(models.Model):
    time = models.DateTimeField()
    exacttime = models.DateTimeField(null = True)
    device = models.ForeignKey(SmartMeter)
    lW = models.DecimalField(max_digits=9, decimal_places=3)

    class Meta:
        unique_together = (("time", "device"))

class SmartMeterEntryMinuteBackup(models.Model):
    time = models.DateTimeField()
    exacttime = models.DateTimeField(null = True)
    device = models.ForeignKey(SmartMeter)
    lW = models.DecimalField(max_digits=9, decimal_places=3)

    class Meta:
        unique_together = (("time", "device"))
        

class SmartMeterEntryHour(models.Model):
    time = models.DateTimeField()
    device = models.ForeignKey(SmartMeter)
    lW = models.DecimalField(max_digits=9, decimal_places=3)

    class Meta:
        unique_together = (("time", "device"))


class SmartMeterEntryDay(models.Model):
    time = models.DateField()
    device = models.ForeignKey(SmartMeter)
    lW = models.DecimalField(max_digits=9, decimal_places=3)

    class Meta:
        unique_together = (("time", "device"))


class SmartMeterEntryMonth(models.Model):
    time = models.DateField()
    device = models.ForeignKey(SmartMeter)
    lW = models.DecimalField(max_digits=9, decimal_places=3)

    class Meta:
        unique_together = (("time", "device"))


class SmartMeterEntryYear(models.Model):
    time = models.DateField()
    device = models.ForeignKey(SmartMeter)
    lW = models.DecimalField(max_digits=9, decimal_places=3)

    class Meta:
        unique_together = (("time", "device"))


class SmartMeterDailyMaxima(models.Model):
  time = models.DateField()
  device = models.ForeignKey(SmartMeter)
  lW = models.DecimalField(max_digits=9, decimal_places=3)
  exacttime = models.DateTimeField()
  class Meta:
        unique_together = (("time", "device"))
               
                
###############
# other stuff #
############### 
  
class Reward(models.Model):
	time = models.DateTimeField()
	value = models.DecimalField(max_digits=5, decimal_places=2)


class Settings(models.Model):
	active = models.BooleanField()
	kwhforsound = models.DecimalField(max_digits=9, decimal_places=3)
	soundfile = models.TextField()
