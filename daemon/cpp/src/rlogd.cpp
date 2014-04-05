#include <cstdlib>
#include "rlogd.h"
#include <iostream>
#include <functional>
#include <list>
#include <string>
#include <sqlite3.h>
#include "util.h"

using namespace std;

RLogd::RLogd(const string& database, const string& mqtt_hostname,
		const unsigned int mqtt_port, const string& mqtt_clientID) :
		mqtt(mqtt_clientID, mqtt_hostname, mqtt_port) {

}

void RLogd::init() {
	mqtt.ConnectCallback = bind(&RLogd::onConnect, this);
	mqtt.DisconnectCallback = bind(&RLogd::onDisconnect, this);
	mqtt.ConnectionLostCallback = bind(&RLogd::onConnectionLost, this,
			placeholders::_1);
	mqtt.SubscribeCallback = bind(&RLogd::onSubscribe, this, placeholders::_1);
	mqtt.MessageCallback = bind(&RLogd::onMessage, this, placeholders::_1,
			placeholders::_2, placeholders::_3, placeholders::_4);
	mqtt.UnsubscribeCallback = bind(&RLogd::onUnsubscribe, this);

	try{
		mqtt.connect();
	} catch (runtime_error &e){
		cerr << "mqtt connect failed: " << e.what() << endl;;
	}
}

void RLogd::start(){
	list<string> topics = { "/devices/Switch 1/#", "/devices/Switch 2/#" };
	try{
		mqtt.unsubscribe(topics);
	} catch (runtime_error &e){
		cerr << "mqtt unsubscribe error: " << e.what() << endl;;
	}
}

void RLogd::stop() {
	try{
		mqtt.disconnect();
	} catch (runtime_error &e){
		cerr << "mqtt disconnect  error: " << e.what() << endl;;
	}
}

void RLogd::test() {
	if(invReader.openDevice("/dev/ttyUSB0"))
		while(true){
			auto ret = invReader.read();
			if(ret.size())
				for (auto c : ret)
					cout << "read:" << trim(c) << endl;;
		}
	else
		cerr << "can't open arduino" << endl;

}

void RLogd::onConnect() {
	cout << "MQTT connected" << endl;
	mqtt.subscribe("/devices/RLog/controls/Erzeugung");
	mqtt.subscribe(string("/devices/RLog/controls/Nutzung"));
	list<string> topics = { "/devices/Switch 1/#", "/devices/Switch 2/#",
			"/devices/Switch 3/#" };
	mqtt.subscribe(topics);
}

void RLogd::onDisconnect() {
	cout << "MQTT disconnected" << endl;
}

void RLogd::onConnectionLost(string reason) {
	cout << "MQTT connection lost because of " << reason << endl;
}

void RLogd::onSubscribe(int QoS) {
	cout << "MQTT subscribed with QoS " << QoS << endl;
}

void RLogd::onMessage(std::string topic, std::string payload, int QoS,
		bool retained) {
	cout << string(retained ? "Retained " : "")
			<< "MQTT message received with QoS " << QoS << " on topic " << topic
			<< ": " << payload << endl;
}

void RLogd::onUnsubscribe() {
	cout << "MQTT unsubscribed with QoS " << endl;
}
