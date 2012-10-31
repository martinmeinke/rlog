import mqtt, time

test = mqtt.mqtt()
test.subscribe("foo", 0)
test.startMQTT()
test.subscribe("test", 0)
def foo(message):
  print "and here it comes", message.payload

time.sleep(10)
print "changed message callback"
test.on_message = foo
time.sleep(1)
test.unsubscribe("test")


try:
  while(True):
    time.sleep(1)

# handle app closure
except (KeyboardInterrupt):
  print "Interrupt received"
  test.stopMQTT()
  time.sleep(1)
