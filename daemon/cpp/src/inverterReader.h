#include "util.h"

#ifndef INVERTER_READER_H
#define INVERTER_READER_H

class InverterReader : public BaseSerialReader{
public:
	InverterReader();
	std::vector<std::string> read();
private:
	bool openDevice(std::string path);
	std::string readType();
	std::string readData();
	bool typeValid(std::string& type);
	bool dataValid(std::string& data);
};

#endif
