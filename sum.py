#! /usr/bin/python
import mqtt, time

MQTT_HOST = "127.0.0.1"
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
	mqttPublisher.publish("/devices/RLog/controls/Erzeugung", str(WRsum) + "W", 0, True)
	mqttPublisher.publish("/devices/RLog/controls/Nutzung", str(SMsum) + "W", 0, True)
	if diff < 0:
		mqttPublisher.publish("/devices/RLog/controls/Bilanz", str(-diff) + "W Bezug", 0, True)
	else:
		mqttPublisher.publish("/devices/RLog/controls/Bilanz", str(diff) + "W Einspeisung", 0, True)	


mqttPublisher = mqtt.mqtt(MQTT_HOST)
mqttPublisher.startMQTT()
mqttPublisher.on_message = on_message
mqttPublisher.subscribe("/devices/RLog/controls/+", 0)
mqttPublisher.publish("/devices/RLog/controls/Erzeugung/meta/type", "text", 0, True)
mqttPublisher.publish("/devices/RLog/controls/Nutzung/meta/type", "text", 0, True)
mqttPublisher.publish("/devices/RLog/controls/Bilanz/meta/type", "text", 0, True)

while(True):
	time.sleep(3)
