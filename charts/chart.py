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

class Chart(object):
    locale.setlocale( locale.LC_ALL, 'de_DE')

    def __init__(self,pStartDate,pEndDate,pPeriod):
        '''
        Constructor
        '''
        self.__startdate = pStartDate
        self.__enddate = pEndDate
        self.__period = pPeriod
        self.__rewards = []

        self.__conn = sqlite3.connect(settings.DATABASES['default']['NAME'])

        self.__totalSupply = 0
        self.__rewardTotal = 0

        self.__rowarray_list = {}
        self.__rowarray_list_live = {}
        
        if self.__period == "period_min":
            self.__formatstring = "%d.%m.%Y %H:%M"
            self.__flot_formatstring = "%H:%M"
            self.__barwidth = 1000*60
            lft = self.__startdate+datetime.timedelta(minutes=-1)
            rht = self.__enddate+datetime.timedelta(minutes=1)
        elif self.__period == "period_hrs":
            self.__formatstring = "%d.%m.%Y %H Uhr"
            self.__flot_formatstring = "%H Uhr"
            self.__barwidth = 1000*60*60
            lft = self.__startdate+datetime.timedelta(hours=-1)
            rht = self.__enddate+datetime.timedelta(hours=1)
        elif self.__period == "period_day":
            self.__formatstring = "%d.%m.%Y"
            self.__flot_formatstring = "%d.%m"
            self.__barwidth = 1000*60*60*24
            lft = self.__startdate+datetime.timedelta(days=-1)
            rht = self.__enddate+datetime.timedelta(days=1)
        elif self.__period == "period_mon":
            self.__formatstring = "%m/%Y"
            self.__flot_formatstring = "%m/%Y"
            self.__barwidth = 1000*60*60*24*30
            lft = self.__startdate+relativedelta(months=-1)
            rht = self.__enddate+relativedelta(months=1)
        elif self.__period == "period_yrs":
            self.__formatstring = "%Y"
            self.__flot_formatstring = "%Y"
            self.__barwidth = 1000*60*60*24*30*12
            lft = self.__startdate+relativedelta(years=-1)
            rht = self.__enddate+relativedelta(years=1)

#        self.__lBoundary = "new Date("+str(lft.year)+","+str(lft.month-1)+","+str(lft.day)+","+str(lft.hour)+","+str(lft.minute)+","+str(lft.second)+").getTime()"
#        self.__lBoundary = "(new timezoneJS.Date(" + str(lft.year)+","+str(lft.month - 1)+","+str(lft.day)+","+str(lft.hour)+","+str(lft.minute)+","+str(lft.second) + ", 'Europe/Berlin')).getTime()"
        self.__lBoundary = calendar.timegm(lft.utctimetuple()) * 1000
