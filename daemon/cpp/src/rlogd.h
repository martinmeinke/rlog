#include <string>
#include "mqtt.h"
#include "inverterReader.h"
#include "smartmeterReader.h"

#ifndef RLOGD_H
#define RLOGD_H

class RLogd {
public:
	explicit RLogd(const std::string& database = "/home/stephan/test.db",
			const std::string& mqtt_hostname = "localhost",
			const unsigned int mqtt_port = 1883,
			const std::string& mqtt_clientID = "MQTTRLOGD");
	void init();
	void start();
	void stop();
	void test();

private:
	void onConnect();
	void onDisconnect();
	void onConnectionLost(std::string reason);
	void onSubscribe(int QoS);
	void onUnsubscribe();
	void onMessage(std::string topic, std::string payload, int QoS,
			bool retained);

	MQTT_Client mqtt;
	InverterReader invReader;
	SmartmeterReader smReader;
};

#endif