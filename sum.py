#!/usr/bin/env python2
import mqtt, time

MQTT_HOST = "192.168.11.54"
WRs = {"dummy" : 0}
SMs = {"dummy" : 0}

def on_message(mosquitto, message):
	device = message.topic.split("/")[4]
	if device[0] == "3":
		WRs[device] = int(message.payload)
	elif device[0] == "V":
		SMs[device] = float(message.payload)
	WRsum = reduce(lambda x, y: x + y, WRs.values())
	SMsum = reduce(lambda x, y: x + y, SMs.values())
	diff = WRsum - SMsum
	mqttPublisher.publish("/devices/RLog/controls/Erzeugung", WRsum, 0, True)
	mqttPublisher.publish("/devices/RLog/controls/Nutzung", SMsum, 0, True)
	if diff < 0:
		mqttPublisher.publish("/devices/RLog/controls/Bezug", -diff, 0, True)
		mqttPublisher.publish("/devices/RLog/controls/Einspeisung", 0, 0, True)
	else:
		mqttPublisher.publish("/devices/RLog/controls/Einspeisung", diff, 0, True)
		mqttPublisher.publish("/devices/RLog/controls/Bezug", 0, 0, True)


mqttPublisher = mqtt.mqtt(MQTT_HOST)
mqttPublisher.startMQTT()
mqttPublisher.on_message = on_message
mqttPublisher.subscribe("/devices/RLog/controls/3002IN (1)", 0)
mqttPublisher.subscribe("/devices/RLog/controls/3002IN (2)", 0)
mqttPublisher.subscribe("/devices/RLog/controls/3002IN (3)", 0)
mqttPublisher.subscribe("/devices/RLog/controls/VSM-102 (1)", 0)
mqttPublisher.subscribe("/devices/RLog/controls/VSM-102 (2)", 0)
mqttPublisher.subscribe("/devices/RLog/controls/VSM-102 (3)", 0)
mqttPublisher.publish("/devices/RLog/controls/Erzeugung/meta/type", "text", 0, True)
mqttPublisher.publish("/devices/RLog/controls/Nutzung/meta/type", "text", 0, True)
mqttPublisher.publish("/devices/RLog/controls/Einspeisung/meta/type", "text", 0, True)
mqttPublisher.publish("/devices/RLog/controls/Bezug/meta/type", "text", 0, True)

while(True):
	time.sleep(3)
