extern "C" {
#include <MQTTAsync.h>
}
#include <cstddef>
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
	std::function<void()> UnsubscribeCallback;
	std::function<
			void(std::string topic, std::string payload, int QoS, bool retained)> MessageCallback;
	std::function<void()> DisconnectCallback;
	std::function<void(int rc, std::string desc)> ConnectFailureCallback;
	std::function<void(int rc, std::string desc)> SubscribeFailureCallback;
	std::function<void(int rc, std::string desc)> UnsubscribeFailureCallback;
	std::function<void(int rc, std::string desc)> DisconnectFailureCallback;
	std::function<void(std::string desc)> ConnectionLostCallback;

	void publish(std::string& topic, std::string& payload, int Qos = 0,
			bool retained = false);
	void connect(unsigned int pingTimeout = 60, bool cleanSession = false);
	void disconnect();
	template<typename Cont>
	void subscribe(Cont const &topics, int QoS = 0);
	template<std::size_t N>
	void subscribe(const char (&topic)[N], int QoS = 0);
	template<typename Cont>
	void unsubscribe(Cont const &topics);
	template<std::size_t N>
	void unsubscribe(const char (&topic)[N]);
	bool isConnected() const;

private:
	static void onConnect(void* context, MQTTAsync_successData*);
	static void onSubscribe(void* context, MQTTAsync_successData* response);
	static void onUnsubscribe(void* context, MQTTAsync_successData* response);
	static int onMessage(void *context, char * topicName, int topicLen,
			MQTTAsync_message * message);
	static void onDisconnect(void* context, MQTTAsync_successData*);
	static void onConnectFailure(void* context, MQTTAsync_failureData*);
	static void onDisconnectFailure(void* context, MQTTAsync_failureData*);
	static void onSubscribeFailure(void* context, MQTTAsync_failureData*);
	static void onUnsubscribeFailure(void* context, MQTTAsync_failureData*);
	static void onConnectionLost(void * context, char * cause);

	bool connected;
	std::string hostname;
	unsigned short port;
	std::string clientId;
	MQTTAsync mqttClient;

};

template<typename Cont>
inline void MQTT_Client::subscribe(Cont const &topics, int QoS) {
	for (const std::string& topic : topics)
		subscribe(topic, QoS);
}

template<>
inline void MQTT_Client::subscribe(const std::string& topic, int QoS) {
	MQTTAsync_responseOptions subscribeOpts =
	MQTTAsync_responseOptions_initializer;
	subscribeOpts.onFailure = &MQTT_Client::onSubscribeFailure;
	subscribeOpts.onSuccess = &MQTT_Client::onSubscribe;
	subscribeOpts.context = this;
	int rc;
	if ((rc = MQTTAsync_subscribe(mqttClient, const_cast<char*>(topic.c_str()),
			QoS, &subscribeOpts)) != MQTTASYNC_SUCCESS) {
		throw std::runtime_error(
				"Subscribing failed with return code: " + std::to_string(rc));
	}
}

template<std::size_t N>
inline void MQTT_Client::subscribe(const char (&topic)[N], int QoS) {
	subscribe(std::string(topic), QoS);
}

template<typename Cont>
inline void MQTT_Client::unsubscribe(Cont const &topics) {
	for (const std::string& topic : topics)
		unsubscribe(topic);
}

template<>
inline void MQTT_Client::unsubscribe(const std::string& topic) {
	MQTTAsync_responseOptions unsubscribeOpts =
	MQTTAsync_responseOptions_initializer;
	unsubscribeOpts.onFailure = &MQTT_Client::onUnsubscribeFailure;
	unsubscribeOpts.onSuccess = &MQTT_Client::onUnsubscribe;
	unsubscribeOpts.context = this;
	int rc;
	if ((rc = MQTTAsync_unsubscribe(mqttClient, const_cast<char*>(topic.c_str()), &unsubscribeOpts)) != MQTTASYNC_SUCCESS) {
		throw std::runtime_error(
				"Unsubscribing failed with return code: " + std::to_string(rc));
	}
}

template<std::size_t N>
inline void MQTT_Client::unsubscribe(const char (&topic)[N]) {
	unsubscribe(std::string(topic));
}

#endif
