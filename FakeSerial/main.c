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

	fprintf(stderr, "Slave device: %s\n", ptsname(pt));

	while (1) {
		write(pt, "\n*030   4 355.9  2.92  1039 239.5  4.12   974  40   3229 « 5000xi\r", 66);
		sleep(1);
	}

	return 0;
}
