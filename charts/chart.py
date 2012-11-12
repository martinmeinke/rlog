# -*- coding: utf-8 -*-
'''
Created on Oct 6, 2012

@author: martin
'''
from django.conf import settings
from dateutil.relativedelta import relativedelta
import datetime
import sqlite3
import locale
import os
import logging
import sys
import random

class Chart(object):
    '''
    classdocs
    '''
    TABLE_BASE = "charts_solarentry"
    locale.setlocale( locale.LC_ALL, 'de_DE')

    def __init__(self,pStartDate,pEndDate,pPeriod):
        '''
        Constructor
        '''
        Chart.log = logging.getLogger("test")
        Chart.log.info("""Start: %s\nEnd: %s\n Period: %s""" % (pStartDate,pEndDate,pPeriod))

        self.__startdate = pStartDate
        self.__enddate = pEndDate
        self.__period = pPeriod
        self.__conn = sqlite3.connect(settings.DATABASES['default']['NAME'])
        self.__totalSupply = 0
        self.__rewardTotal = 0
        
        self.__rowarray_list = []
        self.__rowarray_list_live = []
        
        if self.__period == "period_min":
            self.__formatstring = "%d.%m.%Y %H:%M"
            self.__barwidth = 1000*60
            lft = datetime.datetime.fromtimestamp(self.__startdate)+datetime.timedelta(minutes=-1)
            rht = datetime.datetime.fromtimestamp(self.__enddate)+datetime.timedelta(minutes=1)
        elif self.__period == "period_hrs":
            self.__formatstring = "%d.%m.%Y %H Uhr"
            self.__barwidth = 1000*60*60
            lft = datetime.datetime.fromtimestamp(self.__startdate)+datetime.timedelta(hours=-1)
            rht = datetime.datetime.fromtimestamp(self.__enddate)+datetime.timedelta(hours=1)
        elif self.__period == "period_day":
            self.__formatstring = "%d.%m.%Y"
            self.__barwidth = 1000*60*60*24
            lft = datetime.datetime.fromtimestamp(self.__startdate)+datetime.timedelta(days=-1)
            rht = datetime.datetime.fromtimestamp(self.__enddate)+datetime.timedelta(days=1)
        elif self.__period == "period_wks":
            self.__formatstring = "%W - %Y"
            self.__barwidth = 1000*60*60*24*7
            lft = datetime.datetime.fromtimestamp(self.__startdate)+relativedelta(weeks=-1)
            rht = datetime.datetime.fromtimestamp(self.__enddate)+relativedelta(weeks=1)
        elif self.__period == "period_mon":
            self.__formatstring = "%m/%Y"
            self.__barwidth = 1000*60*60*24*30
            lft = datetime.datetime.fromtimestamp(self.__startdate)+relativedelta(months=-1)
            rht = datetime.datetime.fromtimestamp(self.__enddate)+relativedelta(months=1)
        
        self.__lBoundary = "new Date("+str(lft.year)+","+str(lft.month-1)+","+str(lft.day)+","+str(lft.hour)+","+str(lft.minute)+","+str(lft.second)+").getTime()"
        self.__rBoundary = "new Date("+str(rht.year)+","+str(rht.month-1)+","+str(rht.day)+","+str(rht.hour)+","+str(rht.minute)+","+str(rht.second)+").getTime()"
        
    def fetchTimeSeries(self):
        cursor = self.__conn.cursor()
        subselect = "(SELECT value FROM reward b WHERE time <= a.time ORDER BY time DESC LIMIT 1)"
        
        for row in cursor.execute(
            "SELECT time ,SUM(lW)/360,SUM(lW*"+str(subselect)+"/360)" + 
            "FROM " + self.TABLE_BASE + " a WHERE time BETWEEN "+ str(self.__startdate) + " AND " + str(self.__enddate) +
                " GROUP BY strftime('" + self.__formatstring + "',datetime(time, 'unixepoch'),'localtime') "+
                " ORDER BY time ASC"):
            
            self.__totalSupply+=row[1]
            self.__rewardTotal+=row[2]
            Chart.log.info(str(row))
            t = (int(row[0]) * 1000, row[1])
            self.__rowarray_list.append(t)

    def fetchTimeSeriesLiveView(self):
        cursor = self.__conn.cursor()
        
        for row in cursor.execute(
            "SELECT time , lW " + 
            "FROM " + self.TABLE_BASE + " a "+
                " ORDER BY time DESC "+
                " LIMIT "+str(Chart.TICKS_ON_LIVE_VIEW)):
            
            Chart.log.info(str(row))
            t = (int(row[0]) * 1000, row[1])
            self.__rowarray_list_live.append(t)
    
    def chartOptions(self):
        settings = {}
        settings["series"] = {}
        if len(self.__rowarray_list) > 0:
            Chart.log.info("using lines & points")
            settings["series"]["lines"] = {"show" : "true"}
            settings["series"]["points"] = {"show" : "true"}
        else:
            Chart.log.info("using bars")
            settings["series"]["bars"] = {
                            "show": "true",
                            "align": "left",
                            "barWidth": self.barWidth(),
                            "fill": "true"}
        
        settings["xaxis"] = {
                "mode" : "time",
                "timezone" : "browser",
                "timeformat" : self.__formatstring,
                "min" : self.jsonPlotBoundaries()[0],
                "max" : self.jsonPlotBoundaries()[1]
        }
        
        return settings

    def chartOptionsLiveView(self):
        settings = {}
        settings["series"] = {}
        settings["series"]["lines"] = {"show" : "true"}
        #settings["series"]["points"] = {"show" : "true"}
        
        settings["xaxis"] = {
                "mode" : "time",
                "timezone" : "browser",
                "timeformat" : self.__formatstring
        }
        
        return settings
    
    def barWidth(self):
        return self.__barwidth
    
    def jsonPlotBoundaries(self):
        json = self.__lBoundary,self.__rBoundary
        return json
    
    def getTimeSeriesLiveView(self):
        return self.__rowarray_list_live

    def getTimeSeries(self):
        return self.__rowarray_list

    def getStatTable(self):
        bz = datetime.datetime.fromtimestamp(self.__startdate).strftime(self.__formatstring)
        ez = datetime.datetime.fromtimestamp(self.__enddate).strftime(self.__formatstring)
        
        kws = round(self.__totalSupply,2)
        avgsp = round((self.__totalSupply/self.getNumPoints()),2)
        
        rwrdtotal = locale.currency(self.__rewardTotal/100)
        avgrwrd = locale.currency(self.__rewardTotal/self.getNumPoints()/100)
        
        table = """<table>
                <tr>
                    <td><strong>Beginn Zeitraum:</strong></td>
                    <td>%(bz)s</td>
                </tr>
                <tr>
                    <td><strong>Ende Zeitraum:</strong></td>
                    <td>%(ez)s</td>
                </tr>
                <tr>
                    <td><strong>Kw Eingespeist:</strong></td>
                    <td>%(kws)s</td>
                </tr>
                <tr>
                    <td><strong>Durchschnitt / Periode</strong></td>
                    <td>%(avgsp)s</td>
                </tr>
                <tr>
                    <td><strong>Einspeisevergürung</strong></td>
                    <td>%(rwrdtotal)s</td>
                </tr>
                <tr>
                    <td><strong>Durchschnittleiche Einspeisevergütung</strong></td>
                    <td>%(avgrwrd)s</td>
                </tr>
            </table>""" % vars()
        return table
    
    def getNumPoints(self):
        if len(self.__rowarray_list) > 0:
            return len(self.__rowarray_list)
        else:
            return 1

    def getDeviceIDList(self):
        cursor = self.__conn.cursor()
        devices = []
        
        for row in cursor.execute("SELECT DISTINCT device FROM "+TABLE_BASE):
            devixes.add(row[0]);

        print devices
        return devices
