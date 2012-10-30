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
from daemon import Daemon
import subprocess

DEBUG = False

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
DATABASE = PROJECT_PATH+"/../sensor.db"
SP = "/dev/ttyUSB"
DebugSP = "/dev/pts/7"
SOUND = ""
KWHPERRING = 1
NEXTRING = 1

DELAY = 10

bellcounter = 0

ser = None
slaves = []
connection = sqlite3.connect(DATABASE)
c = connection.cursor()

def log(msg):
    print "["+str(datetime.datetime.now())+"]: "+str(msg)

def is_ascii(s):
    return all(ord(c) < 128 for c in s)

def discover_device():
    global SP
    for devID in range(99):
        log("Checking if %s%d exists..." % (SP,devID))
        if os.path.exists("%s%d" % (SP,devID)):
            SP = "%s%d" % (SP,devID)
            log("Using device: %s" % SP)
            break
    return

def requestFromDevice(devID):
    global ser

    dev = "{0:02d}".format(devID)
    requeststring = "#"+str(dev)+"0\r"
    log("Asking device %s " % requeststring)
    ser.write(requeststring)
    ser.write(requeststring)

    #read 2 lines, because they sometimes seem to buffer their output
    for i in range(2):
        a = ser.readline()
        if len(a) > 1:
            return a

    sys.stdout.flush()
    return None

def detect_slaves():
    global slaves

    for deviceID in range(4):
        a = requestFromDevice(deviceID)
        if a != None:
            log("Device %d answered %s " % (deviceID, a))
            slaves.append(deviceID)

def validRow(tup):
    if tup != None and len(tup.split())==12:
        num_chars = len(tup)
        if num_chars > 60:
            return True
        elif num_chars > 0:
            log("Read invalid row ; length is: %d" % num_chars)
    
    log("Read invalid row ; None or invalid number of cols:")
    return False

#check if we need to play the sound
def updateBellCounter(val):
    global NEXTRING   
    global KWHPERRING
    global bellcounter

    bellcounter += (float(val) / 360000)
    
    if(bellcounter > NEXTRING):
        ringBell()
        NEXTRING = NEXTRING + KWHPERRING
    
    log("""Bellcount: %s 
Nextring: %s""" % (str(bellcounter),str(NEXTRING)))
    
    return

#trigger playsound tool 
def ringBell(): 
    global SOUND 
    #add check if sound is correctly setup (tutorial in adafruit sound pdf)
    test=os.system("mpg321 -q "+SOUND)
    log(test)
    return

def pollDevices():
    global connection
    global c

    for deviceID in slaves:
        dRow = requestFromDevice(deviceID)
        log("Read row %s" % dRow)

        if validRow(dRow):
            #TODO catch errors more precise 
            #Errors might occur during physical transmission 
            try:
                cols = dRow.split()
                updateBellCounter(cols[7])
                tup = ",".join(cols[2:9])

                qString = "INSERT INTO charts_solarentry VALUES(NULL," + str(time.time()) + ","+str(deviceID)+"," + tup + ")"
                log("Executing: "+qString)
            
                #this might fail if the database is currently accessed by another process
                try:
                    c.execute(qString)
                    connection.commit()
                except sqlite3.OperationalError:
                    log("Database is locked!")

            except Exception as ex:
                print type(ex)
            except Error as err:
                print type(err)


#TODO: pot more stuff into the class to eliminate the need for the global stuff
class RLogDaemon(Daemon):
    def run(self):
        global ser
        global slaves
        global connection
        global cursor
        global KWHPERRING
        global NEXTRING
        global SOUND
        global DELAY


        c.execute("SELECT * FROM charts_settings WHERE active = 1 ORDER BY id DESC LIMIT 1")
        
        if c.rowcount == 0:
            return

        sets = c.fetchone()

        KWHPERRING = sets[2]
        NEXTRING = sets[2]
        SOUND = sets[3]

        log("""Using Parameters:
    KWHPERRING: %s
    NEXTRING: %s
    SOUND: %s""" % (KWHPERRING,NEXTRING,SOUND))

        if DEBUG:
            ser = serial.Serial(DebugSP, 9600, timeout=1)
        else:
            ser = discover_device()
            ser = serial.Serial(SP)
            ser.timeout = 1

        detect_slaves()
        
        while True:
            t1 = time.time()
            pollDevices()
            t2 = time.time()
            #nicht unbedingt so genau, aber sollte passen...
            time.sleep(((DELAY*1000000)-(t2-t1))/1000000)

        ser.close();

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
