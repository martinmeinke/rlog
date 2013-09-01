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
import re
import sys, time, datetime
import string
from daemon import Daemon
import argparse

DEBUG_ENABLED = True
DEBUG_SERIAL = False

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
DATABASE = PROJECT_PATH+"/../sensor.db"
DEVICE_NAME_BASE = "/dev/ttyUSB"
DEBUG_SERIAL_PORT = "/dev/pts/4"

def log(msg):
    stripped = str(msg).translate(string.maketrans("\n\r", "  "))
    print "[%s]: %s" % (str(datetime.datetime.today()), stripped)

#check if we need to play the sound
def update_bell_counter(val):
    RLogDaemon.BELLCOUNTER += (float(val) / 360000)
    
    if RLogDaemon.BELLCOUNTER > RLogDaemon.NEXTRING:
        ring_bell()
        RLogDaemon.NEXTRING = RLogDaemon.NEXTRING + RLogDaemon.KWHPERRING
    if DEBUG_ENABLED:
        log("""Bellcount: %s Nextring: %s""" % (str(RLogDaemon.BELLCOUNTER),str(RLogDaemon.NEXTRING)))
    return

#trigger playsound tool 
def ring_bell():
    #add check if sound is correctly setup (tutorial in adafruit sound pdf)
    #test=os.system("mpg321 -q "+SOUND)
    test = os.system("mpg321 -q /home/pi/rlog/sound/coin.mp3")
    log(test)
    return


