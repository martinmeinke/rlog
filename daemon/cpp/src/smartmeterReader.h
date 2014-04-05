#include "util.h"

#ifndef SMARTMETER_READER_H
#define SMARTMETER_READER_H

class SmartmeterReader: public BaseSerialReader {
public:
	std::vector<std::string> read();
	bool openDevice(const std::string path);
private:
	std::string readData();
	bool dataValid(const std::string& data);
};

#endif
