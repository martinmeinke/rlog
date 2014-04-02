libserial:
	cd libserial-0.5.2; \
	./configure && \
	make && \
	make install

paho: submodules
	cd org.eclipse.paho.mqtt.c; \
	make && \
	make install

submodules:
	git submodule init 
	git submodule update
