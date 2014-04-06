#include "util.h"
#include <vector>

#ifndef INVERTER_READER_H
#define INVERTER_READER_H

class InverterReader: public BaseSerialReader {
public:
	std::vector<std::string> read();
	bool openDevice(const std::string path);
private:
	std::string readType(unsigned short id = 1);
	std::string readData(unsigned short id = 1);
	std::string readMessage();
	bool typeValid(const std::string& type);
	bool dataValid(const std::string& data);
	std::vector<int> deviceIDs;
};

#endif
