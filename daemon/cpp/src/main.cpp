#include "rlogd.h"
#include <csignal>
#include <getopt_pp.h>
#include <thread>
#include <chrono>
#include "log.h"
#include <iostream>

using namespace std;
using namespace GetOpt;


bool RLogd::running = true;

void signal_handler(int signal){
	RLogd::running = false;
}

void printUsage(){
	cout << "USAGE: rlogd [options]\n\nOptions:" << endl
		 << "  --help, -h\t\tPrint usage and exit." << endl
		 << "  --inverter, -i\tComma separated list of inverter bus IDs. Default \"1,2,3\"" << endl
		 << "  --database, -d\tPath to database file. Default /home/pi/git/rlog/sensor.db" << endl
		 << "  --logfile, -l\t\tPath to log file. Default /home/pi/git/rlog/rlogd.log" << endl
		 << "  --broker, -b\t\tHostname of MQTT broker. Default 127.0.0.1" << endl
		 << "  --brokerPort, -p\tPort of the MQTT broker. Default 1883" << endl
		 << "  --clientId, -c\tThe MQTT client ID to be used. Default \"rlogd\"" << endl
		 << "  --deviceBaseName, -n\tThe common prefix of USB-Serial adapter. Default /dev/ttyUSB" << endl
		 << "  --interval, -t\tDelay between readings in milliseconds. Default 10000" << endl
	 	 << "  --maxDeviceID, -m\tMaximum ID of USB device to look for serial ports on. Default 1" << endl;

}

int main(int argc, char* argv[]) {
	string broker = "127.0.0.1";
	string inverter = "1,2,3";
	uint16_t brokerPort = 1883;
	string database = "/home/pi/git/rlog/sensor.db";
	string logfile = "/home/pi/git/rlog/rlogd.log";
	string clientID = "rlogd";
	string deviceBaseName = "/dev/ttyUSB";
	unsigned int interval = 10000;
	unsigned short maxDeviceID = 1;
	bool help = false;

	GetOpt_pp ops(argc, argv);

	ops >> Option('i', "inverter", inverter, "1,2,3");
	ops >> Option('d', "database", database, "/home/pi/git/rlog/sensor.db");
	ops >> Option('l', "logfile", logfile, "/home/pi/git/rlog/rlogd.log");
	ops >> Option('b', "broker", broker, "127.0.0.1");
	ops >> Option('p', "brokerPort", brokerPort);
	ops >> Option('c', "clientId", clientID, "rlogd");
	ops >> Option('n', "deviceBaseName", deviceBaseName, "/dev/ttyUSB");
	ops >> Option('t', "interval", interval);
	ops >> Option('m', "maxDeviceID", maxDeviceID);


	ops >> OptionPresent('h', "help", help);

	if (help) {
		printUsage();
		return 0;
	}


	FILELog::ReportingLevel() = logDEBUG;
	FILELog::ReplaceLineEndings() = true;
	FILE* log_fd = fopen(logfile.c_str(), "a");
	Output2FILE::Stream() = log_fd;
	cerr << "logging initialized to file " << logfile << endl;
	RLogd rlog(database, broker, brokerPort, clientID, deviceBaseName, inverter, interval, maxDeviceID);
	cerr << "rlog created" << endl;
	signal(SIGINT, signal_handler);
	rlog.init();
	cerr << "init successful" << endl;
	rlog.start();
	exit(0);
}
