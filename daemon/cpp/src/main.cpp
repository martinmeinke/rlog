#include "rlogd.h"
#include <csignal>
#include <getopt_pp.h>
#include <thread>
#include <chrono>
#include "log.h"
#include <iostream>

using namespace std;

bool RLogd::running = true;

void signal_handler(int signal){
	RLogd::running = false;
}

int main(int argc, char* argv[]) {
	FILELog::ReportingLevel() = logDEBUG;
	FILELog::ReplaceLineEndings() = true;
	FILE* log_fd = fopen("/home/pi/rlogd.log", "a");
	Output2FILE::Stream() = log_fd;
	cerr << "logging initialized" << endl;
	RLogd rlog("/home/pi/test.db", "127.0.0.1", 1883, "testClient1");
	cerr << "rlog created" << endl;
	signal(SIGINT, signal_handler);
	rlog.init();
	cerr << "init successful" << endl;
	rlog.start();
	exit(0);
}
