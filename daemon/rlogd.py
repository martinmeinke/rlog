#!/usr/bin/env python
 
'''
Created on Oct 10, 2012

@author: martin and stephan
'''
import serial
import sqlite3
import time
import commands
import os
import sys
import datetime
import string
import mqtt
from daemon import Daemon
import argparse

DEBUG_ENABLED = True
DEBUG_SERIAL = True

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
DATABASE = PROJECT_PATH+"/../sensor.db"
DEVICE_NAME_BASE = "/dev/ttyUSB"
DEBUG_SERIAL_PORT = "/dev/pts/5"
MQTT_HOST = "localhost"

def log(msg):
    stripped = str(msg).translate(string.maketrans("\n\r", "  "))
    print "[%s]: %s" % (str(datetime.datetime.today()), stripped)

class WR():
    def __init__(self, bus_id, serial_port):
        self.__serial_port = serial_port
        self.__bus_id = bus_id
        self.__model = ''
    
    # getters for member variables
    @property
    def bus_id(self):
        return self.__bus_id
    
    @property
    def model(self):
        return self.__model
    
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
                    break
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
            self.__serial_port.flushInput()
            self.__serial_port.flushOutput()
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
            self.__serial_port.flushInput()
            self.__serial_port.flushOutput()
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

class RLogDaemon(Daemon):
    DEVICE_NAME = None
    KWHPERRING = None
    NEXTRING = None
    SOUND = None
    DELAY = None
    BELLCOUNTER = 0
    MAX_BUS_PARTICIPANTS = None
    DISCOVERY_COUNT = None

    def __init__(self,pidfile):
        super(RLogDaemon, self).__init__(pidfile)
        self._serial_port = None
        self._slaves = []
        self._slave_names = []
        self._mqttPublisher = None
        self._db_connection = sqlite3.connect(DATABASE)
        self._db_cursor = self._db_connection.cursor()
        self._current_discovery_id = 1
        self._discovery_credit = 0
