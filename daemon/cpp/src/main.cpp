#include "rlogd.h"
#include <thread>
#include <chrono>

using namespace std;

int main(int argc, char* argv[]) {
	RLogd rlog("/home/stephan/test.db", "192.168.11.50", 1883, "testClient1");
	rlog.start();
	this_thread::sleep_for(chrono::seconds(30));
	rlog.stop();
	this_thread::sleep_for(chrono::seconds(1));

	exit(0);
}
