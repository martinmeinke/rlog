#!/usr/bin/env python
 
'''
Created on Oct 10, 2012

@author: martin and stephan
'''
import serial
#import sqlite3
import psycopg2
import time
import commands
import os
import sys
import string
import mqtt
from daemon import Daemon
import argparse
import re
from decimal import Decimal
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.tz import tzlocal


DEBUG_ENABLED = False

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
#DATABASE = PROJECT_PATH+"/../sensor.db"
DEVICE_NAME_BASE = "/dev/ttyUSB"
MQTT_HOST = "localhost"

LOCATIONX = "14.122994"
LOCATIONY = "52.508519"

def log(msg):
    stripped = str(msg).translate(string.maketrans("\n\r", "  "))
    print "[%s]: %s" % (str(datetime.now(tzlocal())), stripped)

class WR():
    def __init__(self, bus_id, serial_port):
        self.__serial_port = serial_port
        self.__bus_id = bus_id
        self.__model = ""
        self.__bytesize = serial.EIGHTBITS
        self.__parity = serial.PARITY_NONE
        self.setup_serial_port()
    
    # getters for member variables
    @property
    def bus_id(self):
        return self.__bus_id
    
    @property
    def model(self):
        return self.__model
        
    def setup_serial_port(self):
        self.__serial_port.flushInput()
        self.__serial_port.flushOutput()
        self.__serial_port.bytesize = self.__bytesize
        self.__serial_port.parity = self.__parity
    
    # reads the answer of the WR after request has been issued
    def read_line(self, timeout = 2):
        response = ''
        start_zeit = time.time()
        try:
            # skip everything until line feed
            while(True):
                response = self.__serial_port.read()
                if response and response[0] == '\n':
                    break
                if time.time() - start_zeit > timeout:
                    return response
            # read until return character
            while(True):
                response += self.__serial_port.read()
                if response and response[-1] == '\r':
                    break
                if time.time() - start_zeit > timeout:
                    return response
        except serial.SerialException as e:
            log("RS45 problem while reading from WR")
        return response
      
    # checks checksum in type message
    def type_valid(self, typ_string):
        if len(typ_string) != 15: # so lang sind meine typen normalerweise
            if DEBUG_ENABLED:
                log("Read type message with invalid length. message is: " + typ_string + " length was: " + str(len(typ_string)))
            return False
        summe = 0
        for i in range(1, len(typ_string) - 2): # 2. zeichen von hinten ist pruefsumme bei mir
            summe += ord(typ_string[i])
        if ord(typ_string[-2]) != summe % 256:
            if DEBUG_ENABLED:
                log("Read invalid type message: " + typ_string)
            return False
        return True

    # checks checksum in data message
    def data_valid(self, data_string):
        if len(data_string) != 66: # so lang sind meine daten normalerweise
            if DEBUG_ENABLED:
                log("Read data message with invalid length. message is: " + data_string + " length was: " + str(len(data_string)))
            return False
        summe = 0
        for i in range(1, len(data_string) - 9): # 9. zeichen von hinten ist pruefsumme bei mir
            summe += ord(data_string[i])
        if ord(data_string[-9]) != summe % 256:
            if DEBUG_ENABLED:
                log("Read invalid data message: " + data_string)
            return False
        return True
    
    # returns the type message or None
    def request_type(self):
        try:
            self.__serial_port.write("#" + "{0:02d}".format(self.__bus_id) + "9\r")
            self.__serial_port.flush()
        except serial.SerialException as e:
            log("RS45 problem while requesting WR type")
        typ = self.read_line()
        if self.type_valid(typ):
            return typ
        return None
        
    # returns the data message or None
    def request_data(self):
        try:
            self.__serial_port.write("#" + "{0:02d}".format(self.__bus_id) + "0\r")
            self.__serial_port.flush()
        except serial.SerialException as e:
            log("RS45 problem while requesting WR data") 
        daten = self.read_line()
        if self.data_valid(daten):
            return daten
        return None
            
    # returns True / False indicating whether that device exists on the bus (if it answered valid data) and adds model name to WR object (in case of valid response)
    def does_exist(self):
        log("Running discovery on ID " + str(self.__bus_id))
        typ = self.request_type()
        if typ:
            if DEBUG_ENABLED:
                log("Device %d answered on type request %s " % (self.__bus_id, typ))
            self.__model = typ.split()[1]
            return True
        # if it didn't answer on type request it gets another chance and is asked for data this time ...
        time.sleep(0.33)
        data = self.request_data()
        if data:
            if DEBUG_ENABLED:
                log("Device %d answered on data request %s " % (self.__bus_id, data))
            self.__model = data.split()[-1]
            return True
        return False
        
        
        
class SmartMeter():
    def __init__(self, serial_port):
        self.__serial_port = serial_port
        self.__model = "VSM-102"
        self.__bytesize = serial.SEVENBITS
        self.__parity = serial.PARITY_EVEN
        self.__start_regex = re.compile("1-0:1\\.8\\.0\\*255")  # OBIS for total meter reading
        self.__end_regex = re.compile("0-0:96\\.1\\.255\\*255") # OBIS for serial number
        self.setup_serial_port()
    
    # getters for member variables
    
    @property
    def model(self):
        return self.__model
        
    def setup_serial_port(self):
        self.__serial_port.flushInput()
        self.__serial_port.flushOutput()
        self.__serial_port.bytesize = self.__bytesize
        self.__serial_port.parity = self.__parity
    

    def data_valid(self, data_string):
        # in my test there where 11 elements
        if len(data_string.split("\n")) != 11:
            if DEBUG_ENABLED:
                log("Read smart meter datagram with invalid structure. datagram is: " + data_string + "number of elements (should be 11): " + len(data_string.split("\n")))
            return False
        return True
        
    def read_datagram(self, timeout = 2):
        data_buffer = ''
        response = ''
        start_zeit = time.time()
        try:
            # skip everything until 1-0:1.8.0*255 arrives the beginning of total meter reading)
            while(True):
                data_buffer += self.__serial_port.readline()
                match = self.__start_regex.search(data_buffer)
                if match:
                    response = data_buffer[match.start(0):] # accept everything from the beginning of the eyecatcher
                    break
                if time.time() - start_zeit > timeout:
                    return response
            # read until 0-0:96.1.255*255 arrives (indicates the last line containing the serial number)
            while(True):
                response += self.__serial_port.readline()
                match = self.__end_regex.search(response)
                if match:
                    break
                if time.time() - start_zeit > timeout:
                    return response
        except serial.SerialException as e:
            log("RS45 problem while reading from WR")
        return response
        
    # returns the data message or None
    def request_data(self):
        try:
            self.__serial_port.write("/?!\r\n")
            self.__serial_port.flush()
            time.sleep(0.2)
            self.__serial_port.write(chr(6) + "050\r\n")
            self.__serial_port.flush()
        except serial.SerialException as e:
            log("RS45 problem while requesting smart meter data") 
        daten = self.read_datagram()
        if self.data_valid(daten):
            return daten
        return None
            

    # returns True / False indicating whether that device exists on the bus (if it answered valid data)
    def does_exist(self):
        log("discovering smart meter")
        data = self.request_data()
        if data and self.data_valid(data):
            return True
        log("smart meter answered badly on data request: %s " % (data))
        return False

class AggregationItem():
    def __init__(self, data = None, time = None):    
        self.data = [] if data == None else data # this is going to hold the data as psycopg2's execute() expects it
        self.timestamp = datetime.now(tzlocal()) if time == None else time # this is going to hold the exact datetime when self.data was last updated
    
    # debugging helpers :)
    def __str__(self):
        return "time: " + str(self.timestamp) + " data: " + str(self.data)

    def __repr__(self):
        return self.__str__()


