#include "rlogd.h"
#include <csignal>
#include <getopt_pp.h>
#include <thread>
#include <chrono>
#include "log.h"

using namespace std;

bool RLogd::running = true;

void signal_handler(int signal){
	RLogd::running = false;
}

int main(int argc, char* argv[]) {
	FILELog::ReportingLevel() = logDEBUG;
	FILELog::ReplaceLineEndings() = true;
	FILE* log_fd = fopen("home/pi/rlogd.log", "a");
	Output2FILE::Stream() = log_fd;
	RLogd rlog("/home/pi/test.db", "localhost", 1883, "testClient1");
	signal(SIGINT, signal_handler);
	rlog.init();
	rlog.start();
	exit(0);
}
