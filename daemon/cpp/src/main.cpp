#include "rlogd.h"
#include <getopt_pp.h>
#include <thread>
#include <chrono>
#include "log.h"

using namespace std;

int main(int argc, char* argv[]) {
	FILELog::ReportingLevel() = logDEBUG;
	FILELog::ReplaceLineEndings() = true;
	FILE* log_fd = fopen("/home/stephan/rlogd.log", "a");
	Output2FILE::Stream() = log_fd;
	RLogd rlog("/home/stephan/test.db", "localhost", 1883, "testClient1");
	rlog.init();
	rlog.start();
	this_thread::sleep_for(chrono::seconds(1));
	rlog.stop();
	this_thread::sleep_for(chrono::milliseconds(42));
	exit(0);
}
