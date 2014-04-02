extern "C" {
    #include <MQTTAsync.h>
}
#include <string>

class MQTT_Client {
public:
	explicit MQTT_Client(const std::string& hostname = "localhost", unsigned short port = 1883);
private:
	void onConnectionLost(void * context, char * cause);

	void onDisconnect(void* context, MQTTAsync_successData*);

	void onConnectFailure(void* context, MQTTAsync_failureData*);

	void onSubscribeFailure(void* context, MQTTAsync_failureData*);

	void onConnect(void* context, MQTTAsync_successData*);

	int onMessage(void *context, char * topicName, int topicLen, MQTTAsync_message * message);

	void onSubscribe(void* context, MQTTAsync_successData* response);
};