class Aggregation():
    def __init__(self):
        self.WRminute = {} # dictionary for the minutely inverter data, e.g by bus_id (should be of type AggregationItem so that makeExecutemanyDataStructure() is able to operate on it)
        self.WRhour = {}
        self.WRday = {} # inverter day does not need to be aggregated as it is contained precisely in every inverter message. But I still need to save it to be able to do the hacky stuff and pass it to execute()
        self.WRmonth = {}
        self.WRyear = {}
        self.WRmaxima = {}
        
        # now this is hacky:
        # those additional AggregationItem dictionaries should make the inverter month and year aggregation more accurate:
        # There is a precise daily production counter in every inverter message (which gets stored in charts_solarentryday).
        # In order to aggregate for month and year, I want to add the values excluding the current day, to the reading for that current day (as this reading is constatnly rising thougout the day).
        # This means that whenever a day passes, the production of this day must be added to the 'day before' values, but only if the new date is in the same period.
        # So I'm going to use that data part of the AggregationItem 
        #     to store just the Decimal holding the value 
        #     (no list that execute() could deal with)
        #     and the timestamp 
        #     in order to later find out whether the corresponding period 
        #     has passed and the value can be zeroed again.
        # Puh, database triggers doing sums were not that bad I guess ... 
        self.WRmonthDayBefore = {}
        self.WRyearDayBefore = {}
        
        self.SmartMeterMinute = None # should be of type AggregationItem
        self.SmartMeterHour = None
        self.SmartMeterDay = None
        self.SmartMeterMonth = None
        self.SmartMeterYear = None
        self.SmartMeterMaximum = None
        
        self.Eigenverbrauch = None # should be of type AggregationItem
    
    # this method takes a db cursor and the bus id and retrieves the latest data from the database to initialize inverter fields
    def fetchInitialWRdata(self, db_cursor, busID):
        # I don't want to use Django here because the daemon should be able to operate anywhere without django installed
        # start with minute
        try:
            thisMinute = datetime.now(tzlocal()) + relativedelta(second=0, microsecond=0) # this is localtime (with correct timezone as there is in the database)
            self.WRminute[busID] = AggregationItem([thisMinute, datetime.now(tzlocal()), busID, Decimal(0)])
            db_cursor.execute('SELECT time, exacttime, device_id, "lW" FROM charts_solarentryminute WHERE device_id = %s AND time = %s LIMIT 1;', [busID, thisMinute])
            if db_cursor.rowcount == 0:
                if DEBUG_ENABLED:
                    log("There is no matching minutely inverter data for bus id " + str(busID))
            else:
                minutely = db_cursor.fetchone()
                if DEBUG_ENABLED:
                    log("There is relevant data for this minute: " + ", ".join([str(x) for x in minutely]))
                self.WRminute[busID] = AggregationItem(list(minutely), minutely[1]) # list() because the database gives me a tuple but I want to update it later
        except Exception as ex:
            log("Exception while loading minutely inverter data: " + str(ex))
            sys.exit(1) # I really want this to work
        
        # hour
        try:
            thisHour = datetime.now(tzlocal()) + relativedelta(minute=0, second=0, microsecond=0)
            self.WRhour[busID] = AggregationItem([thisHour, busID, Decimal(0)])
            db_cursor.execute('SELECT time, device_id, "lW" FROM charts_solarentryhour WHERE device_id = %s AND time = %s LIMIT 1;', [busID, thisHour])
            if db_cursor.rowcount == 0:
                if DEBUG_ENABLED:
                    log("There is no matching hourly inverter data for bus id " + str(busID))
            else:
                hourly = db_cursor.fetchone()
                if DEBUG_ENABLED:
                    log("There is relevant inverter data for this hour: " + ", ".join([str(x) for x in hourly]))
                self.WRhour[busID] = AggregationItem(list(hourly))
        except Exception as ex:
            log("Exception while loading hourly inverter data: " + str(ex))
            sys.exit(1)
        
        # day
        try:
            thisDay = datetime.now(tzlocal()).date()
            self.WRday[busID] = AggregationItem([thisDay, busID, Decimal(0)])
            db_cursor.execute('SELECT time, device_id, "lW" FROM charts_solarentryday WHERE device_id = %s AND time = %s LIMIT 1;', [busID, thisDay])
            if db_cursor.rowcount == 0:
                if DEBUG_ENABLED:
                    log("There is no matching daily inverter data for bus id " + str(busID))
            else:
                daily = db_cursor.fetchone()
                if DEBUG_ENABLED:
                    log("There is relevant inverter data for this day: " + ", ".join([str(x) for x in daily]))
                self.WRday[busID] = AggregationItem(list(daily))
        except Exception as ex:
            log("Exception while loading daily inverter data: " + str(ex))
            sys.exit(1)
        
        # hacky dayBefore stuff
        try:
            # let's do the month thing first
            thisDay = datetime.now(tzlocal()).date()
            thisMonth = (datetime.now(tzlocal()) + relativedelta(day=1)).date()
            self.WRmonthDayBefore[busID] = AggregationItem(Decimal(0))
            db_cursor.execute('SELECT SUM("lW") FROM charts_solarentryday WHERE "time" >= %s AND time < %s AND device_id = %s;', [thisMonth, thisDay, busID])
            if db_cursor.rowcount == 0:
                if DEBUG_ENABLED:
                    log("There is no matching sum for the days in the current month for bus id " + str(busID))
            else:
                hackyMonth = db_cursor.fetchone()
                if hackyMonth[0] != None:
                    if DEBUG_ENABLED:
                        log("There is a sum for all days except today of this month: " + str(hackyMonth[0]))
                    self.WRmonthDayBefore[busID] = AggregationItem(hackyMonth[0])
                else:
                    if DEBUG_ENABLED:
                        log("There is no matching sum for the days in the current month for bus id " + str(busID))
        except Exception as ex:
            log("Exception while loading sum for current month except today: " + str(ex))
            sys.exit(1)
        try:
            # now do the year thing similarly
            thisDay = datetime.now(tzlocal()).date()
            thisYear = (datetime.now(tzlocal()) + relativedelta(month=1, day=1)).date()
            self.WRyearDayBefore[busID] = AggregationItem(Decimal(0))
            db_cursor.execute('SELECT SUM("lW") FROM charts_solarentryday WHERE "time" >= %s AND time < %s AND device_id = %s;', [thisYear, thisDay, busID])
            if db_cursor.rowcount == 0:
                if DEBUG_ENABLED:
                    log("There is no matching sum for the days in the current year for bus id " + str(busID))
            else:
                hackyYear = db_cursor.fetchone()
                if hackyYear[0] != None:
                    if DEBUG_ENABLED:
                        log("There is a sum for all days except today of this year " + str(hackyYear[0]))
                    self.WRyearDayBefore[busID] = AggregationItem(hackyYear[0])
                else: # sum was None
                    if DEBUG_ENABLED:
                        log("There is no matching sum for the days in the current year for bus id " + str(busID))
        except Exception as ex:
            log("Exception while loading sum for current year except today: " + str(ex))
            sys.exit(1)
        
        # end of hacky dayBefore stuff
        # month
        try:
            thisMonth = (datetime.now(tzlocal()) + relativedelta(day=1)).date() # local time zone corrected date (I hope so!)
            self.WRmonth[busID] = AggregationItem([thisMonth, busID, Decimal(0)])
            db_cursor.execute('SELECT time, device_id, "lW" FROM charts_solarentrymonth WHERE device_id = %s AND time = %s LIMIT 1;', [busID, thisMonth])
            if db_cursor.rowcount == 0:
                if DEBUG_ENABLED:
                    log("There is no matching monthly inverter data for bus id " + str(busID))
            else:
                monthly = db_cursor.fetchone()
                if DEBUG_ENABLED:
                    log("There is relevant inverter data for this month: " + ", ".join([str(x) for x in monthly]))
                self.WRmonth[busID] = AggregationItem(list(monthly))
        except Exception as ex:
            log("Exception while loading monthly inverter data: " + str(ex))
            sys.exit(1)
        
        # year
        try:
            thisYear = (datetime.now(tzlocal()) + relativedelta(month=1, day=1)).date()
            self.WRyear[busID] = AggregationItem([thisYear, busID, Decimal(0)])
            db_cursor.execute('SELECT time, device_id, "lW" FROM charts_solarentryyear WHERE device_id = %s AND time = %s LIMIT 1;', [busID, thisYear])
            if db_cursor.rowcount == 0:
                if DEBUG_ENABLED:
                    log("There is no matching yearly inverter data for bus id " + str(busID))
            else:
                yearly = db_cursor.fetchone()
                if DEBUG_ENABLED:
                    log("There is relevant inverter data for this year: " + ", ".join([str(x) for x in yearly]))
                self.WRyear[busID] = AggregationItem(list(yearly))
        except Exception as ex:
            log("Exception while loading yearly inverter data: " + str(ex))
            sys.exit(1)
        
        # maximum
        try:
            thisDay = datetime.now(tzlocal()).date()
            self.WRmaxima[busID] = AggregationItem([thisDay, busID, Decimal(0), datetime.now(tzlocal())])
            db_cursor.execute('SELECT time, device_id, "lW", exacttime FROM charts_solardailymaxima WHERE device_id = %s AND time = %s LIMIT 1;', [busID, thisDay])
            if db_cursor.rowcount == 0:
                if DEBUG_ENABLED:
                    log("There is no matching maximum inverter data for bus id " + str(busID))
            else:
                maximum = db_cursor.fetchone()
                if DEBUG_ENABLED:
                    log("There is relevant maximum inverter data for today: " + ", ".join([str(x) for x in maximum]))
                self.WRmaxima[busID] = AggregationItem(list(maximum))
        except Exception as ex:
            log("Exception while loading maximum inverter data: " + str(ex))
            sys.exit(1)
    
    # this method takes a db cursor and retrieves the latest data from the database to initialize smartmeter fields
    def fetchInitialSmartMeterData(self, db_cursor):
        # minute
        try:
            thisMinute = datetime.now(tzlocal()) + relativedelta(second=0, microsecond=0) # this is localtime (with correct timezone as there is in the database)
            self.SmartMeterMinute = AggregationItem([thisMinute, datetime.now(tzlocal()), Decimal(0), Decimal(0), Decimal(0), Decimal(0)])
            db_cursor.execute('SELECT "time", exacttime, reading, phase1, phase2, phase3 FROM charts_smartmeterentryminute WHERE time = %s LIMIT 1;', [thisMinute])
            if db_cursor.rowcount == 0:
                if DEBUG_ENABLED:
                    log("There is no matching minutely data for smart meter")
            else:
                minutely = db_cursor.fetchone()
                if DEBUG_ENABLED:
                    log("There is relevant smart meter data for this minute: " + ", ".join([str(x) for x in minutely])) 
                self.SmartMeterMinute = AggregationItem(list(minutely), minutely[1])
        except Exception as ex:
            log("Exception while loading minutely smart meter data: " + str(ex))
            sys.exit(1)
        
        # hour
        try:
            thisHour = datetime.now(tzlocal()) + relativedelta(minute=0, second=0, microsecond=0)
            self.SmartMeterHour = AggregationItem([thisHour, Decimal(0), Decimal(0), Decimal(0), Decimal(0)])
            db_cursor.execute('SELECT "time", reading, phase1, phase2, phase3 FROM charts_smartmeterentryhour WHERE time = %s LIMIT 1;', [thisHour])
            if db_cursor.rowcount == 0:
                if DEBUG_ENABLED:
                    log("There is no matching hourly data for smart meter")
            else:
                hourly = db_cursor.fetchone()
                if DEBUG_ENABLED:
                    log("There is relevant smart meter data for this hour: " + ", ".join([str(x) for x in hourly]))
                self.SmartMeterHour = AggregationItem(list(hourly))
        except Exception as ex:
            log("Exception while loading hourly smart meter data: " + str(ex))
            sys.exit(1)
        
        # day
        try:
            thisDay = datetime.now(tzlocal()).date()
            self.SmartMeterDay = AggregationItem([thisDay, Decimal(0), Decimal(0), Decimal(0), Decimal(0)])
            db_cursor.execute('SELECT "time", reading, phase1, phase2, phase3 FROM charts_smartmeterentryday WHERE time = %s LIMIT 1;', [thisDay])
            if db_cursor.rowcount == 0:
                if DEBUG_ENABLED:
                    log("There is no matching daily data for smart meter")
            else:
                daily = db_cursor.fetchone()
                if DEBUG_ENABLED:
                    log("There is relevant smart meter data for this day: " + ", ".join([str(x) for x in daily]))
                self.SmartMeterDay = AggregationItem(list(daily))
        except Exception as ex:
            log("Exception while loading daily smart meter data: " + str(ex))
            sys.exit(1)
        
        # month
        try:
            thisMonth = (datetime.now(tzlocal()) + relativedelta(day=1)).date() # local time zone corrected date (I hope so!)
            self.SmartMeterMonth = AggregationItem([thisMonth, Decimal(0), Decimal(0), Decimal(0), Decimal(0)])
            db_cursor.execute('SELECT "time", reading, phase1, phase2, phase3 FROM charts_smartmeterentrymonth WHERE time = %s LIMIT 1;', [thisMonth])
            if db_cursor.rowcount == 0:
                if DEBUG_ENABLED:
                    log("There is no matching monthly data for smart meter")
            else:
                monthly = db_cursor.fetchone()
                if DEBUG_ENABLED:
                    log("There is relevant smart meter data for this month: " + ", ".join([str(x) for x in monthly]))
                self.SmartMeterMonth = AggregationItem(list(monthly))
        except Exception as ex:
            log("Exception while loading monthly smart meter  data: " + str(ex))
            sys.exit(1)
        
        # year
        try:
            thisYear = (datetime.now(tzlocal()) + relativedelta(month=1, day=1)).date()
            self.SmartMeterYear = AggregationItem([thisYear, Decimal(0), Decimal(0), Decimal(0), Decimal(0)])
            db_cursor.execute('SELECT "time", reading, phase1, phase2, phase3 FROM charts_smartmeterentryyear WHERE time = %s LIMIT 1;', [thisYear])
            if db_cursor.rowcount == 0:
                if DEBUG_ENABLED:
                    log("There is no matching yearly data for smart meter")
            else:
                yearly = db_cursor.fetchone()
                if DEBUG_ENABLED:
                    log("There is relevant smart meter data for this year: " + ", ".join([str(x) for x in yearly]))
                self.SmartMeterYear = AggregationItem(list(yearly))
        except Exception as ex:
            log("Exception while loading yearly smart meter data: " + str(ex))
            sys.exit(1)
        
        # maximum
        try:
            thisDay = datetime.now(tzlocal()).date()
            self.SmartMeterMaximum = AggregationItem([thisDay, datetime.now(tzlocal()), Decimal(0)])
            db_cursor.execute('SELECT "time", exacttime, maximum FROM charts_smartmeterdailymaxima WHERE time = %s LIMIT 1;', [thisDay])
            if db_cursor.rowcount == 0:
                if DEBUG_ENABLED:
                    log("There is no matching maximum data for smart meter")
            else:
                maximum = db_cursor.fetchone()
                if DEBUG_ENABLED:
                    log("There is relevant maximum smart meter data for this day: " + ", ".join([str(x) for x in maximum]))
                self.SmartMeterMaximum = AggregationItem(list(maximum))
        except Exception as ex:
            log("Exception while loading maximum smart meter data: " + str(ex))
            sys.exit(1)
    
    # this method takes a db cursor and retrieves the latest data from the database to initialize smartmeter fields
    def fetchInitialEigenverbrauchData(self, db_cursor):
        try:
            thisDay = datetime.now(tzlocal()).date()
            self.Eigenverbrauch = AggregationItem([thisDay, Decimal(0)])
            db_cursor.execute('SELECT "time", eigenverbrauch FROM charts_eigenverbrauch WHERE time = %s LIMIT 1;', [thisDay])
            if db_cursor.rowcount == 0:
                if DEBUG_ENABLED:
                    log("There is no matching eigenverbrauch")
            else:
                eigenverbrauch = db_cursor.fetchone()
                if DEBUG_ENABLED:
                    log("There is relevant eigenverbrauch data for this day: " + ", ".join([str(x) for x in eigenverbrauch]))
                self.Eigenverbrauch = AggregationItem(list(eigenverbrauch))
        except Exception as ex:
            log("Exception while loading eigenverbrauch: " + str(ex))
            sys.exit(1)
            
        
    # makes a executemany compliant nested array structure from dictionary of AggregationItems
    def makeExecutemanyDataStructure(self, dictionaryOfAggregationItems):
        return [item.data for item in dictionaryOfAggregationItems.values()]
    
    # aggregates daily eigenverbrauch
    # expects input to be Decimal
    def updateEigenverbrauch(self, sumProduced, sumUsed):
        now = datetime.now(tzlocal())
        eigenverbrauch = sumUsed if sumProduced > sumUsed else sumProduced
        thisDay = now.date()
        increment = eigenverbrauch * Decimal((now - self.Eigenverbrauch.timestamp).total_seconds()) / 3600 # energy in Wh since the last update
        if self.Eigenverbrauch.timestamp.date() == thisDay:
            self.Eigenverbrauch.data[1] += increment # add to current day's eigenverbrauch (the time is still valid)
        else:        
            self.Eigenverbrauch.data[0] = thisDay    # we have a new day
            self.Eigenverbrauch.data[1] = increment  # first value of today
        self.Eigenverbrauch.timestamp = now
    
    # aggregates minutely, hourly, daily, monthly and yearly data
    # expects input (except busID and now ehich are int and datetime) to be Decimal
    def updateInverter(self, busID, now, lW, dailyTotal):
        # prepare timestamps
        thisMinute = now + relativedelta(second=0, microsecond=0) # this is localtime (with correct timezone as there is in the database)
        thisHour = now + relativedelta(minute=0, second=0, microsecond=0)
        thisDay = now.date()
        thisMonth = (now + relativedelta(day=1)).date() # local time zone corrected date (I hope so!)
        thisYear = (now + relativedelta(month=1, day=1)).date()
        
        # care about the hacky day before stuff (needs to be done before self.WRday[busID] gets updated)
        oldMonthlyAggregationDate = self.WRmonthDayBefore[busID].timestamp.date()
        if oldMonthlyAggregationDate != thisDay: # I only expect it to be either exatly the same or at most one day off but I'm too lazy to really assert that
            self.WRmonthDayBefore[busID].data += self.WRday[busID].data[2] # add yesterdays value to the monthly accumulated day- before- sum
            if oldMonthlyAggregationDate < thisMonth:
                self.WRmonthDayBefore[busID].data = Decimal(0) # clear the montly day-before-sum when the month changes
        self.WRmonthDayBefore[busID].timestamp = now
        oldYearlyAggregationDate = self.WRyearDayBefore[busID].timestamp.date()
        if oldMonthlyAggregationDate != thisDay: # actually, this should be in sync with the hacky monthly stuff (as all aggregated values use the same now- timestamp)
            self.WRyearDayBefore[busID].data += self.WRday[busID].data[2]
            if oldYearlyAggregationDate < thisYear:
                self.WRyearDayBefore[busID].data = Decimal(0)
        self.WRyearDayBefore[busID].timestamp = now
        
        # OK, hacky things are done now let's start with the minute aggregation (data order: time, exacttime, device_id, "lW")
        if self.WRminute[busID].data[0] < thisMinute: # if a new minute has started estimate the energy for this minute by expecting that the same power is drawn for 60 seconds
            self.WRminute[busID].data[3] = lW / 60 # the consumed energy in this minute assuming that the consumption stays constant
        else: # we already have an estimate for this minute
            timePassedInThisMinute = Decimal((now - self.WRminute[busID].timestamp).total_seconds()) # self.WRminute[busID].timestamp should be the same as self.WRminute[busID].data[1] (which is exacttime) but requires one array access less!
            timeLeftInThisMinute = 60 - timePassedInThisMinute
            self.WRminute[busID].data[3] = (self.WRminute[busID].data[3] * timePassedInThisMinute + (lW / 60) * timeLeftInThisMinute) / 60 # let's continue our estimation with the current value (until we get another update). Therefore, make a weighted sum based on time.
        # fill in the remaining fields that need to be updated the same, no matter whether it is the same minute or a new one
        self.WRminute[busID].data[0] = thisMinute
        self.WRminute[busID].data[1] = now # this entry exists for historical reasons and I'm affraid of removing it :(
        self.WRminute[busID].timestamp = now
        
        # the hour aggregation. data order: time, device_id, "lW"
        # this might be inaccurate because of rounding (decimal is accurate to 28 digits by default).
        # Maybe I'll use a trigger to iron that out for the day before in the database every midnight but I don't think the difference appears in the database at all because the precision is only 3 digits there)
        if self.WRhour[busID].data[0] < thisHour: # if a new hour has started
            self.WRhour[busID].data[2] = Decimal(0) # clear aggregation if a new hour has started
        timePassedSinceLastHourUpdate = Decimal((now - self.WRhour[busID].timestamp).total_seconds())
        if timePassedSinceLastHourUpdate > 10 * Decimal(RLogDaemon.DELAY): # in case the inverter starts in the morning with a non-zero reading we would account the entire night for it which is wrong
            timePassedSinceLastHourUpdate = Decimal(RLogDaemon.DELAY) # so we limit it to one polling interval
        self.WRhour[busID].data[0] = thisHour
        self.WRhour[busID].data[2] += lW * timePassedSinceLastHourUpdate / 3600  # add the the consumed energy since the last update
        self.WRhour[busID].timestamp = now
        
        # day 'aggregation'. data order: time, device_id, "lW" (it is not really aggregation as we read the aggregated value every time and don't need to compute anything)
        self.WRday[busID].data[0] = thisDay
        self.WRday[busID].data[2] = dailyTotal
        self.WRday[busID].timestamp = now # actually nobody cares about that (delete it in case of performance issues :) )
        
        # month agregation. data order: time, device_id, "lW" (we are using hacky day before stuff here)
        self.WRmonth[busID].data[0] = thisMonth
        self.WRmonth[busID].data[2] = self.WRmonthDayBefore[busID].data + self.WRday[busID].data[2] # add the accumulation until (and including yesterday) and the current daily total
        self.WRmonth[busID].timestamp = now
        
        # year agregation. data order: time, device_id, "lW"
        self.WRyear[busID].data[0] = thisYear
        self.WRyear[busID].data[2] = self.WRyearDayBefore[busID].data + self.WRday[busID].data[2] # add the accumulation until (and including yesterday) and the current daily total
        self.WRyear[busID].timestamp = now
        
        # so, finally the maximum. data order: time, device_id, "lW", exacttime
        if self.WRmaxima[busID].data[0] < thisDay: # if a new day has started
            self.WRmaxima[busID].data[0] = thisDay
            self.WRmaxima[busID].data[2] = Decimal(0)           
            self.WRmaxima[busID].data[3] = now
            self.WRmaxima[busID].timestamp = now # actualy unused (remove this assignment if you want to save some cycles but I leave it here for completeness)
        if lW > self.WRmaxima[busID].data[2]:
            self.WRmaxima[busID].data[0] = thisDay # this should not be necessary as the first condition MUST hold once a day
            self.WRmaxima[busID].data[2] = lW
            self.WRmaxima[busID].data[3] = now
            self.WRmaxima[busID].timestamp = now
    
    # aggregates minutely, hourly, daily, monthly and yearly data
    # expects input (except budID) to be Decimal
    def updateSmartMeter(self, now, reading, phase1, phase2, phase3):
        # prepare timestamps
        thisMinute = now + relativedelta(second=0, microsecond=0) # this is localtime (with correct timezone as there is in the database)
        thisHour = now + relativedelta(minute=0, second=0, microsecond=0)
        thisDay = now.date()
        thisMonth = (now + relativedelta(day=1)).date() # local time zone corrected date (I hope so!)
        thisYear = (now + relativedelta(month=1, day=1)).date()
        
        # start with the minute aggregation (data order: "time", exacttime, reading, phase1, phase2, phase3)
        if self.SmartMeterMinute.data[0] < thisMinute: # if a new minute has started estimate the energy for this minute by expecting that the same power is drawn for 60 seconds
            self.SmartMeterMinute.data[3] = phase1 / 60 # the consumed energy in this minute assuming that the consumption stays constant
            self.SmartMeterMinute.data[4] = phase2 / 60 
            self.SmartMeterMinute.data[5] = phase3 / 60 
        else: # we already have an estimate for this minute
            timePassedInThisMinute = Decimal((now - self.SmartMeterMinute.timestamp).total_seconds()) # self.WRminute[busID].timestamp should be the same as self.WRminute[busID].data[1] (which is exacttime) but requires one array access less!
            timeLeftInThisMinute = 60 - timePassedInThisMinute
            self.SmartMeterMinute.data[3] = (self.SmartMeterMinute.data[3] * timePassedInThisMinute + (phase1 / 60) * timeLeftInThisMinute) / 60 # let's continue our estimation with the current value (until we get another update). Therefore, make a weighted sum based on time.
            self.SmartMeterMinute.data[4] = (self.SmartMeterMinute.data[4] * timePassedInThisMinute + (phase2 / 60) * timeLeftInThisMinute) / 60
            self.SmartMeterMinute.data[5] = (self.SmartMeterMinute.data[5] * timePassedInThisMinute + (phase3 / 60) * timeLeftInThisMinute) / 60
        # fill in the remaining fields that need to be updated the same, no matter whether it is the same minute or a new one
        self.SmartMeterMinute.data[0] = thisMinute
        self.SmartMeterMinute.data[1] = now # actually not used any more because my datastructur has an exact timestamp but says in here for historical reasons
        self.SmartMeterMinute.data[2] = reading
        self.SmartMeterMinute.timestamp = now
        
        timePassedSinceLastUpdate = Decimal((now - self.SmartMeterHour.timestamp).total_seconds()) # the time passed is the same for all aggregation periods.
        # Therefore, we save us from computing it from every AggregationItem's timestamp as it would be the same every time and take the hourly as example.
        # We also don't apply the same sanity check to the passed time because we expect it to run continuously 
        # (and if not then we'd just account for the stuff we missed (but unfortunately write it in only one inverval))
        phase1Increment = phase1 * timePassedSinceLastUpdate / 3600 # the energy in Wh computed from timePassedSinceLastUpdate seconds with phase1 Watts power consumption
        phase2Increment = phase2 * timePassedSinceLastUpdate / 3600
        phase3Increment = phase3 * timePassedSinceLastUpdate / 3600
        
        # the hour aggregation. data order: "time", reading, phase1, phase2, phase3
        # this might be inaccurate because of rounding (decimal is accurate to 28 digits by default).
        # Maybe I'll use a trigger to iron that out for the day before in the database every midnight but I don't think the difference appears in the database at all because the precision is only 3 digits there)
        # And the worst thing to know is that is is accumulating errors and I can't make up for it (only thing I have is a constantly increasing total reading for all phases together)
        if self.SmartMeterHour.data[0] < thisHour: # if a new hour has started
            self.SmartMeterHour.data[2] = Decimal(0) # clear aggregation if a new hour has started
            self.SmartMeterHour.data[3] = Decimal(0)
            self.SmartMeterHour.data[4] = Decimal(0)
        self.SmartMeterHour.data[0] = thisHour # this could also be done only once in the if clause above
        self.SmartMeterHour.data[1] = reading
        self.SmartMeterHour.data[2] += phase1Increment # add the the consumed energy since the last update
        self.SmartMeterHour.data[3] += phase2Increment
        self.SmartMeterHour.data[4] += phase3Increment
        self.SmartMeterHour.timestamp = now
        
        # the day aggregation. data order: "time", reading, phase1, phase2, phase3
        # same thougths here (and on the following periods) as stated above
        if self.SmartMeterDay.data[0] < thisDay:
            self.SmartMeterDay.data[2] = Decimal(0)
            self.SmartMeterDay.data[3] = Decimal(0)
            self.SmartMeterDay.data[4] = Decimal(0)
        self.SmartMeterDay.data[0] = thisDay
        self.SmartMeterDay.data[1] = reading
        self.SmartMeterDay.data[2] += phase1Increment
        self.SmartMeterDay.data[3] += phase2Increment
        self.SmartMeterDay.data[4] += phase3Increment
        self.SmartMeterDay.timestamp = now # acutally unused as the timePassedSinceLastUpdate is computed from the hourly period only (so this can be remoced but i keep it for completeness)
        
        # the month aggregation. data order: "time", reading, phase1, phase2, phase3
        if self.SmartMeterMonth.data[0] < thisMonth:
            self.SmartMeterMonth.data[2] = Decimal(0)
            self.SmartMeterMonth.data[3] = Decimal(0)
            self.SmartMeterMonth.data[4] = Decimal(0)
        self.SmartMeterMonth.data[0] = thisMonth 
        self.SmartMeterMonth.data[1] = reading
        self.SmartMeterMonth.data[2] += phase1Increment
        self.SmartMeterMonth.data[3] += phase2Increment
        self.SmartMeterMonth.data[4] += phase3Increment
        self.SmartMeterMonth.timestamp = now
        
        # the year aggregation. data order: "time", reading, phase1, phase2, phase3
        if self.SmartMeterYear.data[0] < thisMonth:
            self.SmartMeterYear.data[2] = Decimal(0)
            self.SmartMeterYear.data[3] = Decimal(0)
            self.SmartMeterYear.data[4] = Decimal(0)
        self.SmartMeterYear.data[0] = thisMonth 
        self.SmartMeterYear.data[1] = reading
        self.SmartMeterYear.data[2] += phase1Increment
        self.SmartMeterYear.data[3] += phase2Increment
        self.SmartMeterYear.data[4] += phase3Increment
        self.SmartMeterYear.timestamp = now
        
        # so, finally the maximum. data order: "time", exacttime, maximum
        if self.SmartMeterMaximum.data[0] < thisDay: # if a new day has started
            self.SmartMeterMaximum.data[0] = thisDay
            self.SmartMeterMaximum.data[1] = now
            self.SmartMeterMaximum.data[2] = Decimal(0)
            self.SmartMeterMaximum.timestamp = now # actualy unused (remove this assignment if you want to save some cycles but I leave it here for completeness)
        totalConsumption = phase1 + phase2 + phase3 # this was computed as sumUsed before so it might be faster to pass it as parameter instead of calculating it here again
        if totalConsumption > self.SmartMeterMaximum.data[2]:
            self.SmartMeterMaximum.data[0] = thisDay # this should not be necessary as the first condition MUST hold once a day
            self.SmartMeterMaximum.data[1] = now
            self.SmartMeterMaximum.data[2] = totalConsumption
            self.SmartMeterMaximum.timestamp = now
        
