#!/usr/bin/env python
 
'''
Created on Oct 10, 2012

@author: martin
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

DEBUG_ENABLED = False

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
DATABASE = PROJECT_PATH+"/../sensor.db"
DEVICE_NAME_BASE = "/dev/ttyUSB"
DEBUG_SERIAL_PORT = "/dev/pts/7"

def log(msg):
    stripped = str(msg).translate(string.maketrans("\n\r", "  "))
    print "[%s]: %s" % (str(datetime.datetime.now()), stripped)

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
    test=os.system("mpg321 -q /home/pi/rlog/sound/coin.mp3")
    log(test)
    return


#TODO: pot more stuff into the class to eliminate the need for the global stuff
class RLogDaemon(Daemon):
    DEVICE_NAME = None
    KWHPERRING = None
    NEXTRING = None
    SOUND = None
    DELAY = 10
    BELLCOUNTER = 0

    def __init__(self,pidfile):
        super(RLogDaemon, self).__init__(pidfile)
        self._serial_port = None
        self._slaves = []
        self._db_connection = sqlite3.connect(DATABASE)
        self._db_cursor = self._db_connection.cursor()
#        self._db_cursor.execute('PRAGMA journal_mode=WAL;') 
        log("RLogDaemon created")

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
    SOUND: %s""" % (RLogDaemon.KWHPERRING,RLogDaemon.NEXTRING,RLogDaemon.SOUND))

        if DEBUG_ENABLED:
            self._serial_port= serial.Serial(DEBUG_SERIAL_PORT, 9600, timeout=1)
        else:
            self._serial_port = self.discover_device()
            self._serial_port = serial.Serial(port=RLogDaemon.DEVICE_NAME, baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=1)

        log("looking for WR")
        self.findWR()
        log("starting normal execution")
        while True:
            t1 = time.time()
            self.poll_devices()
            t2 = time.time()
            sleepduration = RLogDaemon.DELAY-(t2-t1)
            if sleepduration < 0:
              log("Timing problem: %f" % sleepduration)
            if sleepduration > 0:
              time.sleep(sleepduration)

        self._serial_port.close();
    
    def discover_device(self):
        for device_id in range(0,100):
            log("Checking if %s%d exists..." % (DEVICE_NAME_BASE, device_id))
            if os.path.exists("%s%d" % (DEVICE_NAME_BASE,device_id)):
                RLogDaemon.DEVICE_NAME = "%s%d" % (DEVICE_NAME_BASE, device_id)
                log("Using device: %s" % RLogDaemon.DEVICE_NAME)
                break
        return

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
      if ord(data_string[-9]) != summe % 256:
        log("Read invalid Data Message: " + data_string)
        return False
      else:
        return True
	    
    def read_line(self, timeout = 2):
      response = ''
      start_zeit = time.time()
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
      return response

    def request_type_from_device(self, device_id_raw):
      self._serial_port.flushInput()
      self._serial_port.flushOutput()
      self._serial_port.write("#" + "{0:02d}".format(device_id_raw) + "9\r")
      self._serial_port.write("#" + "{0:02d}".format(device_id_raw) + "9\r")
      self._serial_port.flush()
      typ = self.read_line()
      if len(typ) != 15: # so lang sind meine typen normalerweise
        log("read type with invalid length (" + str(len(typ)) + ") from WR " + str(device_id_raw) + " (" + typ + ")")
        return None
      else:
        return typ
        
    def request_data_from_device(self, device_id_raw):
      self._serial_port.flushInput()
      self._serial_port.flushOutput()
      self._serial_port.write("#" + "{0:02d}".format(device_id_raw) + "0\r")
      self._serial_port.write("#" + "{0:02d}".format(device_id_raw) + "0\r")
      self._serial_port.flush()
      daten = self.read_line()
      if len(daten) != 66: # so lang sind meine daten normalerweise
        log("read data with invalid length (" + str(len(daten)) + ") from WR " + str(device_id_raw) + " (" + daten + ")")
        return None
      else:
        return daten
    
    # try to read type message of each WR to get their IDs on the bus 
    def findWR(self):
        statements = []
        for deviceID in range(1, 4):
            typ = self.request_type_from_device(deviceID)
            if typ != None and self.check_typ(typ):
                log("Device %d answered %s " % (deviceID, typ))
                self._slaves.append(deviceID)  
                statements.append([str(deviceID), typ.split()[1]])
                if DEBUG_ENABLED:           
                    log("Adding " + typ.split()[1] + " with device ID " + str(deviceID) + " to transaction for charts_device table")
                time.sleep(0.2)
        if statements:
            try:
                self._db_cursor.executemany("INSERT OR REPLACE INTO charts_device (id, model) VALUES (?, ?)", statements)
                self._db_connection.commit()
            except sqlite3.OperationalError as ex:
                log("Database is locked or some other DB error!")
                print str(type(ex))+str(ex)

    def poll_devices(self):
        statements = []
        for device_id in self._slaves:
            new_row = self.request_data_from_device(device_id)
            if DEBUG_ENABLED:
                log("Read row %s" % new_row)
            if new_row != None and self.check_daten(new_row):
                cols = new_row.split()
                try:
                  line_power = cols[7]
                  update_bell_counter(line_power)
                except Exception as e:
                  print e
                tmp = [str(device_id)]
                tmp.extend(cols[2:10])
                statements.append(tmp)
                if DEBUG_ENABLED:
                  log("adding: "+ ", ".join(tmp) + " to transaction")
                time.sleep(0.2)
        if statements:
            try:
              self._db_cursor.executemany("INSERT INTO charts_solarentrytick VALUES (NULL, datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?)", statements)
              self._db_connection.commit()
            except sqlite3.OperationalError as ex:
              log("Database is locked or some other DB error!")
              print str(type(ex))+str(ex)

if __name__ == "__main__":
    if os.geteuid() != 0:
        print "You must be root to run this script."
        sys.exit(1)

    daemon = RLogDaemon('/tmp/daemon-example.pid')
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print "Unknown command"
            sys.exit(2)

        sys.exit(0)
    else:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)
