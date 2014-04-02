dependencies: libserial paho getopt

libserial:
	cd libserial-0.5.2; \
	./configure && \
	make && \
	make install

paho: submodules
	cd org.eclipse.paho.mqtt.c; \
	make && \
	make install
	
getopt:
	cd getoptpp; \
	make SHARED=n && \
	make SHARED=n install

submodules:
	git submodule init 
	git submodule update
