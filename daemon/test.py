import mqtt, time

def myMessageCallback(message):
  print message

# make a new mqtt client. You can pass broker and port. Defaults to 127.0.0.1 (localhost) and 1883
test = mqtt.mqtt()
# add a callback that gets executed when a message arrives
  # you can also set callbacks for:
   # on_connect(return_code)
   # on_disconnect()
   # on_subscribe(message_id, qos_list)
   # on_unsubscribe(message_id)
   # on_publish(message_id)
   # on_message(message)
  # if you want but we only do that for on_message here
test.on_message = myMessageCallback
# subscribe to something (topic, Quality of Service) - there is no connection to a broker yet so the action will be queued
test.subscribe("foo", 0)
# starts the client
test.startMQTT()
# subscribe to something else
test.subscribe("test", 0)


time.sleep(3)


# function we're going to set as new on_message callback
def foo(message):
  print "and here it comes:", message.payload, "on topic:", message.topic

print "changed message callback"
test.on_message = foo


time.sleep(1)
# well, unsubscribe
test.unsubscribe("foo")

# prevent the script from exiting
try:
  while(True):
    time.sleep(1)
   # test.publish("time", time.now())

# handle app closure
except (KeyboardInterrupt):
  # unsubscribes from all subscriptions and closes connection
  test.stopMQTT()
  # just wait for the disconnect messages to appear (not really necessary)
  time.sleep(1)
