all: util.o mqtt.o rlogd.o inverter.o smartmeter.o main.o
	g++ -o "rlogd" util.o mqtt.o rlogd.o inverter.o smartmeter.o main.o -L/usr/local/lib -L/usr/lib/getoptpp -lsqlite3 -lpthread -lgetopt_pp -lserial -lpaho-mqtt3a --std=c++11 -ggdb -Wall

inverter.o: src/inverterReader.cpp src/inverterReader.h
	g++ -o "inverter.o" -c src/inverterReader.cpp -Isrc -I/usr/local/include -O0 -fstack-protector-all -std=c++11 -ggdb -Wall

smartmeter.o: src/smartmeterReader.cpp src/smartmeterReader.h
	g++ -o "smartmeter.o" -c src/smartmeterReader.cpp -Isrc -I/usr/local/include -O0 -fstack-protector-all -std=c++11 -ggdb -Wall

rlogd.o: src/rlogd.cpp
	g++ -o "rlogd.o" -c src/rlogd.cpp -Isrc -O0 -fstack-protector-all -std=c++11 -ggdb -Wall
	
mqtt.o: src/mqtt.cpp src/mqtt.h
	g++ -o "mqtt.o" -c src/mqtt.cpp -Isrc -I/usr/local/include -O0 -fstack-protector-all -std=c++11 -ggdb -Wall
	
util.o: src/util.cpp src/util.h
	g++ -o "util.o" -c src/util.cpp -Isrc -O3 -fstack-protector-all -O0 -std=c++11 -ggdb -Wall

main.o: src/main.cpp
	g++ -o "main.o" -c src/main.cpp -Isrc -O3 -fstack-protector-all -I/usr/include/getoptpp -O0 -std=c++11 -ggdb -Wall
    
dependencies: submodules clean_dependencies libserial paho getopt

libserial:
	cd libserial-0.5.2; \
	./configure && \
	make && \
	make install

paho:
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
	
	
clean:
	rm -f *.o rlogd
	
clean_dependencies: clean_getopt clean_paho clean_libserial

clean_paho:
	cd org.eclipse.paho.mqtt.c; \
	make clean \

clean_libserial:
	cd libserial-0.5.2; \
	make clean

clean_getopt:
	cd getoptpp; \
	make clean
