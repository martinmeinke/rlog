#include "rlogd.h"
#include <getopt_pp.h>
#include <thread>
#include <chrono>
#include <string.h>
#include "util.h"
#include <iostream>

using namespace std;

int main(int argc, char* argv[]) {
	RLogd rlog("/home/stephan/test.db", "192.168.11.50", 1883, "testClient1");
	rlog.init();
	this_thread::sleep_for(chrono::seconds(1));
	rlog.start();
	this_thread::sleep_for(chrono::seconds(1));
	rlog.stop();
	this_thread::sleep_for(chrono::seconds(1));

	exit(0);
}
