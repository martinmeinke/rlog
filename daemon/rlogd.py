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
import datetime
import string
import mqtt
from daemon import Daemon
import argparse
import re

DEBUG_ENABLED = True
DEBUG_SERIAL = True

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
#DATABASE = PROJECT_PATH+"/../sensor.db"
DEVICE_NAME_BASE = "/dev/ttyUSB"
DEBUG_SERIAL_PORT = "/dev/pts/3"
MQTT_HOST = "localhost"

LOCATIONX = "14.122994"
LOCATIONY = "52.508519"

def log(msg):
    stripped = str(msg).translate(string.maketrans("\n\r", "  "))
    print "[%s]: %s" % (str(datetime.datetime.today()), stripped)

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
        if DEBUG_SERIAL:
            return True
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
                data_buffer += self.__serial_port.read()
                match = self.__start_regex.search(data_buffer)
                if match:
                    response = match.group(0)
                    break
                if time.time() - start_zeit > timeout:
                    return response
            # read until 0-0:96.1.255*255 arrives (indicates the last line containing the serial number)
            while(True):
                response += self.__serial_port.read()
                match = self.__end_regex.search(response)
                if match:
                    break
                if time.time() - start_zeit > timeout:
                    return response
            # skip everything until line feed
            while(True):
                response += self.__serial_port.read()
                if response[-1] == '\n':
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
    def __init__(self, time = None, data = None):
        self.timestamp = datetime.datetime.today() if time == None else time # this is going to hold the time when the data was last updated
        self.data = [] if data == None else data # this is going to hold the actual data as psycopg2's execute() expects
    
    def __str__(self):
        return "time: " + str(self.timestamp) + " data: " + str(self.data)

    def __repr__(self):
        return self.__str__()


class Aggregation():
    def __init__(self):
        self.WRminute = {} # dictionary for the minutely inverter data, e.g by bus_id (should be of type AggregationItem so that makeExecutemanyDataStructure() is able to operate on it)
        self.WRhour = {}
        # inverter day does not need to be aggregated as it is contained precisely in every inverter message
        self.WRmonth = {}
        self.WRyear = {}
        self.WRmaxima = {}
        
        self.SmartMeterMinute = None # should be AggregationItem so that makeExecutemanyDataStructure() is able to operate on it)
        self.SmartMeterHour = None
        self.SmartMeterDay = None
        self.SmartMeterMonth = None
        self.SmartMeterYear = None
        self.SmartMeterMaximum = None
    
    # this method takes a db cursor and the bus id and retrieves the latest data from the database to initialize inverter fields
    def getInitialWRdata(self, db_cursor, busID):
        # start with WR minute
        try:
            db_cursor.execute('SELECT time, exacttime, device_id, "lW" FROM charts_solarentryminute where device_id = %s ORDER BY time DESC LIMIT 1;', [busID])
            if db_cursor.rowcount == 0:
                log("There is no minutely inverter data for bus id " + str(busID))
                self.WRminute[busID] = AggregationItem()
            else:
                minutely = db_cursor.fetchone()
                self.WRminute[busID] = AggregationItem(minutely[1], minutely)
        except Exception as ex:
            log("Exception while loading minutely data: " + str(ex))
            sys.exit(1)
        # hour
        try:
            db_cursor.execute('SELECT time, device_id, "lW" FROM charts_solarentryhour where device_id = %s ORDER BY time DESC LIMIT 1;', [busID])
            if db_cursor.rowcount == 0:
                log("There is no hourly inverter data for bus id " + str(busID))
                self.WRhour[busID] = AggregationItem()
            else:
                hourly = db_cursor.fetchone()
                self.WRhour[busID] = AggregationItem(hourly[0], hourly)
        except Exception as ex:
            log("Exception while loading hourly data: " + str(ex))
            sys.exit(1)
        # month
        try:
            db_cursor.execute('SELECT time, device_id, "lW" FROM charts_solarentrymonth where device_id = %s ORDER BY time DESC LIMIT 1;', [busID])
            if db_cursor.rowcount == 0:
                log("There is no monthly inverter data for bus id " + str(busID))
                self.WRmonth[busID] = AggregationItem()
            else:
                monthly = db_cursor.fetchone()
                self.WRmonth[busID] = AggregationItem(monthly[0], monthly)
        except Exception as ex:
            log("Exception while loading monthly data: " + str(ex))
            sys.exit(1)
        # year
        try:
            db_cursor.execute('SELECT time, device_id, "lW" FROM charts_solarentryyear where device_id = %s ORDER BY time DESC LIMIT 1;', [busID])
            if db_cursor.rowcount == 0:
                log("There is no yearly inverter data for bus id " + str(busID))
                self.WRyear[busID] = AggregationItem()
            else:
                yearly = db_cursor.fetchone()
                self.WRyear[busID] = AggregationItem(yearly[0], yearly)
        except Exception as ex:
            log("Exception while loading yearly data: " + str(ex))
            sys.exit(1)
        # maximum
        try:
            db_cursor.execute('SELECT time, device_id, "lW", exacttime FROM charts_solardailymaxima where device_id = %s ORDER BY time DESC LIMIT 1;', [busID])
            if db_cursor.rowcount == 0:
                log("There is no maximum inverter data for bus id " + str(busID))
                self.WRmaxima[busID] = AggregationItem()
            else:
                maximum = db_cursor.fetchone()
                if maximum[0] == datetime.datetime.today().date():
                    self.WRmaxima[busID] = AggregationItem(maximum[0], maximum)
        except Exception as ex:
            log("Exception while loading maximum data: " + str(ex))
            sys.exit(1)
        log("Minutely: " + str(self.WRminute))
        log("Hourly: " + str(self.WRhour))
        log("Monthly: " + str(self.WRmonth))
        log("Yearly: " + str(self.WRyear))
        log("Maxima: " + str(self.WRmaxima))
       
    
    # this method takes a db cursor and retrieves the latest data from the database to initialize smartmeter fields
    def getInitialSmartMeterData(self, db_cursor):
        # start with WR minute
        try:
            for bus_id in busIDs:
                db_cursor.execute('SELECT ("time", exacttime, device_id, "lW") FROM charts_solarentryminute where device_id = %s ORDER BY time DESC LIMIT 1', [bus_id])
                if db_cursor.rowcount == 0:
                    log("There is no minutely inverter data for bus id " + str(bus_id))
                    self.WRminute[bus_id] = AggregationItem()
                else:
                    minutely = db_cursor.fetchone()
                    self.WRminute[bus_id] = AggregationItem(minutely[0], minutely)
        except Exception as ex:
            log("Exception while loading minutely data: " + str(ex))
            sys.exit(1)
        
    # makes a executemany compliant nested array structure from dictionary of AggregationItems
    def makeExecutemanyDataStructure(self, arrayOfAggregationItems):
        return [item.data for item in arrayOfAggregationItems.values()]
        
