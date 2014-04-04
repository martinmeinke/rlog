#include <string>
#include <vector>
#include <SerialStream.h>

#ifndef UTIL_H
#define UTIL_H

std::vector<std::string> split(const std::string &s, char delim);

class BaseSerialReader{
public:
	virtual ~BaseSerialReader();
	virtual std::vector<std::string> read() = 0;
protected:
	virtual bool openDevice(std::string path) = 0;
	LibSerial::SerialStream serialPort;
};

#endif
