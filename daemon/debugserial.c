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
		write(pt,
				"00.00.0000 09:22:20   4 357.5  0.39   139 230.3  0.45   106  31\n",
				64);
		sleep(10);
	}

	return 0;
}