class RLogDaemon(Daemon):
    KWHPERRING = None
    NEXTRING = None
    SOUND = None
    DELAY = None
    BELLCOUNTER = 0
    MAX_BUS_PARTICIPANTS = None
    DISCOVERY_COUNT = None

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
        log("database conencted")

    def run(self):
        log("daemon running")

        self.connectToDatabase() # necessary to connect here and not earlier in constructor because database connections will not survive daemonization (fork) (at least not when using ip sockets)
        
        self._db_cursor.execute("SELECT * FROM charts_settings WHERE active = TRUE ORDER BY id DESC LIMIT 1;")
        try:
            if self._db_cursor.rowcount == 0:
                log("Couldn't read settings from database")
            else:
                sets = self._db_cursor.fetchone()
                RLogDaemon.KWHPERRING = sets[2]
                RLogDaemon.NEXTRING = sets[2]
                RLogDaemon.SOUND = sets[3]
        except Exception as ex:
            log(str(type(ex))+str(ex))
            RLogDaemon.KWHPERRING = 1
            RLogDaemon.NEXTRING = 1
            RLogDaemon.SOUND = "/home/pi/git/rlog/coin.mp3"
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
 

        #determine the serial adapter to be used
        if DEBUG_SERIAL:
            self._WR_serial_port = serial.Serial(DEBUG_SERIAL_PORT, 9600, timeout = 1)
        else:
            self.discover_device()
                   
        if(self._WR_serial_port != None):
            log("looking for WR")
            self.findWRs()
            log("starting normal execution")
            sys.exit(0)

            while True:
                t1 = time.time()
                self.poll_devices()
                t15 = time.time()
                self.run_discovery_if_required()
                t2 = time.time()
                if DEBUG_ENABLED:
                    log("befor poll: {0}\nafter poll: {1}\n after discovery: {2}".format(t1, t15, t2))
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
                        self._db_cursor.execute("INSERT INTO charts_device (id, model) VALUES (%s, %s)", (candidate.bus_id, candidate.model)) # actually updates if exists due to database rule:
# CREATE OR REPLACE RULE upsert_device AS
#    ON INSERT TO charts_device
#       WHERE (EXISTS (SELECT 1 FROM charts_device WHERE charts_device."id" = new."id"))
#    DO INSTEAD 
#       UPDATE charts_device SET "model" = new."model"
#            WHERE charts_device."id" = new."id";
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
                    self._aggregator.getInitialWRdata(self._db_cursor, candidate.bus_id)
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
            log("poll delay is : "+str(RLogDaemon.DELAY))
        sleepduration = RLogDaemon.DELAY - (t2 - t1)
        if sleepduration <= 0:
          log("Timing problem (discovery?): %f" % sleepduration)
        else:
          time.sleep(sleepduration)

    # try all device starting with DEVICE_NAME_BASE and try to talk to the smart meter if it exists (if smart meter is enabled).
    # if smart meter is found (or smartmeter is not enabled) try the first device starting with DEVICE_NAME_BASE and assume it is the rs485 adapter for the WR (make sure to skip smart meter adapter if present)
    def discover_device(self):
        smart_meter_device = -1 # to be excluded in the second run
        if self._smart_meter_enabled:
            log("Searching for device where the smart meter responds")
            for device_id in range(0, 100):
                log("Checking if %s%d exists ..." % (DEVICE_NAME_BASE, device_id))
                if os.path.exists("%s%d" % (DEVICE_NAME_BASE, device_id)):
                    smart_meter_device_name = "%s%d" % (DEVICE_NAME_BASE, device_id)
                    log("trying device: %s as smart meter device" % smart_meter_device_name)
                    self._smart_meter_serial_port = serial.Serial(smart_meter_device_name, baudrate = 9600, stopbits = serial.STOPBITS_ONE, timeout = 1)
                    if self.findSmartMeter():
                        log("Using %s for smart meter" % smart_meter_device_name)
                        smart_meter_device = device_id
                        break
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
                self._aggregator.getInitialWRdata(self._db_cursor, candidate.bus_id)
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
                self._db_cursor.executemany("INSERT INTO charts_device (id, model) VALUES (%s, %s)", statements) # actually updates if exists due to database rule:
# CREATE OR REPLACE RULE upsert_device AS
#    ON INSERT TO charts_device
#       WHERE (EXISTS (SELECT 1 FROM charts_device WHERE charts_device."id" = new."id"))
#    DO INSTEAD 
#       UPDATE charts_device SET "model" = new."model"
#            WHERE charts_device."id" = new."id";

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
            return True
        return False
        

    def poll_devices(self):
	# variables for Eigenverbrauch
	sumProduced = 0
	sumUsed = 0
        # poll the WR
        statements = []
        for (bus_id, wr) in self._slaves.iteritems():
            data = wr.request_data()
            if DEBUG_ENABLED:
                log("Read row %s" % data)
            if data:
                cols = data.split()
                try:
                  linePower = cols[7]
                  sumProduced += float(linePower) # add together production
                  self.update_bell_counter(linePower)
                except Exception as e:
                   log("Exception polling WR: cols: " + str(cols) + "Message:" + str(e))
                tmp = [str(wr.bus_id)]
                tmp.extend(cols[2:10])
                statements.append(tmp)
                try:
                    self._mqttPublisher.publish("/devices/RLog/controls/" + wr.model + " (" + str(wr.bus_id) + ")", tmp[-3], 0, True)
                except Exception as e:
                    log("MQTT cause exception in poll_devices(): " + str(e) + " value to publish was: " + tmp[-3])
                if DEBUG_ENABLED:
                    log("adding: "+ ", ".join(tmp) + " to transaction")
                time.sleep(0.33)
        if statements:
            try:
                self._db_cursor.executemany('INSERT INTO charts_solarentrytick (time, device_id, "gV", "gA", "gW", "lV", "lA", "lW", temp, total) VALUES (now(), %s, %s, %s, %s, %s, %s, %s, %s, %s)', statements)
                self._db_connection.commit()
            except psycopg2.OperationalError as ex:
                log("WR: Database Operational Error!")
                log(str(type(ex))+str(ex))
            except psycopg2.IntegrityError as e:
                log("integrity error shit is going on\n" + str(e))
        # poll the smart meter (if it's there)
        if self._smart_meter:
            statements = []
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
                values = []
                match = self._reading_regex.search(datagram)
                if match:
                    values.append(float(match.group(1)))
                match = self._phase1_regex.search(datagram)
                if match:
                    values.append(float(match.group(1)) * 1000)
                    sumUsed += values[-1]
                    try:
                        self._mqttPublisher.publish("/devices/RLog/controls/" + self._smart_meter.model + " (1)", str(values[-1]), 0, True)
                    except Exception as e:
                        log("MQTT cause exception in poll_devices(): " + str(e))
                match = self._phase2_regex.search(datagram)
                if match:
                    values.append(float(match.group(1)) * 1000)
                    sumUsed += values[-1]
                    try:
                        self._mqttPublisher.publish("/devices/RLog/controls/" + self._smart_meter.model + " (2)", str(values[-1]), 0, True)
                    except Exception as e:
                        log("MQTT cause exception in poll_devices(): " + str(e))
                match = self._phase3_regex.search(datagram)
                if match:
                    values.append(float(match.group(1)) * 1000)
                    sumUsed += values[-1]
                    try:
                        self._mqttPublisher.publish("/devices/RLog/controls/" + self._smart_meter.model + " (3)", str(values[-1]), 0, True)
                    except Exception as e:
                        log("MQTT cause exception in poll_devices(): " + str(e))
                if len(values) == 4:
                    try:
                        self._db_cursor.execute("INSERT INTO charts_smartmeterentrytick (time, reading, phase1, phase2, phase3) VALUES (now(), %s, %s, %s, %s)", values)
                        self._db_connection.commit()
                    except psycopg2.OperationalError as ex:
                        log("Smart Meter: Database Operational Error!")
                        log(str(type(ex))+str(ex))
                    except psycopg2.IntegrityError as e:
                        log("Integrity shit is going on\n" + str(e))
                else:
                    log("Can't read all values from smart meter: " + str(values))
        # insert Eigenverbrauch into database
        eigenverbrauch = sumUsed if sumProduced > sumUsed else sumProduced
        try:
            currentValue = 0;
            self._db_cursor.execute("SELECT eigenverbrauch FROM charts_eigenverbrauch WHERE time = CURRENT_DATE LIMIT 1")
            if self._db_cursor.rowcount != 0:
                value = self._db_cursor.fetchone()
		if value:
                    currentValue = float(value[0])
            newValue = currentValue + eigenverbrauch * (time.time() - self._eigenverbrauchLastSaved) / 3600 # make energy from power within last polling interval
            self._db_cursor.execute("INSERT INTO charts_eigenverbrauch VALUES (now(), %s)/", [newValue]) # will do insert or replace because of table rule:
#"CREATE OR REPLACE RULE upsert_eigenverbrauch AS
#   ON INSERT TO charts_eigenverbrauch
#     WHERE (EXISTS (SELECT 1 FROM charts_eigenverbrauch WHERE ("time" = new."time")))
#   DO INSTEAD 
#     UPDATE charts_eigenverbrauch SET "eigenverbrauch" = new."eigenverbrauch" WHERE ("time" = new."time");
            self._db_connection.commit()
            self._eigenverbrauchLastSaved = time.time()
        except psycopg2.OperationalError as ex:
            log("Eigenverbrauch: Database Operational Error")
            log(str(type(ex)) + str(ex))
        except psycopg2.IntegrityError as e:
            log("integrity error (triggers?)")
            log(str(type(ex)) + str(ex))
                
    #check if we need to play the sound
    def update_bell_counter(self, val):
        RLogDaemon.BELLCOUNTER += (float(val) / 360000)
        
        if RLogDaemon.BELLCOUNTER > RLogDaemon.NEXTRING:
            self.ring_bell()
            RLogDaemon.NEXTRING = RLogDaemon.NEXTRING + RLogDaemon.KWHPERRING
        if DEBUG_ENABLED:
            log("""Bellcount: %s Nextring: %s""" % (str(RLogDaemon.BELLCOUNTER),str(RLogDaemon.NEXTRING)))

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
    parser.add_argument('--participants', default = 32, type = int, help = 'Maximum ID of bus participant to discover')
    parser.add_argument('--discoverytimer', default = 10, type = int, help = 'Every X iterations the device discovery will run on the next sequential id')
    parser.add_argument('--smartmeter', action='store_true', help = 'Flip this switch if you also want to read a VSM-102 smart meter on the same bus')
    parser.add_argument('mode', choices = ['start', 'stop', 'restart'], help = 'What should the daemon do?')
    args = parser.parse_args()

    if os.geteuid() != 0:
        print "You must be root to run this script."
        sys.exit(1)

    daemon = RLogDaemon('/tmp/rlogd.pid')
    RLogDaemon.MAX_BUS_PARTICIPANTS = args.participants
    RLogDaemon.DELAY = args.querydelay
    RLogDaemon.DISCOVERY_COUNT = args.discoverytimer
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
