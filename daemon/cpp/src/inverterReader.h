#include "util.h"

#ifndef INVERTER_READER_H
#define INVERTER_READER_H

class InverterReader: public BaseSerialReader {
public:
	std::vector<std::string> read();
	bool openDevice(const std::string path);
private:
	std::string readType();
	std::string readData();
	bool typeValid(const std::string& type);
	bool dataValid(const std::string& data);
};

#endif
