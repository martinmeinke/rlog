extern "C" {
#include <MQTTAsync.h>
}
#include <string>
#include <functional>

#ifndef MQTT_CLIENT_H
#define MQTT_CLIENT_H

class MQTT_Client {
public:
	explicit MQTT_Client(const std::string& clientID = "MQTTcpp",
			const std::string& hostname = "localhost", unsigned short port =
					1883);
	~MQTT_Client();

	std::function<void()> ConnectCallback;
	std::function<void(int QoS)> SubscribeCallback;
	std::function<
			void(std::string topic, std::string payload, int QoS, bool retained)> MessageCallback;
	std::function<void()> DisconnectCallback;
	std::function<void(int rc, std::string desc)> ConnectFailureCallback;
	std::function<void(int rc, std::string desc)> SubscribeFailureCallback;
	std::function<void(int rc, std::string desc)> DisconnectFailureCallback;
	std::function<void(std::string desc)> ConnectionLostCallback;

	void publish(std::string& topic, std::string& payload, int Qos = 0,
			bool retained = false);
	void connect();
	void disconnect();
	void subscribe(const std::string& topic, int QoS = 0);
	/*
	template<typename C>
	void subscribe(const C& topicCollection, int QoS = 0);
	*/
	bool isConnected() const;

private:
	static void onConnect(void* context, MQTTAsync_successData*);
	static void onSubscribe(void* context, MQTTAsync_successData* response);
	static int onMessage(void *context, char * topicName, int topicLen,
			MQTTAsync_message * message);
	static void onDisconnect(void* context, MQTTAsync_successData*);
	static void onConnectFailure(void* context, MQTTAsync_failureData*);
	static void onDisconnectFailure(void* context, MQTTAsync_failureData*);
	static void onSubscribeFailure(void* context, MQTTAsync_failureData*);
	static void onConnectionLost(void * context, char * cause);

	bool connected;
	std::string hostname;
	unsigned short port;
	std::string clientId;
	MQTTAsync mqttClient;

};

/*
template<typename C>
void MQTT_Client::subscribe(const C& topicCollection, int QoS) {
	for (const std::string& topic : topicCollection)
		subscribe(topic, QoS);
}
*/
#endif
