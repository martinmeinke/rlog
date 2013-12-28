# -*- coding: utf-8 -*-
'''
Created on Oct 6, 2012

@author: martin, stephan
'''

import calendar

class LiveChart(object):
    def fetchTimeSeriesLiveView(self, deviceID, ticks):
        return [(calendar.timegm(tick.time.timetuple()) * 1000, int(tick.lW)) for tick in ticks if tick.device_id == deviceID]  # python!!!
    
            
    def chartOptionsLiveView(self):
        settings = {}
        settings["series"] = {}
        settings["series"]["lines"] = {"show" : "true"}
        #settings["series"]["points"] = {"show" : "true"}
        
        settings["xaxis"] = {
                "mode" : "time",
                "timezone" : "UTC",
                "timeformat" : "%H:%M"
        }

        #settings["xaxis"].update({"ticks" : 8})
        settings["legend"] = {"backgroundOpacity" : "0.5", "position" : "nw"}
        settings["crosshair"] = {"mode" : "x", "color": "rgba(0, 170, 0, 0.80)"}
        settings["grid"] = {"hoverable" : "true", "autoHighlight" : "false"}
        
        return settings

