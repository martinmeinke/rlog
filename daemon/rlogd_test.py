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

def discover_device():
    for device_id in range(0,100):
        log("Checking if %s%d exists..." % (DEVICE_NAME_BASE,device_id))
        if os.path.exists("%s%d" % (DEVICE_NAME_BASE,device_id)):
            RLogDaemon.DEVICE_NAME = "%s%d" % (DEVICE_NAME_BASE,device_id)
            log("Using device: %s" % RLogDaemon.DEVICE_NAME)
            break
    return

# checks checksum in type message
def check_typ(typ_string):
  summe = 0
  for i in range(1, len(typ_string) - 2): # 2. zeichen von hinten ist pruefsumme bei mir
    summe += ord(typ_string[i])
  if ord(typ_string[-2]) != summe % 256:
    log("Read invalid Type Message: " + typ_string)
    return False
  else:
    return True

# checks checksum in data message
def check_daten(data_string):
  summe = 0
  for i in range(1, len(data_string) - 9): # 9. zeichen von hinten ist pruefsumme bei mir
    summe += ord(data_string[i])
  if ord(data_string[-9]) != summe % 256:
    log("Read invalid Data Message: " + data_string)
    return False
  else:
    return True

#check if we need to play the sound
def update_bell_counter(val):
    RLogDaemon.BELLCOUNTER += (float(val) / 360000)
    
    if RLogDaemon.BELLCOUNTER > RLogDaemon.NEXTRING:
        ring_bell()
        RLogDaemon.NEXTRING = RLogDaemon.NEXTRING + RLogDaemon.KWHPERRING
    
    log("""Bellcount: %s 
Nextring: %s""" % (str(RLogDaemon.BELLCOUNTER),str(RLogDaemon.NEXTRING)))
    
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
        self._db_cursor.execute('PRAGMA journal_mode=WAL;') 

    def run(self):
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
            self._serial_port = discover_device()
            self._serial_port = serial.Serial(port=RLogDaemon.DEVICE_NAME, baudrate=9600, bytesize=8, parity='N', stopbits=1)
            self._serial_port.timeout = 1

        self.findWR()
        
        while True:
            t1 = time.time()
            self.poll_devices()
            t2 = time.time()
            sleepduration = RLogDaemon.DELAY-(t2-t1)
            log("Sleeping: %f" % sleepduration)
            if sleepduration > 0:
              time.sleep(sleepduration)

        self._serial_port.close();
	    
    def read_line(self, timeout = 3):
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
        log("read type with invalid length (" + str(len(typ)) + ") " + typ)
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
        log("read data with invalid length (" + str(len(daten)) + ") " + daten)
        return None
      else:
        return daten
    
    # try to read type message of each WR to get their IDs on the bus 
    def findWR(self):
        for deviceID in range(1, 4):
            typ = self.request_type_from_device(deviceID)
            if typ != None and check_typ(typ):
                log("Device %d answered %s " % (deviceID, typ))
                self._slaves.append(deviceID)
                try:
                    cols = typ.split()                
                    q_string = (
                        "INSERT OR REPLACE INTO charts_device (id, model) "
                        "VALUES ("+str(deviceID)+",'"+str(cols[2])+"')")
                    log("Executing: "+q_string)
                    self._db_connection.execute(q_string)
                    self._db_connection.commit()
                except sqlite3.OperationalError as ex:
                    log("Database is locked!")
                    print str(type(ex))+str(ex)

    def poll_devices(self):
        for device_id in self._slaves:
            new_row = self.request_data_from_device(device_id)
            log("Read row %s" % new_row)

            if new_row != None and check_daten(new_row):
                try:
                    cols = new_row.split()
                    line_power = cols[7]
                    update_bell_counter(line_power)
                    tup = ",".join(cols[2:10])

                    q_string = (
                        "INSERT INTO charts_solarentrytick "
                        "VALUES (NULL, datetime('now') ,"+str(device_id)+"," + tup + ")")
                    log("Executing: "+q_string)
                    #this might fail if the database is currently accessed by another process
                    try:
                        self._db_connection.execute(q_string)
                        self._db_connection.commit()
                    except sqlite3.OperationalError as ex:
                        log("Database is locked!")
                        print str(type(ex))+str(ex)
                except Exception as ex: 
                    print str(type(ex))+str(ex)
                except Error as err:
                    print type(err)
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