class RLogDaemon(Daemon):
    KWHPERRING = None
    NEXTRING = None
    SOUND = None
    DELAY = None
    BELLCOUNTER = Decimal(0)
    MAX_BUS_PARTICIPANTS = None
    DISCOVERY_COUNT = None
    DEBUG_INVERTER_PORT = ''
    DEBUG_SMARTMETER_PORT = ''

    def __init__(self, pidfile):
        super(RLogDaemon, self).__init__(pidfile)
        self._smart_meter_serial_port = None
        self._WR_serial_port = None
        self._slaves = {}
        self._mqttPublisher = None
#        self._db_connection = sqlite3.connect(DATABASE)
        self._db_connection = None
        self._db_cursor = None
        self._current_discovery_id = 1
        self._discovery_credit = 0
        self._smart_meter = None
        self._smart_meter_enabled = False
        self._smart_meter_found = False
        self._eigenverbrauchLastSaved = time.time()
        self._aggregator = Aggregation();
        
        self._reading_regex = re.compile("1-0:1\\.8\\.0\\*255\\(([0-9]+\\.[0-9]+)\\*kWh\\)")          # 1-0:1.8.0*255(00000.00*kWh)
        self._phase1_regex = re.compile("1-0:21\\.7\\.255\\*255\\(([0-9]+\\.[0-9]+)\\*kW\\)")       # 1-0:21.7.255*255(0000.0000*kW)
        self._phase2_regex = re.compile("1-0:41\\.7\\.255\\*255\\(([0-9]+\\.[0-9]+)\\*kW\\)")       # 1-0:41.7.255*255(0000.0000*kW)
        self._phase3_regex = re.compile("1-0:61\\.7\\.255\\*255\\(([0-9]+\\.[0-9]+)\\*kW\\)")       # 1-0:61.7.255*255(0000.0000*kW)
            