#        self.__rBoundary = "new Date("+str(rht.year)+","+str(rht.month-1)+","+str(rht.day)+","+str(rht.hour)+","+str(rht.minute)+","+str(rht.second)+").getTime()"
#        self.__rBoundary = "(new timezoneJS.Date(" +str(rht.year)+","+str(rht.month - 1)+","+str(rht.day)+","+str(rht.hour)+","+str(rht.minute)+","+str(rht.second) + ", 'Europe/Berlin')).getTime()"
        self.__rBoundary = calendar.timegm(rht.utctimetuple()) * 1000
      
        print "Start date: %s\nEnd date: %s" % (self.__startdate, self.__enddate)

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

        #ticks = SolarEntryTick.objects.extra(
        #    select={
        #        "groupkey":"strftime('" + self.__formatstring + "', datetime(time, 'utc'),'localtime')",
        #    }
        #).filter(
        #    time__range=(self.__startdate, self.__enddate), 
        #    device = str(deviceID)
        #)

        #tick_groups = {}

        #groups = groupby(ticks, lambda x: x.groupkey)
        #for key, group in groups: 
        #    tick_groups[key] = TickGroup(key, group)
        #    tick_groups[key]["lW"] = 0
        #    for tick in group:
        #        print "A %s is in %s." % (tick.groupkey, key)
        #        tick_groups[key]["lW"] += tick.lW
        #    print " "
        
        self.__rowarray_list.update({deviceID : []})

        #print ticks.query
        #print ticks

        #import pdb; pdb.set_trace()
        
        for tick in ticks:
            self.__totalSupply += tick.lW
            self.__rewardTotal += self.get_reward_for_tick(tick)
            t = None
            if self.__period == "period_min" or self.__period == "period_hrs":
                t = (calendar.timegm(tick.time.utctimetuple()) * 1000, float(tick.lW))
            else:
                t = (time.mktime(tick.time.timetuple()) * 1000, float(tick.lW))
            self.__rowarray_list[deviceID].append(t)
           # print t
           # print vars(tick)
        print "start", self.__startdate, calendar.timegm(self.__startdate.utctimetuple()) * 1000, "end", self.__enddate, calendar.timegm(self.__enddate.utctimetuple()) * 1000

        return 0

        '''
        cursor = self.__conn.cursor()
        subselect = ("("
            "SELECT value "
            "FROM reward b "
            "WHERE time <= a.time "
            "   ORDER BY time DESC "
            "   LIMIT 1"
            ")")

        q_string = (
            "SELECT time ,SUM(lW)/360,SUM(lW*"+str(subselect)+"/360)"
            "FROM " + self.TABLE_BASE + " a "
            "WHERE time BETWEEN "+ str(self.__startdate) + " AND " + str(self.__enddate) +""
                " GROUP BY strftime('" + self.__formatstring + "',datetime(time, 'utc'),'localtime') "
                " ORDER BY time ASC")
        
        self.__rowarray_list.update({deviceID : []})

        for row in cursor.execute(q_string):
            self.__totalSupply+=row[1]
            self.__rewardTotal+=row[2]
            t = (int(row[0]) * 1000, row[1])
            self.__rowarray_list[deviceID].append(t)
        '''

    def chartOptions(self):
        settings = {}
        settings["series"] = {}
        if len(self.__rowarray_list) > 0:
            settings["series"]["lines"] = {"show" : "true"}
            settings["series"]["points"] = {"show" : "true"}
        else:
            settings["series"]["bars"] = {
                            "show": "true",
                            "align": "left",
                            "barWidth": self.barWidth(),
                            "fill": "true"}
        
        settings["xaxis"] = {
                "mode" : "time",
                "timezone" : "Europe/Berlin",
                "timeformat" : self.__flot_formatstring,
                "min" : self.jsonPlotBoundaries()[0],
                "max" : self.jsonPlotBoundaries()[1]
        }
        settings["crosshair"] = {
                "mode" : "x",
                "color": "rgba(0, 170, 0, 0.80)"
        }
        settings["grid"] = {
                "hoverable" : "true",
                "autoHighlight" : "false"
        }
        settings["legend"] = {
            "backgroundOpacity" : "0.5"
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
    
    def getTimeSeriesLiveView(self, deviceID):
        return self.__rowarray_list_live[deviceID]

    def getTimeSeries(self, deviceID):
        return self.__rowarray_list[deviceID]

    def getStatTable(self):
        bz = self.__startdate.strftime(self.__formatstring)
        ez = self.__enddate.strftime(self.__formatstring)
        
        kws = round(self.__totalSupply,2)
        avgsp = None
        try:
            avgsp = round((self.__totalSupply/self.getNumPoints()),2)
        except:
            pass
        
        rwrdtotal = locale.currency(self.__rewardTotal/100)

        avgrwrd = None
        try:
            avgrwrd = locale.currency(self.__rewardTotal/self.getNumPoints()/100)
        except:
            pass
        
        devices = []
        distinct_devices = Device.objects.distinct()
        for device in distinct_devices:
            devices.append(device.id)
        
        # TODO find a way to put that HTML into template
        maximaHTML = ""
        try: # not sure if really works with old tables which do not match updated model
            for deviceID in devices:
                ticks = SolarDailyMaxima.objects.filter(
                    time__range=(self.__startdate, self.__enddate), 
                    device = deviceID).order_by('-lW')
                maximaHTML += """<tr>
                        <td><strong>Maximum WR {0}:</strong></td>
                        <td>{1}W ({2})</td>
                    </tr>""".format(deviceID, ticks[0].lW, datetime.datetime.fromtimestamp(calendar.timegm(ticks[0].exacttime.utctimetuple())))
        except Exception as e:
            print "maxima calculation failed", e
        
        #TODO: split this up in several methods and move HTML to template
        table = """<table class="table table-striped">
                <tr>
                    <td><strong>Beginn Zeitraum:</strong></td>
                    <td>%(bz)s</td>
                </tr>
                <tr>
                    <td><strong>Ende Zeitraum:</strong></td>
                    <td>%(ez)s</td>
                </tr>
                <tr>
                    <td><strong>W eingespeist:</strong></td>
                    <td>%(kws)s</td>
                </tr>
                <tr>
                    <td><strong>Durchschnitt / Periode</strong></td>
                    <td>%(avgsp)s</td>
                </tr>
                %(maximaHTML)s
                <tr>
                    <td><strong>Einspeiseverguetung</strong></td>
                    <td>%(rwrdtotal)s</td>
                </tr>
                <tr>
                    <td><strong>Durchschnittleiche Einspeiseverguetung</strong></td>
                    <td>%(avgrwrd)s</td>
                </tr>
            </table>""" % vars()
        return table
    
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
