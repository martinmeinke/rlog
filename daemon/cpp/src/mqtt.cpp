#include "mqtt.h"

using namespace std;

MQTT_Client::MQTT_Client(const string& clientID, const string& hostname,
		unsigned short port) :
		connected(false), hostname(hostname), port(port), clientId(clientID) {
	string address = "tcp://" + hostname + ":" + to_string(port);
	MQTTAsync_create(&mqttClient, const_cast<char*>(address.c_str()),
			const_cast<char*>(clientId.c_str()), MQTTCLIENT_PERSISTENCE_NONE,
			NULL);
}

void MQTT_Client::onDisconnectFailure(void* context,
		MQTTAsync_failureData* ret) {
	if (context) {
		MQTT_Client* client = reinterpret_cast<MQTT_Client*>(context);
		client->connected = true;
		if (client->DisconnectFailureCallback)
			client->DisconnectFailureCallback(ret->code, string(ret->message));
	}
}

MQTT_Client::~MQTT_Client() {
	disconnect();
	MQTTAsync_destroy(&mqttClient);
}

void MQTT_Client::onConnectionLost(void* context, char* cause) {
	if (context) {
		MQTT_Client* client = reinterpret_cast<MQTT_Client*>(context);
		client->connected = false;
		if (client->ConnectionLostCallback)
			client->ConnectionLostCallback(cause ? string(cause) : string(""));
	}
}

void MQTT_Client::onDisconnect(void* context, MQTTAsync_successData* ret) {
	if (context) {
		MQTT_Client* client = reinterpret_cast<MQTT_Client*>(context);
		client->connected = false;
		if (client->DisconnectCallback)
			client->DisconnectCallback();
	}
}

void MQTT_Client::onConnectFailure(void* context, MQTTAsync_failureData* ret) {
	if (context) {
		MQTT_Client* client = reinterpret_cast<MQTT_Client*>(context);
		client->connected = false;
		if (client->ConnectFailureCallback)
			client->ConnectFailureCallback(ret->code, string(ret->message));
	}
}

void MQTT_Client::onSubscribeFailure(void* context,
		MQTTAsync_failureData* ret) {
	if (context) {
		MQTT_Client* client = reinterpret_cast<MQTT_Client*>(context);
		if (client->SubscribeFailureCallback)
			client->SubscribeFailureCallback(ret->code, string(ret->message));
	}
}

void MQTT_Client::onUnsubscribeFailure(void* context,
		MQTTAsync_failureData* ret) {
	if (context) {
		MQTT_Client* client = reinterpret_cast<MQTT_Client*>(context);
		if (client->UnsubscribeFailureCallback)
			client->UnsubscribeFailureCallback(ret->code, string(ret->message));
	}
}

void MQTT_Client::onConnect(void* context, MQTTAsync_successData* ret) {
	if (context) {
		MQTT_Client* client = reinterpret_cast<MQTT_Client*>(context);
		client->connected = true;
		if (client->ConnectCallback)
			client->ConnectCallback();
	}
}

int MQTT_Client::onMessage(void* context, char* topicName, int topicLen,
		MQTTAsync_message* message) {
	if (context) {
		MQTT_Client* client = reinterpret_cast<MQTT_Client*>(context);
		if (client->MessageCallback)
			client->MessageCallback(string(topicName, topicLen),
					string(static_cast<char*>(message->payload),
							message->payloadlen), message->qos,
					message->retained);
		MQTTAsync_free(topicName);
		MQTTAsync_freeMessage(&message);
		return 1;
	} else
		return 0;
}

void MQTT_Client::publish(string& topic, string& payload, int QoS,
		bool retained) {
	MQTTAsync_responseOptions opts = MQTTAsync_responseOptions_initializer;
	MQTTAsync_message pubmsg = MQTTAsync_message_initializer;
	opts.context = mqttClient;
	pubmsg.payload = static_cast<void*>(const_cast<char*>(payload.c_str()));
	pubmsg.payloadlen = payload.length();
	pubmsg.qos = QoS;
	pubmsg.retained = retained;
	int rc;
	if ((rc = MQTTAsync_sendMessage(mqttClient,
			const_cast<char*>(topic.c_str()), &pubmsg, &opts))
			!= MQTTASYNC_SUCCESS)
		throw runtime_error(
				"MQTT publish failed with return code: " + to_string(rc));
}

void MQTT_Client::connect(unsigned int pingTimeout, bool cleanSession) {
	MQTTAsync_setCallbacks(mqttClient, this, &MQTT_Client::onConnectionLost,
			&MQTT_Client::onMessage, NULL);
	MQTTAsync_connectOptions conn_opts = MQTTAsync_connectOptions_initializer;
	conn_opts.keepAliveInterval = pingTimeout;
	conn_opts.cleansession = cleanSession;
	conn_opts.onSuccess = &MQTT_Client::onConnect;
	conn_opts.onFailure = &MQTT_Client::onConnectFailure;
	conn_opts.context = this;
	int rc;
	if ((rc = MQTTAsync_connect(mqttClient, &conn_opts)) != MQTTASYNC_SUCCESS) {
		throw runtime_error(
				"MQTT connect failed with return code " + to_string(rc));
	}
}

void MQTT_Client::disconnect() {
	int rc;
	MQTTAsync_disconnectOptions opts = MQTTAsync_disconnectOptions_initializer;
	opts.onSuccess = &MQTT_Client::onDisconnect;
	opts.context = this;
	opts.onFailure = &MQTT_Client::onDisconnectFailure;
	if ((rc = MQTTAsync_disconnect(mqttClient, &opts)) != MQTTASYNC_SUCCESS) {
		throw runtime_error("Failed to disconnect. Return code: " + to_string(rc));
	}
}

void MQTT_Client::onSubscribe(void* context, MQTTAsync_successData* response) {
	if (context) {
		MQTT_Client* client = reinterpret_cast<MQTT_Client*>(context);
		if (client->SubscribeCallback)
			client->SubscribeCallback(response->alt.qos);
	}
}


void MQTT_Client::onUnsubscribe(void* context, MQTTAsync_successData* response) {
	if (context) {
		MQTT_Client* client = reinterpret_cast<MQTT_Client*>(context);
		if (client->UnsubscribeCallback)
			client->UnsubscribeCallback();
	}
}


bool MQTT_Client::isConnected() const {
	return connected;
}
