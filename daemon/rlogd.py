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

def valid_row(tup):
    if tup != None and len(tup.split())==12:
        num_chars = len(tup)
        if num_chars > 60:
            return True
        elif num_chars > 0:
            log("Read invalid row ; length is: %d" % num_chars)
    
    log("Read invalid row ; None or invalid number of cols:")
    return False

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
        self._db_cursor  = self._db_connection.cursor()

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

        RLogDaemon.KWHPERRING = sets[2]
        RLogDaemon.NEXTRING = sets[2]
        RLogDaemon.SOUND = sets[3]

        log("""Using Parameters:
    KWHPERRING: %s
    NEXTRING: %s
    SOUND: %s""" % (RLogDaemon.KWHPERRING,RLogDaemon.NEXTRING,RLogDaemon.SOUND))

        if DEBUG_ENABLED:
            self._serial_port= serial.Serial(DEBUG_SERIAL_PORT, 9600, timeout=1)
        else:
            self._serial_port = discover_device()
            self._serial_port = serial.Serial(RLogDaemon.DEVICE_NAME)
            self._serial_port.timeout = 1

        self.detect_slaves()
        
        while True:
            t1 = time.time()
            self.poll_devices()
            t2 = time.time()
            sleepduration = RLogDaemon.DELAY-(t2-t1)
            log("Sleeping: %f" % sleepduration)
            if sleepduration > 0:
              time.sleep(sleepduration)

        self._serial_port.close();

    def request_from_device(self, device_id_raw):
        device_id = "{0:02d}".format(device_id_raw)
        request_string = "#"+str(device_id)+"0\r"
        log("Asking device %s " % request_string)

        self._serial_port.write(request_string)
        self._serial_port.write(request_string)

        #read 2 lines, because they sometimes seem to buffer their output
        for i in range(2):
            a = self._serial_port.readline()
            if len(a) > 1:
                return a

        sys.stdout.flush()
        return None

    def detect_slaves(self):
        for deviceID in range(1,33):
            a = self.request_from_device(deviceID)
            if a != None:
                log("Device %d answered %s " % (deviceID, a))
                self._slaves.append(deviceID)

    def poll_devices(self):
        for device_id in self._slaves:
            new_row = self.request_from_device(device_id)
            log("Read row %s" % new_row)

            if valid_row(new_row):
                #TODO catch errors more precise 
                #Errors might occur during physical transmission 
                try:
                    cols = new_row.split()
                    line_power = cols[7]
                    update_bell_counter(line_power)
                    tup = ",".join(cols[2:10])

                    q_string = (
                        "INSERT INTO charts_solarentrytick "
                        "VALUES (NULL," + str(time.time()) + ","+str(device_id)+"," + tup + ")")

                    log("Executing: "+q_string)
                
                    q_string2 = (
                        "INSERT OR REPLACE INTO charts_device (id, model) "
                        "VALUES ("+str(device_id)+","+str(cols[12])+")")

                    #this might fail if the database is currently accessed by another process
                    try:
                        self._db_connection.execute(q_string)
                        self._db_connection.execute(q_string2)
                        self._db_connection.commit()
                    except sqlite3.OperationalError:
                        log("Database is locked!")

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
