#define _XOPEN_SOURCE
#include <stdlib.h>
#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
	int pt;

	pt = open("/dev/ptmx", O_RDWR | O_NOCTTY);
	if (pt < 0) {
		perror("open /dev/ptmx");
		return 1;
	}

	grantpt(pt);
	unlockpt(pt);

	fprintf(stderr, "Inverter device: %s\n", ptsname(pt));

	while (1) {
		write(pt, "\n*030   5 172.1  0.10    22 230.4  0.05    20  26   1925 C 3501xi\r", 66);
		sleep(2);
	}

	return 0;
}
