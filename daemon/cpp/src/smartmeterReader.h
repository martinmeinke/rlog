#include "util.h"

#ifndef SMARTMETER_READER_H
#define SMARTMETER_READER_H

class SmartmeterReader : public BaseSerialReader{
public:
	SmartmeterReader();
	std::vector<std::string> read();
private:
	bool openDevice(std::string path);
	std::string readData();
	bool dataValid(std::string& data);
};

#endif