#        self._db_cursor.execute('PRAGMA journal_mode=WAL;') 
        log("RLogDaemon created")

    def run(self):
        log("daemon running")
        
        self._db_cursor.execute("SELECT * FROM charts_settings WHERE active = 1 ORDER BY id DESC LIMIT 1")
        if self._db_cursor.rowcount == 0:
            log("Couldn't read settings from database")
            return

        sets = self._db_cursor.fetchone()

        try:
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

        #determine the serial adapter to be used
        if DEBUG_SERIAL:
            self._serial_port= serial.Serial(DEBUG_SERIAL_PORT, 9600, timeout = 1)
        else:
            self.discover_device()
        
        log("starting MQTT")
        try:
            self._mqttPublisher = mqtt.mqtt(broker = MQTT_HOST)
            self._mqttPublisher.startMQTT()
            self._mqttPublisher.publish("/devices/RLog/meta/name", "Rlog", 0, True)
        except Exception as e:
            log("mqtt start problem:" + str(e))
            
        if(self._serial_port != None):
            log("looking for WR")
            self.findWRs()
            log("starting normal execution")

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
        self._discovery_credit -= 1

        if DEBUG_ENABLED:
            log("Discovery credit is now: "+str(self._discovery_credit))

        if self._discovery_credit <= 0:
            candidate = WR(self._current_discovery_id, self._serial_port)
            if candidate.does_exist():
                self._slaves.append(candidate)
                self.slaves.sort(key = lambda x: x.bus_id)
                try:
                    self._db_cursor.execute("INSERT OR REPLACE INTO charts_device (id, model) VALUES (?, ?)", (candidate.bus_id, candidate.model))
                    self._db_connection.commit()
                except sqlite3.OperationalError as ex:
                    log("Database is locked or some other DB error!")
                    log(str(type(ex))+str(ex))
                try:
                    self._mqttPublisher.publish("/devices/RLog/controls/" + candidate.model + " (" + str(candidate.bus_id) + ")/meta/type", "text", 0, True)
                except Exception as e:
                    log("Exception while doing MQTT stuff: " + str(e))
            self._current_discovery_id = (self._current_discovery_id % RLogDaemon.MAX_BUS_PARTICIPANTS) + 1
            self._discovery_credit = RLogDaemon.DISCOVERY_COUNT

    def sleep_to_delay(self, t1, t2):
        if DEBUG_ENABLED:
            log("poll delay is : "+str(RLogDaemon.DELAY))
        sleepduration = RLogDaemon.DELAY - (t2 - t1)
        if sleepduration <= 0:
          log("Timing problem (discovery?): %f" % sleepduration)
        else:
          time.sleep(sleepduration)

    #assume the first device starting with DEVICE_NAME_BASE is the rs485 adapter
    def discover_device(self):
        for device_id in range(0, 100):
            log("Checking if %s%d exists..." % (DEVICE_NAME_BASE, device_id))
            if os.path.exists("%s%d" % (DEVICE_NAME_BASE, device_id)):
                RLogDaemon.DEVICE_NAME = "%s%d" % (DEVICE_NAME_BASE, device_id)
                log("Using device: %s" % RLogDaemon.DEVICE_NAME)
                self._serial_port = serial.Serial(port=RLogDaemon.DEVICE_NAME, baudrate = 9600, bytesize = 8, parity = 'N', stopbits = 1, timeout = 1)
                return
        log("Unable to find serial port")

    
    # try to read type message (and if that doesn't help data message) of each WR to get their IDs on the bus 
    def findWRs(self):
        self._slaves = []
        statements = []
        for bus_id in range(1, RLogDaemon.MAX_BUS_PARTICIPANTS + 1):
            candidate = WR(bus_id, self._serial_port)
            if candidate.does_exist():
                if DEBUG_ENABLED:
                    log("found WR: " + candidate.model + " with bus id " + str(candidate.bus_id))
                self._slaves.append(candidate)
                try:
                    self._mqttPublisher.publish("/devices/RLog/controls/" + candidate.model + " (" + str(candidate.bus_id) + ")/meta/type", "text", 0, True)
                except Exception as e:
                    log("Exception while doing MQTT stuff: " + str(e))
                statements.append((candidate.bus_id, candidate.model))
            time.sleep(0.33)
        if len(statements) > 0:
            try:
                self._db_cursor.executemany("INSERT OR REPLACE INTO charts_device (id, model) VALUES (?, ?)", statements)
                self._db_connection.commit()
            except sqlite3.OperationalError as ex:
                log("Database is locked or some other DB error!")
                log(str(type(ex))+str(ex))

    def poll_devices(self):
        statements = []
        for wr in self._slaves:
            data = wr.request_data()
            if DEBUG_ENABLED:
                log("Read row %s" % data)
            if data:
                cols = data.split()
                try:
                  line_power = cols[7]
                  self.update_bell_counter(line_power)
                except Exception as e:
                  log(str(e))
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
                self._db_cursor.executemany("INSERT INTO charts_solarentrytick VALUES (NULL, datetime('now', 'localtime'), ?, ?, ?, ?, ?, ?, ?, ?, ?)", statements)
                self._db_connection.commit()
            except sqlite3.OperationalError as ex:
                log("Database is locked or some other DB error!")
                log(str(type(ex))+str(ex))
                
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
        test = os.system("mpg321 -q /home/pi/rlog/sound/coin.mp3")
        log(test)

# calling this script directly...
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='The RLog daemon handles the communication among the KACO inverters and the Sqlite database.')

    parser.add_argument('--querydelay', default = 10, type = int, help = 'Delay in seconds between two queries')
    parser.add_argument('--participants', default = 32, type = int, help = 'Maximum ID of bus participant to discover')
    parser.add_argument('--discoverytimer', default = 10, type = int, help = 'Every X iterations the device discovery will run on the next sequential id')
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
