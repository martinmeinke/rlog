all: mqtt.o main.o
	g++ -o "rlogd" mqtt.o main.o -L/usr/local/lib -L/usr/lib/getoptpp -lsqlite3 -lpthread -lgetopt_pp -lserial -lpaho-mqtt3a

main.o:
	g++ -o "main.o" -c src/rlogd.cpp -Isrc -I/usr/local/include -I/usr/include/getoptpp -O3 -fstack-protector-all
	
mqtt.o:
	g++ -o "mqtt.o" -c src/mqtt.cpp -Isrc -I/usr/local/include -O3 -fstack-protector-all
    
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
	make && \
	make install

submodules:
	git submodule init 
	git submodule update
