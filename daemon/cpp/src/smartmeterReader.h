#include "util.h"
#include <boost/regex.hpp>

#ifndef SMARTMETER_READER_H
#define SMARTMETER_READER_H

class SmartmeterReader: public BaseSerialReader {
public:
	SmartmeterReader();
	std::vector<std::string> read();
	bool openDevice(const std::string path);
private:
	std::string readData();
	std::string readMessage();
	bool dataValid(const std::string& data);
	// I don't think I can write more efficient FSMs than what comes out when regex compiles my expression ...
	boost::regex start_regex;
	boost::regex end_regex;
	boost::regex reading_regex; // 1-0:1.8.0*255(00000.00*kWh)
	boost::regex phase1_regex;  // 1-0:21.7.255*255(0000.0000*kW)
	boost::regex phase2_regex;  // 1-0:41.7.255*255(0000.0000*kW)
	boost::regex phase3_regex;  // 1-0:61.7.255*255(0000.0000*kW)
};

#endif