#TODO: pot more stuff into the class to eliminate the need for the global stuff
class RLogDaemon(Daemon):
    DEVICE_NAME = None
    KWHPERRING = None
    NEXTRING = None
    SOUND = None
    DELAY = None
    BELLCOUNTER = 0
    MAX_BUS_PARTICIPANTS = 32
    DISCOVERY_COUNT = None

    def __init__(self,pidfile):
        super(RLogDaemon, self).__init__(pidfile)
        self._serial_port = None
        self._slaves = []
        self._db_connection = sqlite3.connect(DATABASE)
        self._db_cursor = self._db_connection.cursor()
        self._current_discovery_id = 0
        self._discovery_credit = 0

    def run(self):
        log("daemon running")
        q_string = (
            "SELECT * "
            "FROM charts_settings "
            "WHERE active = 1 "
            "   ORDER BY id DESC "
            "   LIMIT 1")

        self._db_cursor.execute(q_string)
        if self._db_cursor.rowcount == 0:
            log("Couldn't read settings from database")
            return

        sets = self._db_cursor.fetchone()

        try:
            RLogDaemon.KWHPERRING = sets[2]
            RLogDaemon.NEXTRING = sets[2]
            RLogDaemon.SOUND = sets[3]
        except Exception as ex:
            print str(type(ex))+str(ex)
            RLogDaemon.KWHPERRING = 1
            RLogDaemon.NEXTRING = 1
            RLogDaemon.SOUND = "/home/pi/git/rlog/coin.mp3"
        except Error as err:
            print type(err)

        log("""Using Parameters:
    KWHPERRING: %s
    NEXTRING: %s
    SOUND: %s""" % (RLogDaemon.KWHPERRING, RLogDaemon.NEXTRING, RLogDaemon.SOUND))

        #determine the serial adapter to be used
        if DEBUG_SERIAL:
            self._serial_port= serial.Serial(DEBUG_SERIAL_PORT, 9600, timeout=1)
        else:
            self.discover_device()
            
        if(self._serial_port != None):
            log("looking for WR")
            self.findWRs()
            log("starting normal execution")

            while True:
                t1 = time.time()
                self.poll_devices()
                self.run_discovery_if_required()
                t2 = time.time()
                self.sleep_to_delay(t1, t2)

            self._serial_port.close();
        else:
            sys.exit(1)
    
    def run_discovery_if_required(self):
        self._discovery_credit -= 1
        if self._discovery_credit <= 0:
            self.findWR(self._current_discovery_id)
            self._current_discovery_id += 1
            self._current_discovery_id %= RLogDaemon.MAX_BUS_PARTICIPANTS
            self._discovery_credit = RLogDaemon.DISCOVERY_COUNT

    def sleep_to_delay(self, t1, t2):
        sleepduration = RLogDaemon.DELAY-(t2-t1)
        if sleepduration < 0:
          log("Timing problem (discovery?): %f" % sleepduration)
        if sleepduration > 0:
          time.sleep(sleepduration)

    #assume the first device starting with DEVICE_NAME_BASE is the rs485 adapter
    def discover_device(self):
        for device_id in range(0,100):
            log("Checking if %s%d exists..." % (DEVICE_NAME_BASE, device_id))
            if os.path.exists("%s%d" % (DEVICE_NAME_BASE,device_id)):
                RLogDaemon.DEVICE_NAME = "%s%d" % (DEVICE_NAME_BASE, device_id)
                log("Using device: %s" % RLogDaemon.DEVICE_NAME)
                self._serial_port = serial.Serial(port=RLogDaemon.DEVICE_NAME, baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=1)
                return
        log("Unable to find serial port")

    # checks checksum in type message
    def check_typ(self, typ_string):
      summe = 0
      for i in range(1, len(typ_string) - 2): # 2. zeichen von hinten ist pruefsumme bei mir
        summe += ord(typ_string[i])
      if ord(typ_string[-2]) != summe % 256:
        log("Read invalid Type Message: " + typ_string)
        return False
      else:
        return True

    # checks checksum in data message
    def check_daten(self, data_string):
        summe = 0
        for i in range(1, len(data_string) - 9): # 9. zeichen von hinten ist pruefsumme bei mir
            summe += ord(data_string[i])

        if DEBUG_SERIAL:
            return True
        else:
            if ord(data_string[-9]) != summe % 256:
                log("Read invalid Data Message: " + data_string)
                return False
            else:
                return True
	    
    def read_line(self, timeout = 2):
      response = ''
      start_zeit = time.time()
      try:
        # skip everything until line feed
        while(True):
          response = self._serial_port.read()
          if response and response[0] == '\n':
            break
          if time.time() - start_zeit > timeout:
            return response
        # read until return character
        while(True):
          response += self._serial_port.read()
          if response and response[-1] == '\r':
            break
          if time.time() - start_zeit > timeout:
            break
      except SerialException as e:
        log("Serial breakdown. looking for serial device again")
        if DEBUG_SERIAL:
            self._serial_port= serial.Serial(DEBUG_SERIAL_PORT, 9600, timeout=1)
        else:
            self.discover_device()
      return response

    def request_type_from_device(self, device_id_raw):
        try:
            self._serial_port.flushInput()
            self._serial_port.flushOutput()
            self._serial_port.write("#" + "{0:02d}".format(device_id_raw) + "9\r")
            #self._serial_port.write("#" + "{0:02d}".format(device_id_raw) + "9\r")
            self._serial_port.flush()
            typ = self.read_line()
            if len(typ) != 15: # so lang sind meine typen normalerweise
              log("read type with invalid length (" + str(len(typ)) + ") from WR " + str(device_id_raw) + " (" + typ + ")")
              return None
            else:
              return typ
        except serial.SerialException as e:
            log("Serial breakdown. looking for serial device again")
            if DEBUG_SERIAL:
                self._serial_port= serial.Serial(DEBUG_SERIAL_PORT, 9600, timeout=1)
            else:
                self.discover_device()
            return None
        except Exception as e:
            log("Exception during type request %s" % e)
            return None
        
    def request_data_from_device(self, device_id_raw):
        try:
            self._serial_port.flushInput()
            self._serial_port.flushOutput()
            self._serial_port.write("#" + "{0:02d}".format(device_id_raw) + "0\r")
            #self._serial_port.write("#" + "{0:02d}".format(device_id_raw) + "0\r")
            self._serial_port.flush()
            daten = self.read_line()
            if len(daten) != 66: # so lang sind meine daten normalerweise
              log("read data with invalid length (" + str(len(daten)) + ") from WR " + str(device_id_raw) + " (" + daten + ")")
              return None
            else:
              return daten
        except serial.SerialException as e:
            log("Serial breakdown. looking for serial device again")
            if DEBUG_SERIAL:
                self._serial_port= serial.Serial(DEBUG_SERIAL_PORT, 9600, timeout=1)
            else:
                self.discover_device()
            return None
        except Exception as e:
            log("Exception during data request %s" % e)
            return None

    def findWR(self, device_id):
        log("Running discovery on ID " + str(device_id))
        typ = self.request_type_from_device(device_id)
        new_wr = None

        if typ != None and self.check_typ(typ):
            log("Device %d answered %s " % (device_id, typ))

            new_wr = {"device_id" : device_id, "type" : typ.split()[1]}
            self._slaves.append(new_wr) 

            if DEBUG_ENABLED:           
                log(new_wr)

            time.sleep(0.33)
        else: # if it didn't answer on type request it gets another chance and is asked for data this time ...
           data = self.request_data_from_device(device_id)
           if data != None and self.check_daten(data):
               log("Device %d answered %s " % (device_id, data))

               new_wr = {"device_id" : device_id, "type" : data.split()[-1]}
               self._slaves.append(new_wr)

               if DEBUG_ENABLED:           
                  log(new_wr)

               time.sleep(0.33)

        if new_wr != None:
            try:
                self._db_cursor.execute("INSERT OR REPLACE INTO charts_device (id, model) VALUES (?, ?)", (new_wr["device_id"], new_wr["type"]))
                self._db_connection.commit()
            except sqlite3.OperationalError as ex:
                log("Database is locked or some other DB error!")
                print str(type(ex))+str(ex)
    
    # try to read type message (and if that doesn't help data message) of each WR to get their IDs on the bus 
    def findWRs(self):
        for deviceID in range(1, 33):
            self.findWR(deviceID)

        statements = []
        for nwr in self._slaves:
            statements.append([str(nwr["device_id"]), nwr["type"]])

        if len(statements) > 0:
            try:
                self._db_cursor.executemany("INSERT OR REPLACE INTO charts_device (id, model) VALUES (?, ?)", statements)
                self._db_connection.commit()
            except sqlite3.OperationalError as ex:
                log("Database is locked or some other DB error!")
                print str(type(ex))+str(ex)

    def poll_devices(self):
        statements = []
        for device in self._slaves:
            new_row = self.request_data_from_device(device["device_id"])
            if DEBUG_ENABLED:
                log("Read row %s" % new_row)
            if new_row != None and self.check_daten(new_row):
                cols = new_row.split()
                try:
                  line_power = cols[7]
                  update_bell_counter(line_power)
                except Exception as e:
                  print e
                tmp = [str(device["device_id"])]
                tmp.extend(cols[2:10])
                statements.append(tmp)
                if DEBUG_ENABLED:
                  log("adding: "+ ", ".join(tmp) + " to transaction")
                time.sleep(0.33)
        if statements:
            try:
                self._db_cursor.executemany("INSERT INTO charts_solarentrytick VALUES (NULL, datetime('now', 'localtime'), ?, ?, ?, ?, ?, ?, ?, ?, ?)", statements)
                self._db_connection.commit()
            except sqlite3.OperationalError as ex:
                log("Database is locked or some other DB error!")
                print str(type(ex))+str(ex)

# calling this script directly...
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='The RLog daemon handles the communication among the KACO inverters and the Sqlite database.')

    parser.add_argument('--querydelay', default=20, type=int, help='Delay in seconds between two queries')
    parser.add_argument('--discoverytimer', default=10, type=int, help='Every X iterations the device discovery will run on the next sequential id')
    parser.add_argument('mode', choices=['start', 'stop', 'restart'], help='What should the daemon do?')
    args = parser.parse_args()

    if os.geteuid() != 0:
        print "You must be root to run this script."
        sys.exit(1)

    daemon = RLogDaemon('/tmp/rlogd.pid')
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

    sys.exit(0)
 
