# -*- coding: utf-8 -*-
'''
Created on Oct 6, 2012

@author: martin
'''
from django.conf import settings
from dateutil.relativedelta import relativedelta
import datetime
import time
import sqlite3
import locale
import os
import sys
import random
import calendar
from charts.models import SolarEntryTick, SolarEntryMinute, SolarEntryHour, SolarEntryDay, SolarEntryMonth, SolarEntryYear, Settings, Device, Reward, SolarDailyMaxima
from django.db.models import Sum

class StatsItem(object):
    def __init__(self, pLabel, pValue):
        self.label = pLabel
        self.value = pValue

class Chart(object):
    locale.setlocale( locale.LC_ALL, 'de_DE')

    SECONDS_PER_MINUTE = 60
    SECONDS_PER_HOUR = SECONDS_PER_MINUTE * 60
    SECONDS_PER_DAY = SECONDS_PER_HOUR * 24
    SECONDS_PER_MONTH = SECONDS_PER_DAY * 30
    SECONDS_PER_YEAR = SECONDS_PER_MONTH * 12

    def __init__(self,pStartDate,pEndDate,pPeriod):
        '''
        Constructor
        '''
        self.__startdate = pStartDate
        self.__enddate = pEndDate
        self.__period = pPeriod
        self.__rewards = []

        self.__bar_scale_factor = 0.9

        self.__conn = sqlite3.connect(settings.DATABASES['default']['NAME'])

        self.__totalSupply = 0
        self.__rewardTotal = 0

        self.__rowarray_list = {}
        self.__rowarray_list_live = {}
        
        if self.__period == "period_min":
            self._formatstring = "%d.%m.%Y %H:%M"
            self.__flot_formatstring = "%H:%M"
            self.__barwidth = 1000*60
        elif self.__period == "period_hrs":
            self._formatstring = "%d.%m.%Y %H Uhr"
            self.__flot_formatstring = "%H Uhr"
            self.__barwidth = 1000*60*60
        elif self.__period == "period_day":
            self._formatstring = "%d.%m.%Y"
            self.__flot_formatstring = "%d.%m"
            self.__barwidth = 1000*60*60*24
        elif self.__period == "period_mon":
            self._formatstring = "%m/%Y"
            self.__flot_formatstring = "%m/%Y"
            self.__barwidth = 1000*60*60*24*30
        elif self.__period == "period_yrs":
            self._formatstring = "%Y"
            self.__flot_formatstring = "%Y"
            self.__barwidth = 1000*60*60*24*30*12
      
        print "Start date: %s\nEnd date: %s" % (self.__startdate, self.__enddate)

    def setChartBoundaries(self):
        shift_seconds = 0
        if (not self.use_line_chart()):
            num_vals = len(self.__rowarray_list[self.getDeviceIDList()[0]])
            if self.__period == "period_min":
                shift_seconds = self.SECONDS_PER_MINUTE / 2
            elif self.__period == "period_hrs":
                shift_seconds = self.SECONDS_PER_HOUR / 2
            elif self.__period == "period_day":
                shift_seconds = self.SECONDS_PER_DAY / 2
            elif self.__period == "period_mon":
                shift_seconds = self.SECONDS_PER_MONTH / 2
            elif self.__period == "period_yrs":
                shift_seconds = self.SECONDS_PER_YEAR / 2

        self.__lBoundary = calendar.timegm(self.__startdate.timetuple()) * 1000 - shift_seconds * 1000
        self.__rBoundary = calendar.timegm(self.__enddate.timetuple()) * 1000


    def getFeederReward(self, deviceID):
        ticks = SolarEntryTick.objects.extra(
            select={
                "valued_reward":"(SELECT value FROM charts_reward b WHERE b.time <= time ORDER BY time DESC LIMIT 1) * lW / 360"
            }
        ).filter(
            time__range=(self.__startdate, self.__enddate), 
            device = str(deviceID)
        )

        v_rewards = (tick["valued_reward"] for tick in ticks)
        return sum(v_rewards)

    def fetchTimeSeries(self, deviceID):
        #self.__startdate = datetime.datetime.utcnow()-relativedelta(minutes=30, second=0, microsecond=0)
        #self.__enddate = datetime.datetime.utcnow()

        if self.__period == "period_min":
            ticks = SolarEntryMinute.objects.filter(
                time__range=(self.__startdate, self.__enddate), 
                device = str(deviceID))
        elif self.__period == "period_hrs":
            ticks = SolarEntryHour.objects.filter(
                time__range=(self.__startdate, self.__enddate), 
                device = str(deviceID))
        elif self.__period == "period_day":
            ticks = SolarEntryDay.objects.filter(
                time__range=(self.__startdate, self.__enddate), 
                device = str(deviceID))
        elif self.__period == "period_mon":
            ticks = SolarEntryMonth.objects.filter(
                time__range=(self.__startdate, self.__enddate), 
                device = str(deviceID))
        elif self.__period == "period_yrs":
            ticks = SolarEntryYear.objects.filter(
                time__range=(self.__startdate, self.__enddate), 
                device = str(deviceID))
        
        self.__rowarray_list.update({deviceID : []})

        for tick in ticks:
            self.__rowarray_list[deviceID].append((calendar.timegm(tick.time.timetuple()) * 1000, float(tick.lW)))

        return 0

    def calc_total_reward(self):
        self.__rewardTotal = 0
        days = SolarEntryDay.objects.filter(
                time__range=(self.__startdate, self.__enddate))

        for day in days:
            self.__rewardTotal += self.get_reward_for_tick(day)

    # basically we want to use bar charts. This is not always possible since the get too
    # small when theres too much of them
    # this is not a very nice solution but at least it works.
    # TODO: consider performing this kind of tasks on the client machine, 
    # maybe giving the decision in the users hand.
    def use_line_chart(self):
        maximum_ticks = len(self.__rowarray_list[self.getDeviceIDList()[0]])

        #compute based on period + timeframe
        delta = self.__enddate - self.__startdate
        seconds = (delta.seconds + delta.days*60*60*24)
        if self.__period == "period_min":
            maximum_ticks = max(maximum_ticks, seconds / Chart.SECONDS_PER_MINUTE)
        elif self.__period == "period_hrs":
            maximum_ticks = max(maximum_ticks, seconds / Chart.SECONDS_PER_HOUR)
        elif self.__period == "period_day":
            maximum_ticks = max(maximum_ticks, seconds / Chart.SECONDS_PER_DAY)
        elif self.__period == "period_mon":
            maximum_ticks = max(maximum_ticks, seconds / Chart.SECONDS_PER_MONTH)
        elif self.__period == "period_yrs":
            maximum_ticks = max(maximum_ticks, seconds / Chart.SECONDS_PER_YEAR)

        return True if maximum_ticks > 35 else False

    def chartOptions(self):
        settings = {}
        settings["series"] = {}

        if self.use_line_chart():
            settings["series"]["lines"] = {"show" : "true"}
            settings["series"]["points"] = {"show" : "true"}
        else:
            settings["series"]["bars"] = {
                "show": "true",
                "align": "left",
                "barWidth": (self.barWidth()/(len(self.getDeviceIDList())+1))*self.__bar_scale_factor,
                "fill": "true",
                "lineWidth": 1}
        
        settings["xaxis"] = {
            "mode" : "time",
            "timezone" : "UTC",
            "timeformat" : self.__flot_formatstring,
            "min" : self.jsonPlotBoundaries()[0],
            "max" : self.jsonPlotBoundaries()[1],
            "axisLabelUseCanvas": "true",
            "axisLabelFontSizePixels": 14,
            "axisLabelFontFamily": 'Verdana, Arial, Helvetica, Tahoma, sans-serif',
            "axisLabelPadding": 10
        }

        settings["yaxis"] = {
            "axisLabel": 'Energie [Wh]',
            "axisLabelUseCanvas": "true",
            "axisLabelFontSizePixels": 14,
            "axisLabelFontFamily": 'Verdana, Arial, Helvetica, Tahoma, sans-serif',
            "axisLabelPadding": 10
        }

        settings["crosshair"] = {
            "mode" : "x",
            "color": "rgba(0, 170, 0, 0.80)"
        }
        settings["grid"] = {
            "hoverable" : "true",
            "autoHighlight" : "false",
            "borderWidth": 1
        }
        settings["legend"] = {
            "backgroundOpacity" : "0.5",
            "position" : "nw"
        }

        #some hacking, should be done a little bit nicer
        #tSpacing = relativedelta(self.__enddate, self.__startdate).hours / 3

        #determine the tick Size (axis labeling)
        #settings["xaxis"].update({"tickSize" : (tSpacing, "hour")})
        #settings["xaxis"].update({"ticks" : 8})

        return settings
    
    def barWidth(self):
        return self.__barwidth
    
    def jsonPlotBoundaries(self):
        json = self.__lBoundary,self.__rBoundary
        return json

    #currently not used!
    @staticmethod
    def build_tick_array(self):
        ticks = []
        for i in self.__rowarray_list[self.getDeviceIDList()[0]]:
            ticks.append((i[0], "date"))
        return ticks
    
    def getTimeSeriesLiveView(self, deviceID):
        return self.__rowarray_list_live[deviceID]

    def getTimeSeries(self, deviceID):
        return self.__rowarray_list[deviceID]

    def getStatItems(self):
        bz = self.__startdate.strftime(self._formatstring)
        ez = self.__enddate.strftime(self._formatstring)
        
        devices = self.getDeviceIDList()
        items = []
        
        # TODO find a way to put that HTML into template
        maximaHTML = ""
        try: # not sure if really works with old tables which do not match updated model
            for deviceID in devices:
                ticks = SolarDailyMaxima.objects.filter(
                    time__range=(self.__startdate, self.__enddate), 
                    device = deviceID).order_by('-lW')
                items.append(StatsItem("Maximum WR {0}:".format(deviceID), "{0}W ({1})".format(ticks[0].lW, ticks[0].exacttime)))
        except Exception as e:
            print "maxima calculation failed", e
            
        single = ""
        try: # i'm a chicken
            for deviceID in devices:
                ticks = SolarEntryDay.objects.filter(
                    time__range=(self.__startdate, self.__enddate), 
                    device = deviceID).aggregate(Sum('lW'))
                items.append(StatsItem("Erzeugung WR {0}:".format(deviceID), "{0}Wh".format(round(ticks["lW__sum"]),2)))
                self.__totalSupply += ticks["lW__sum"]
        except Exception as e:
            print "total energy calculation failed", e
        
        kws = round(self.__totalSupply, 2)
        
        avgsp = None
        try:
            avgsp = round((self.__totalSupply/self.getNumPoints()),2)
        except:
            pass
        
        self.calc_total_reward()
        rwrdtotal = locale.currency(self.__rewardTotal/100)

        avgrwrd = None
        try:
            avgrwrd = locale.currency(self.__rewardTotal/self.getNumPoints()/100)
        except:
            pass

        items.append(StatsItem("Beginn Zeitraum: ", bz))
        items.append(StatsItem("Ende Zeitraum: ", ez))
        items.append(StatsItem("Insgesamt eingespeist: ", str(kws) + "Wh"))
        items.append(StatsItem("Durchschnitt / Periode", avgsp))
        items.append(StatsItem("Einspeisevergütung: ", rwrdtotal))
        items.append(StatsItem("Durchschnittliche Einspeisevergütung: ", avgrwrd))

        return items
       
    
    def getNumPoints(self):
        if len(self.__rowarray_list) > 0:
            return len(self.__rowarray_list[self.getDeviceIDList()[0]])
        else:
            return 1

    @staticmethod
    def getDeviceIDList():
        devices = []
        
        distinct_devices = Device.objects.distinct()

        for device in distinct_devices:
            devices.append(device.id)

        return devices

    #doing it the lazy way now ;)
    def get_reward_for_tick(self, t):
        if len(self.__rewards) == 0:
            self.__rewards.extend(Reward.objects.order_by('-time'))
        
        for r in self.__rewards:
            if isinstance(t.time, datetime.datetime):
                if r.time.date() < t.time.date():
                    return r.value * t.lW / 1000
            else:
                if r.time.date() < t.time:
                    return r.value * t.lW / 1000

        #try:
        #    matching_reward = Reward.objects.filter(time__lte=t.time).order_by('-time')[0]
        #    return matching_reward.value * t.lW / 1000
        #except Exception as ex:
        #    print str(type(ex))+str(ex)
        #except Error as err:
        #    print str(type(err))+str(err)

        return 0


class TickGroup():
    def __init__(self, key, group):
        self._key = key
        self._group = group
