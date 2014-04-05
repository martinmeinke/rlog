#include <string>
#include <vector>
#include <SerialPort.h>
#include <memory>

#ifndef UTIL_H
#define UTIL_H

std::string& ltrim(std::string& s);
std::string& rtrim(std::string& s);
std::string& trim(std::string& s);

std::vector<std::string> split(const std::string &s, char delim);

class BaseSerialReader{
public:
	virtual ~BaseSerialReader();
	virtual std::vector<std::string> read() = 0;
	virtual bool openDevice(const std::string path) = 0;
protected:
	char pollSerialPort(int timeout = 1000);
	bool openPort(const std::string& path);
	std::shared_ptr<SerialPort> serialPort;
};

#endif
