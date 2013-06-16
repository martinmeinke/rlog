import sqlite3
import random
import time
import mqtt

db_connection = sqlite3.connect("sensor.db")
db_cursor  = db_connection.cursor()
MQTT_HOST = "192.168.8.34"

print "starting MQTT"
try:
    mqttPublisher = mqtt.mqtt(broker = MQTT_HOST)
    mqttPublisher.startMQTT()
except Exception as e:
    print "mqtt start problem:" + str(e)

while True:
    statements = []
    for dId in range(1,4):
        rand = random.randint(80, 120) * dId
        statements.append([dId, 1, 1, 1, 1, 1, rand, 10, 500])
        try:
            mqttPublisher.publish("/devices/RLog/controls/WR (" + str(dId) + ")", str(rand), 0, True)
        except Exception as e:
            print "line 25", str(e)
    if statements:
        try:
            db_cursor.executemany("INSERT INTO charts_solarentrytick VALUES (NULL, datetime('now', 'localtime'), ?, ?, ?, ?, ?, ?, ?, ?, ?)", statements)
            db_connection.commit()
        except sqlite3.OperationalError as ex:
            print "Database is locked or some other DB error!"
            print str(type(ex))+str(ex)
	time.sleep(10)