#        self._db_cursor.execute('PRAGMA journal_mode=WAL;') 
        log("RLogDaemon created")

    def connectToDatabase(self):
        self._db_connection = psycopg2.connect("dbname='rlog' user='stephan'")
        self._db_cursor = self._db_connection.cursor()
        # self._db_cursor.tzinfo_factory = psycopg2.tz.LocalTimezone # not necessary because the dbms has the time zone set correctly
        log("database conencted")

    def run(self):
        log("daemon running")

        self.connectToDatabase() # necessary to connect here and not earlier in constructor because database connections will not survive daemonization (fork) (at least not when using ip sockets)
        
        self._db_cursor.execute("SELECT * FROM charts_settings WHERE active = TRUE ORDER BY id DESC LIMIT 1;")
        try:
            if self._db_cursor.rowcount > 0:
                sets = self._db_cursor.fetchone()
           	RLogDaemon.KWHPERRING = Decimal(sets[2]) # not sure it is already decimal
           	RLogDaemon.NEXTRING = Decimal(sets[2])
           	RLogDaemon.SOUND = sets[3]
            else:
                 log("no settings in database. using defaults")
                 RLogDaemon.KWHPERRING = Decimal(1)
                 RLogDaemon.NEXTRING = Decimal(1)
                 RLogDaemon.SOUND = "/home/stephan/git/rlog/coin.mp3"
        except Exception as ex:
            log("Couldn't read settings from database. Error was:")
            log(str(type(ex))+str(ex))
        except Error as err:
            log(str(type(err)))

        log("""Using Parameters:
    KWHPERRING: %s
    NEXTRING: %s
    SOUND: %s""" % (RLogDaemon.KWHPERRING, RLogDaemon.NEXTRING, RLogDaemon.SOUND))

        log("starting MQTT")
        try:
            self._mqttPublisher = mqtt.mqtt(broker = MQTT_HOST)
            self._mqttPublisher.startMQTT()
            self._mqttPublisher.publish("/devices/RLog/meta/name", "Rlog", 0, True)
            self._mqttPublisher.publish("/devices/RLog/meta/locationX", LOCATIONX, 0, True)
            self._mqttPublisher.publish("/devices/RLog/meta/locationY", LOCATIONY, 0, True)   
        except Exception as e:
            log("mqtt start problem:" + str(e))
 
        # find the serial ports
        self.discover_devices()
                   
        log("looking for WR")
        self.findWRs()
        
        log("loading eigenverbrauch")
        self._aggregator.fetchInitialEigenverbrauchData(self._db_cursor)
        
        log("starting normal execution")

        while True:
            t1 = time.time()
            self.poll_devices()
            t15 = time.time()
            self.run_discovery_if_required()
            t2 = time.time()
            if DEBUG_ENABLED:
                log("before poll: {0} after poll: {1}  after discovery: {2}".format(t1, t15, t2))
            self.sleep_to_delay(t1, t2)
        else:
            try:
                self._mqttPublisher.stopMQTT()
            except Exception as e:
                log("mqtt stop problem:" + str(e))
            sys.exit(1)
    
    def run_discovery_if_required(self):
        if self._current_discovery_id == None and (self._smart_meter_enabled == False or self._smart_meter_found == True): # there is nothing left to do
            return
            
        self._discovery_credit -= 1
        if DEBUG_ENABLED:
            log("Discovery credit is now: " + str(self._discovery_credit))

        if self._discovery_credit <= 0:
            # find the smart meter if necessary
            if self._smart_meter_found == False and self._smart_meter_enabled == True:
                candidate = SmartMeter(self._smart_meter_serial_port)
                if candidate.does_exist():
                    try:
                        # fake 3 phases as new devices for MQTT
                        self._mqttPublisher.publish("/devices/RLog/controls/" + candidate.model + " (1)/meta/type", "text", 0, True)
                        self._mqttPublisher.publish("/devices/RLog/controls/" + candidate.model + " (2)/meta/type", "text", 0, True)
                        self._mqttPublisher.publish("/devices/RLog/controls/" + candidate.model + " (3)/meta/type", "text", 0, True)
                    except Exception as e:
                        log("Exception while doing MQTT stuff: " + str(e))
                    self._smart_meter_found = True
                    self._smart_meter = candidate
                time.sleep(1)          
                            
        
            # find one missing WR
            if self._current_discovery_id != None:
                missing_wrs = filter(lambda x: x not in self._slaves, range(1, RLogDaemon.MAX_BUS_PARTICIPANTS + 1))
                candidate = WR(self._current_discovery_id, self._WR_serial_port)
                if candidate.does_exist():
                    self._slaves[self._current_discovery_id] = candidate
                    try:
                        self._db_cursor.execute("INSERT INTO charts_device (id, model) VALUES (%s, %s)", (candidate.bus_id, candidate.model)) # actually upserts if exists due to database rule
                        self._db_connection.commit()
                    except psycopg2.OperationalError as ex:
                        log("Database Operational Error!")
                        log(str(type(ex))+str(ex))
                    try:
                        self._mqttPublisher.publish("/devices/RLog/controls/" + candidate.model + " (" + str(candidate.bus_id) + ")/meta/type", "text", 0, True)
                    except Exception as e:
                        log("Exception while doing MQTT stuff: " + str(e))
                    if DEBUG_ENABLED:
                        log("Getting latest data for inverter with ID " + str(candidate.bus_id) + " from database")
                    self._aggregator.fetchInitialWRdata(self._db_cursor, candidate.bus_id)
                if missing_wrs:
                    if missing_wrs.index(self._current_discovery_id) == len(missing_wrs) - 1: # if we looked for the last one
                        self._current_discovery_id = missing_wrs[0]
                    else:
                        self._current_discovery_id = missing_wrs[missing_wrs.index(self._current_discovery_id) + 1]
                else:
                    self._current_discovery_id = None
                self._discovery_credit = RLogDaemon.DISCOVERY_COUNT

    def sleep_to_delay(self, t1, t2):
        if DEBUG_ENABLED:
            log("poll delay is : " + str(RLogDaemon.DELAY))
        sleepduration = RLogDaemon.DELAY - (t2 - t1)
        if sleepduration <= 0:
          log("Timing problem (discovery?): %f" % sleepduration)
        else:
          time.sleep(sleepduration)

    # try all device starting with DEVICE_NAME_BASE and try to talk to the smart meter if it exists (if smart meter is enabled).
    # if smart meter is found (or smartmeter is not enabled) try the first device starting with DEVICE_NAME_BASE and assume it is the rs485 adapter for the WR (make sure to skip smart meter adapter if present)
    def discover_devices(self):
        smart_meter_device = -1 # to be excluded in the second run of 'for device_id in range(0, 100):'
        if self._smart_meter_enabled:
            if RLogDaemon.DEBUG_SMARTMETER_PORT:
                self._smart_meter_serial_port = serial.Serial(RLogDaemon.DEBUG_SMARTMETER_PORT, 9600, timeout = 1)
                if self.findSmartMeter():
                    log("Using %s for smart meter" % RLogDaemon.DEBUG_SMARTMETER_PORT)
                    smart_meter_device = int(RLogDaemon.DEBUG_SMARTMETER_PORT[-1])
                else:
                    log("problem using debug smart meter port: %s" % RLogDaemon.DEBUG_SMARTMETER_PORT)
            else:
                log("Searching for device where the smart meter responds")
                for device_id in range(0, 100):
                    log("Checking if %s%d exists ..." % (DEVICE_NAME_BASE, device_id))
                    if os.path.exists("%s%d" % (DEVICE_NAME_BASE, device_id)):
                        smart_meter_device_name = "%s%d" % (DEVICE_NAME_BASE, device_id)
                        log("trying device: %s as smart meter device" % smart_meter_device_name)
                        self._smart_meter_serial_port = serial.Serial(smart_meter_device_name, baudrate = 9600, stopbits = serial.STOPBITS_ONE, timeout = 2)
                        if self.findSmartMeter():
                            log("Using %s for smart meter" % smart_meter_device_name)
                            smart_meter_device = device_id
                            break
        if RLogDaemon.DEBUG_INVERTER_PORT:
            self._WR_serial_port = serial.Serial(RLogDaemon.DEBUG_INVERTER_PORT, 9600, timeout = 1)
            log("Using device: %s" % RLogDaemon.DEBUG_INVERTER_PORT)
        else:
            log("Searching rs485 device for WR")           
            for device_id in range(0, 100):
                if device_id == smart_meter_device:
                    continue
                log("Checking if %s%d exists..." % (DEVICE_NAME_BASE, device_id))
                if os.path.exists("%s%d" % (DEVICE_NAME_BASE, device_id)):
                    WR_device_name = "%s%d" % (DEVICE_NAME_BASE, device_id)
                    log("Using device: %s" % WR_device_name)
                    self._WR_serial_port = serial.Serial(port=WR_device_name, baudrate = 9600, stopbits = serial.STOPBITS_ONE, timeout = 1)
                    return
            log("Unable to find WR serial port")

    
    # try to read type message (and if that doesn't help data message) of each WR to get their IDs on the bus 
    def findWRs(self):
        if RLogDaemon.MAX_BUS_PARTICIPANTS == 0:
            return
        statements = []
        for bus_id in range(1, RLogDaemon.MAX_BUS_PARTICIPANTS + 1):
            candidate = WR(bus_id, self._WR_serial_port)
            if candidate.does_exist():
                if DEBUG_ENABLED:
                    log("found WR: " + candidate.model + " with bus id " + str(candidate.bus_id))
                self._slaves[bus_id] = candidate
                try:
                    self._mqttPublisher.publish("/devices/RLog/controls/" + candidate.model + " (" + str(candidate.bus_id) + ")/meta/type", "text", 0, True)
                except Exception as e:
                    log("Exception while doing MQTT stuff: " + str(e))
                statements.append((candidate.bus_id, candidate.model))
                if DEBUG_ENABLED:
                    log("Getting latest data for inverter with ID " + str(candidate.bus_id) + " from database")
                self._aggregator.fetchInitialWRdata(self._db_cursor, candidate.bus_id)
            time.sleep(0.33)
        remaining_wr = filter(lambda x: x not in self._slaves, range(1, RLogDaemon.MAX_BUS_PARTICIPANTS + 1))
        if len(remaining_wr) == 0: # all WR have been found
            self._current_discovery_id = None
        else:
            self._current_discovery_id = remaining_wr[0]
            if DEBUG_ENABLED:
                log(str(len(remaining_wr)) + " WR have not yet been discovered")
        if len(statements) > 0:
            try:
                self._db_cursor.executemany("INSERT INTO charts_device (id, model) VALUES (%s, %s)", statements) # actually updates if exists due to database rule
                self._db_connection.commit()
            except psycopg2.OperationalError as ex:
                log("Database is locked or some other DB error!")
                log(str(type(ex))+str(ex))
                
    
    # try to find the smart meter
    def findSmartMeter(self):
        candidate = SmartMeter(self._smart_meter_serial_port)
        if candidate.does_exist():
            try:
                # fake 3 phases as new devices for MQTT
                self._mqttPublisher.publish("/devices/RLog/controls/" + candidate.model + " (1)/meta/type", "text", 0, True)
                self._mqttPublisher.publish("/devices/RLog/controls/" + candidate.model + " (2)/meta/type", "text", 0, True)
                self._mqttPublisher.publish("/devices/RLog/controls/" + candidate.model + " (3)/meta/type", "text", 0, True)
            except Exception as e:
                log("Exception while doing MQTT stuff: " + str(e))
            self._smart_meter_found = True
            self._smart_meter = candidate
            self._aggregator.fetchInitialSmartMeterData(self._db_cursor)
            return True
        return False
        

    def poll_devices(self):
        # variables for Eigenverbrauch
        sumProduced = Decimal(0)
        sumUsed = Decimal(0)
        # poll the WR
        statements = [] # list of string lists that is going to be passed to executemany()
        for (bus_id, wr) in self._slaves.iteritems():
            data = wr.request_data()
            if DEBUG_ENABLED:
                log("Read row %s" % data)
            if data: # looks like "\n*030   5 242.9  0.14    40 230.4  0.27    38  26   1925 Z 3501xi\r"
                tmp = [datetime.now(tzlocal()), str(wr.bus_id)]
                cols = data.split()
                tmp.extend(cols[2:10])
                statements.append(tmp)
                try:
                  linePower = Decimal(cols[7])
                  sumProduced += linePower # add toRether production
                  self.update_bell_counter(linePower)
                except Exception as e:
                   log("Exception polling WR: cols: " + str(cols) + "Message:" + str(e))
                # aggregate stuff (arguments are busID, time of reading, lW and total of day
                self._aggregator.updateInverter(wr.bus_id, tmp[0], Decimal(cols[7]), Decimal(cols[9]))
                # try to publish via MQTT
                try:
                    self._mqttPublisher.publish("/devices/RLog/controls/" + wr.model + " (" + str(wr.bus_id) + ")", cols[7], 0, True) # cols[7] is line power but I saved the str() method on that Decimal as in cols are already strings
                except Exception as e:
                    log("MQTT cause exception in poll_devices(): " + str(e) + " value to publish was: " + cols[7])
                if DEBUG_ENABLED:
                    log("adding: "+ ", ".join([str(x) for x in tmp]) + " to transaction")
                time.sleep(0.33)
        if statements:
            try:
                # every insert is acutally an upsert due to database rules
                self._db_cursor.executemany('INSERT INTO charts_solarentrytick (time, device_id, "gV", "gA", "gW", "lV", "lA", "lW", temp, total) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', statements)
                if DEBUG_ENABLED:
                    log("storing minutely WR data: " + str(self._aggregator.makeExecutemanyDataStructure(self._aggregator.WRminute)))
                self._db_cursor.executemany('INSERT INTO charts_solarentryminute (time, exacttime, device_id, "lW") VALUES (%s, %s, %s, %s)', self._aggregator.makeExecutemanyDataStructure(self._aggregator.WRminute))
                if DEBUG_ENABLED:
                    log("storing hourly WR data: " + str(self._aggregator.makeExecutemanyDataStructure(self._aggregator.WRhour)))
                self._db_cursor.executemany('INSERT INTO charts_solarentryhour (time, device_id, "lW") VALUES (%s, %s, %s)', self._aggregator.makeExecutemanyDataStructure(self._aggregator.WRhour))
                if DEBUG_ENABLED:
                    log("storing daily WR data: " + str(self._aggregator.makeExecutemanyDataStructure(self._aggregator.WRday)))
                self._db_cursor.executemany('INSERT INTO charts_solarentryday (time, device_id, "lW") VALUES (%s, %s, %s)', self._aggregator.makeExecutemanyDataStructure(self._aggregator.WRday))
                if DEBUG_ENABLED:
                    log("storing monthly WR data: " + str(self._aggregator.makeExecutemanyDataStructure(self._aggregator.WRmonth)))
                self._db_cursor.executemany('INSERT INTO charts_solarentrymonth (time, device_id, "lW") VALUES (%s, %s, %s)', self._aggregator.makeExecutemanyDataStructure(self._aggregator.WRmonth))
                if DEBUG_ENABLED:
                    log("storing yearly WR data: " + str(self._aggregator.makeExecutemanyDataStructure(self._aggregator.WRyear)))
                self._db_cursor.executemany('INSERT INTO charts_solarentryyear (time, device_id, "lW") VALUES (%s, %s, %s)', self._aggregator.makeExecutemanyDataStructure(self._aggregator.WRyear))
                if DEBUG_ENABLED:
                    log("storing maximum WR data: " + str(self._aggregator.makeExecutemanyDataStructure(self._aggregator.WRmaxima)))
                self._db_cursor.executemany('INSERT INTO charts_solardailymaxima (time, device_id, "lW", exacttime) VALUES (%s, %s, %s, %s)', self._aggregator.makeExecutemanyDataStructure(self._aggregator.WRmaxima))
                self._db_connection.commit()
            except psycopg2.OperationalError as ex:
                log("WR: Database Operational Error!")
                log(str(type(ex))+str(ex))
            except psycopg2.IntegrityError as e:
                log("integrity error shit is going on: " + str(e))
            except psycopg2.DataError as e:
                log("data error shit is going on: " + str(e))
            except psycopg2.InternalError as e:
                log("internal database error: " + str(e))
        # poll the smart meter (if it's there)
        if self._smart_meter:
            datagram = self._smart_meter.request_data()
            if datagram:
                # looks like this:
                
                # 1-0:1.8.0*255(00000.00*kWh)
                # 1-0:2.1.7*255(00000.00*kWh)
                # 1-0:4.1.7*255(00000.00*kWh)
                # 1-0:6.1.7*255(00000.00*kWh)
                # 1-0:21.7.255*255(0000.0000*kW)
                # 1-0:41.7.255*255(0000.0000*kW)
                # 1-0:61.7.255*255(0000.0000*kW)
                # 1-0:1.7.255*255(0000.0000*kW)
                # 1-0:96.5.5*255(q)
                # 0-0:96.1.255*255(11401476)
                #  <-- yes, here are \r\n!
                
                if DEBUG_ENABLED:
                    log("Smart Meter datagram: %s" % datagram)
                values = [datetime.now(tzlocal())] # appended by list of Decimals. is going to be passed to execute()
                match = self._reading_regex.search(datagram)
                if match:
                    values.append(Decimal(match.group(1)))
                match = self._phase1_regex.search(datagram)
                if match:
                    values.append(Decimal(match.group(1)) * 1000)
                    sumUsed += values[-1]
                    try:
                        self._mqttPublisher.publish("/devices/RLog/controls/" + self._smart_meter.model + " (1)", str(values[-1]), 0, True)
                    except Exception as e:
                        log("MQTT cause exception in poll_devices(): " + str(e))
                match = self._phase2_regex.search(datagram)
                if match:
                    values.append(Decimal(match.group(1)) * 1000)
                    sumUsed += values[-1]
                    try:
                        self._mqttPublisher.publish("/devices/RLog/controls/" + self._smart_meter.model + " (2)", str(values[-1]), 0, True)
                    except Exception as e:
                        log("MQTT cause exception in poll_devices(): " + str(e))
                match = self._phase3_regex.search(datagram)
                if match:
                    values.append(Decimal(match.group(1)) * 1000)
                    sumUsed += values[-1]
                    try:
                        self._mqttPublisher.publish("/devices/RLog/controls/" + self._smart_meter.model + " (3)", str(values[-1]), 0, True)
                    except Exception as e:
                        log("MQTT cause exception in poll_devices(): " + str(e))
                if len(values) == 5:
                    # aggregate stuff (arguments are time of reading, reading, phase1, phase2, phase3
                    self._aggregator.updateSmartMeter(values[0], values[1], values[2], values[3], values[4])
                    # saving everything to database (hopefully that works or I need to do everything in its own try-catch block and transaction
                    # every insert is acutally an upsert due to database rules
                    try:
                        self._db_cursor.execute('INSERT INTO charts_smartmeterentrytick ("time", reading, phase1, phase2, phase3) VALUES (%s, %s, %s, %s, %s)', values)
                        if DEBUG_ENABLED:
                            log("storing minutely smartmeter data: " + str(self._aggregator.SmartMeterMinute.data))
                        self._db_cursor.execute('INSERT INTO charts_smartmeterentryminute ("time", exacttime, reading, phase1, phase2, phase3) VALUES (%s, %s, %s, %s, %s, %s)', self._aggregator.SmartMeterMinute.data)
                        if DEBUG_ENABLED:
                            log("storing hourly smartmeter data: " + str(self._aggregator.SmartMeterHour.data))
                        self._db_cursor.execute('INSERT INTO charts_smartmeterentryhour ("time", reading, phase1, phase2, phase3) VALUES (%s, %s, %s, %s, %s)', self._aggregator.SmartMeterHour.data)
                        if DEBUG_ENABLED:
                            log("storing daily smartmeter data: " + str(self._aggregator.SmartMeterDay.data))
                        self._db_cursor.execute('INSERT INTO charts_smartmeterentryday ("time", reading, phase1, phase2, phase3) VALUES (%s, %s, %s, %s, %s)', self._aggregator.SmartMeterDay.data)
                        if DEBUG_ENABLED:
                            log("storing monthly smartmeter data: " + str(self._aggregator.SmartMeterMonth.data))
                        self._db_cursor.execute('INSERT INTO charts_smartmeterentrymonth ("time", reading, phase1, phase2, phase3) VALUES (%s, %s, %s, %s, %s)', self._aggregator.SmartMeterMonth.data)
                        if DEBUG_ENABLED:
                            log("storing yearly smartmeter data: " + str(self._aggregator.SmartMeterYear.data))
                        self._db_cursor.execute('INSERT INTO charts_smartmeterentryyear ("time", reading, phase1, phase2, phase3) VALUES (%s, %s, %s, %s, %s)', self._aggregator.SmartMeterYear.data)
                        if DEBUG_ENABLED:
                            log("storing maximum smartmeter data: " + str(self._aggregator.SmartMeterMaximum.data))
                        self._db_cursor.execute('INSERT INTO charts_smartmeterdailymaxima ("time", exacttime, maximum) VALUES (%s, %s, %s)', self._aggregator.SmartMeterMaximum.data)
                        self._db_connection.commit()
                    except psycopg2.OperationalError as ex:
                        log("Smart Meter: Database Operational Error!")
                        log(str(type(ex))+str(ex))
                    except psycopg2.IntegrityError as e:
                        log("Integrity shit is going on: " + str(e))
                    except psycopg2.DataError as e:
                        log("data error shit is going on: " + str(e))
                    except psycopg2.InternalError as e:
                        log("internal database error: " + str(e))
                else:
                    log("Can't read all values from smart meter: " + str(values))
        # insert Eigenverbrauch into database
        self._aggregator.updateEigenverbrauch(sumProduced, sumUsed)
        try:
            self._db_cursor.execute("INSERT INTO charts_eigenverbrauch VALUES (%s, %s);", self._aggregator.Eigenverbrauch.data) # will do upsert because of table rule
            self._db_connection.commit()
            if DEBUG_ENABLED:
                log("saving eigenverbrauch: " + str(self._aggregator.Eigenverbrauch.data))
        except Exception as ex:
            log("Error saving eigenverbrauch:")
            log(str(type(ex)) + str(ex))
                
    #check if we need to play the sound
    def update_bell_counter(self, val):
        RLogDaemon.BELLCOUNTER += val / 360000
        
        if RLogDaemon.BELLCOUNTER > RLogDaemon.NEXTRING:
            self.ring_bell()
            RLogDaemon.NEXTRING = RLogDaemon.NEXTRING + RLogDaemon.KWHPERRING
        if DEBUG_ENABLED:
            log("""Bellcount: %s Nextring: %s""" % (str(RLogDaemon.BELLCOUNTER), str(RLogDaemon.NEXTRING)))

    #trigger playsound tool 
    def ring_bell(self):
        #add check if sound is correctly setup (tutorial in adafruit sound pdf)
        #test=os.system("mpg321 -q "+SOUND)
        #test = os.system("mpg321 -q /home/pi/rlog/sound/coin.mp3")
        #log(test)
        pass

