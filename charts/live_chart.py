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
import time
from charts.models import SolarEntryTick, Settings

class LiveChart(object):

    #locale.setlocale(locale.LC_ALL, 'de_DE')

    def __init__(self,pStartDate,pEndDate):
        '''
        Constructor
        '''
        LiveChart.log = logging.getLogger("test")
        LiveChart.log.info("""Start: %s\nEnd: %s\n Period:ticks""" % (pStartDate,pEndDate))

        self.__conn = sqlite3.connect(settings.DATABASES['default']['NAME'])
        self.__rowarray_list_live = {}
        
        self.__formatstring = "%d.%m.%Y %H:%M"
        self.__flot_formatstring = "%H:%M"
        self.__lft = pStartDate
        self.__rht = pEndDate

    def fetchTimeSeriesLiveView(self, deviceID, ticks):
        print self.__lft, self.__rht
        #ticks = SolarEntryTick.objects.filter(time__range=(self.__lft, self.__rht), device = str(deviceID)).order_by('-time')
        self.__rowarray_list_live.update({deviceID : []})

        for tick in ticks:
            if tick.device_id == deviceID:
                t = (time.mktime(tick.time.timetuple()) * 1000, int(tick.lW))
                self.__rowarray_list_live[deviceID].append(t)
            
    def chartOptionsLiveView(self):
        settings = {}
        settings["series"] = {}
        settings["series"]["lines"] = {"show" : "true"}
        #settings["series"]["points"] = {"show" : "true"}
        
        settings["xaxis"] = {
                "mode" : "time",
                "timezone" : "browser",
                "timeformat" : self.__flot_formatstring
        }

        settings["xaxis"].update({"ticks" : 8})
        settings["legend"] = {"backgroundOpacity" : "0.5"}
        settings["crosshair"] = {"mode" : "x"}
        settings["grid"] = {"hoverable" : "true", "autoHighlight" : "false"}
        
        return settings

    def getTimeSeriesLiveView(self, deviceID):
        return self.__rowarray_list_live[deviceID]

    @staticmethod
    def fetch_and_get_ticks_since(device_id, last_tick):
        new_ticks = SolarEntryTick.objects.filter(device=device_id, time__gt=last_tick).order_by("-time")

        return new_ticks
