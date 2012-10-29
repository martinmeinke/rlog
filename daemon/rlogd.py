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

DEBUG = False

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))

DATABASE = PROJECT_PATH+"/../sensor.db"
SP = "/dev/ttyUSB"
DebugSP = "/dev/pts/7"

SOUND = ""
KWHPERRING = 1
NEXTRING = 1

bellcounter = 0

def log(msg):
    print "["+str(datetime.datetime.now())+"]: "+msg

def discover_device():
    global SP
    for devID in range(99):
        log("Checking if %s%d exists..." % (SP,devID))
        if os.path.exists("%s%d" % (SP,devID)):
            SP = "%s%d" % (SP,devID)
            log("Using device: %s" % SP)
            break
    return
        
def validRow(tup):
    num_chars = len(tup)
    if num_chars == 64:
        return True
    elif num_chars > 0:
        log("Wrong string length! String length is: %d" % num_chars)

    return False

#check if we need to play the sound
def updateBellCounter(val):
    global NEXTRING   
    global bellcounter
    bellcounter += (float(val) / 360)
    
    if(bellcounter > NEXTRING):
        ringBell()
        NEXTRING = NEXTRING + KWHPERRING
    
    log("""Bellcount: %s 
Nextring: %s""" % (str(bellcounter),str(NEXTRING)))
    
    return

#trigger playsound tool 
def ringBell():  
    test=commands.getoutput("playsound "+SOUND)
    log(test)
    return


class RLogDaemon(Daemon):
    def run(self):
        connection = sqlite3.connect(DATABASE)
        c = connection.cursor()

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
            ser = serial.Serial(DebugSP, 9600, timeout=60)
        else:
            ser = discover_device()
            ser = serial.Serial(SP)
            ser.timeout = 60
        
        dRow = "*010   4 353.9  0.28    99 231.2  0.27    59  25   1760 k 2500xi"
        while True:
            if validRow(dRow):
                cols = dRow.split()
                updateBellCounter(cols[7])

                tup = ",".join(cols[2:9])

                deviceID = int(re.search('(?<=#)..','#010').group(0))
                qString = "INSERT INTO solar VALUES(NULL," + str(time.time()) + ","+str(deviceID)+"," + tup + ")"
                log(qString)
                c.execute(qString)
                connection.commit()
            
            dRow = "*010   4 353.9  0.28    99 231.2  0.27    59  25   1760 k 2500xi"
            time.sleep(10)

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