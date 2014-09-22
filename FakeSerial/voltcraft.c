#define _XOPEN_SOURCE
#include <stdlib.h>
#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>
#include <string>

std::string smartMeterMessage("# 1-0:1.8.0*255(00300.00*kWh)\r\n"\
	"1-0:2.1.7*255(1.1*kWh)\r\n"\
	"1-0:4.1.7*255(2.2*kWh)\r\n"\
	"1-0:6.1.7*255(3.3*kWh)\r\n"\
	"1-0:21.7.255*255(4.4*kW)\r\n"\
	"1-0:41.7.255*255(5.5*kW)\r\n"\
	"1-0:61.7.255*255(6.6000*kW)\r\n"\
	"1-0:1.7.255*255(7.7000*kW)\r\n"\
	"1-0:96.5.5*255(q)\r\n"\
	"0-0:96.1.255*255(11401476)\r\n"\
	"\r\n");


int main(int argc, char *argv[]) {
	int pt;

	pt = open("/dev/ptmx", O_RDWR | O_NOCTTY);
	if (pt < 0) {
		perror("open /dev/ptmx");
		return 1;
	}

	grantpt(pt);
	unlockpt(pt);

	fprintf(stderr, "Smart Meter device: %s\n", ptsname(pt));

	while (1) {
		write(pt, smartMeterMessage.c_str(), smartMeterMessage.length());
		sleep(2);
	}

	return 0;
}