# calling this script directly...
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='The RLog daemon handles the communication among the KACO inverters, the smartmeter and the postgresql database.')

    parser.add_argument('--querydelay', default = 10, type = int, help = 'Delay in seconds between two queries')
    parser.add_argument('--participants', default = 3, type = int, help = 'Maximum ID (inclusive) of bus participant to discover (Start id is 1, 0 means no inverters)')
    parser.add_argument('--discoverytimer', default = 10, type = int, help = 'Every X iterations the device discovery will run on the next sequential id (if necessary)')
    parser.add_argument('--smartmeter', action='store_true', help = 'Flip this switch if you also want to read a VSM-102 smart meter (on a different bus)')
    parser.add_argument('--debugInverterPort', default = '', help = 'Take this serial port to read inverters instead of auto discovery')
    parser.add_argument('--debugSmartMeterPort', default = '', help = 'Take this serial port to read smart meter instead of auto discovery')
    parser.add_argument('mode', choices = ['start', 'stop', 'restart'], help = 'What should the daemon do?')
    args = parser.parse_args()

    if os.geteuid() != 0:
        print "You must be root to run this script."
        sys.exit(1)

    daemon = RLogDaemon('/tmp/rlogd.pid')
    RLogDaemon.MAX_BUS_PARTICIPANTS = args.participants
    RLogDaemon.DELAY = args.querydelay
    RLogDaemon.DISCOVERY_COUNT = args.discoverytimer
    RLogDaemon.DEBUG_INVERTER_PORT = args.debugInverterPort
    RLogDaemon.DEBUG_SMARTMETER_PORT = args.debugSmartMeterPort
    daemon._discovery_credit = RLogDaemon.DISCOVERY_COUNT
    daemon._smart_meter_enabled = args.smartmeter

    if 'start' == args.mode:
        log("Starting RLog daemon")
        daemon.start()
        log("RLog daemon started")
    elif 'stop' == args.mode:
        log("Stopping RLog daemon")
        daemon.stop()            
        log("RLog daemon stopped")
    elif 'restart' == args.mode:            
        log("Restarting RLog daemon")
        daemon.restart()
        log("RLog daemon restarted")
    else:
        print "Unknown mode command"
        sys.exit(2)
