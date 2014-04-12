#include "smartmeterReader.h"
#include "log.h"
#include "util.h"
#include <exception>
#include <vector>
#include <string>
#include <chrono>
#include <thread>

using namespace std;

SmartmeterReader::SmartmeterReader() :
				BaseSerialReader(), start_regex(R"raw(1-0:1\.8\.0\*255)raw"),
				end_regex(R"raw(0-0:96\.1\.255\*255)raw"),
				reading_regex(R"raw(1-0:1\.8\.0\*255\(([0-9]+\.[0-9]+)\*kWh\))raw"),
				phase1_regex(R"raw(1-0:21\.7\.255\*255\(([0-9]+\.[0-9]+)\*kW\))raw"),
				phase2_regex(R"raw(1-0:41\.7\.255\*255\(([0-9]+\.[0-9]+)\*kW\))raw"),
				phase3_regex(R"raw(1-0:61\.7\.255\*255\(([0-9]+\.[0-9]+)\*kW\))raw"){

}

// Read data from the smart meter. Return string vector where first entry is about total reading and following three are about phase 1 to 3
vector<string> SmartmeterReader::read() {
	vector<string> ret;
	ret.resize(4);
	string data = readData();
	if (dataValid(data)) {
		boost::smatch match;
		if (boost::regex_search(data, match, reading_regex))
			ret.push_back(match[1]);
		else
			return vector<string>();

		if (boost::regex_search(data, match, phase1_regex))
			ret.push_back(match[1]);
		else
			return vector<string>();

		if (boost::regex_search(data, match, phase2_regex))
			ret.push_back(match[1]);
		else
			return vector<string>();

		if (boost::regex_search(data, match, phase3_regex))
			ret.push_back(match[1]);
		else
			return vector<string>();

	}
	return ret;
}

bool SmartmeterReader::openDevice(const string path) {
	serialPort.reset(new SerialPort(path));
	try {
		serialPort->Open(SerialPort::BAUD_9600, SerialPort::CHAR_SIZE_7,
				SerialPort::PARITY_EVEN, SerialPort::STOP_BITS_1,
				SerialPort::FLOW_CONTROL_DEFAULT);
	} catch (exception &e) {
		FILE_LOG(logWARNING) << "Can't open smartmeter serial port " << path
				<< " because of " << e.what();
		return false;
	}
	if (dataValid(readData()))
		return true;
	return false;
}


string SmartmeterReader::readData() {
		try{
			serialPort->Write(string("/?!\r\n"));
			// may read the string that the smartmeter is sending but I'm not interested in the content -> just for timing reasons
			this_thread::sleep_for(chrono::milliseconds(200));
			// send ACK
			serialPort->Write(string(1, 6));
			// wait a bit (may be optional)
			this_thread::sleep_for(chrono::milliseconds(200));
			// send command to get data
			serialPort->Write(string("050\r\n"));
		} catch (runtime_error& e){
			return string();
		}
		return readMessage();
}

string SmartmeterReader::readMessage() {
	string buffer, data("1-0:1.8.0*255");
	try {
		// skip everything until total reading OBIS
		while (not boost::regex_search(buffer, start_regex)) {
			buffer += string(1, serialPort->ReadByte(2000));
		}
		// skip everything until serial number OBIS
		while (not boost::regex_search(data, end_regex)) {
			data += string(1, serialPort->ReadByte(2000));
		}
		// read until return character
		while (data.compare(data.length() - 1, 1, "\n") != 0) {
			data += string(1, serialPort->ReadByte(2000));
		}
	} catch (runtime_error& e) {
		data.clear();
	}
	return data;
}

bool SmartmeterReader::dataValid(const string& data) {
	// in my test there where 10 non-empty elements
	if (int c = split(data, '\n').size() != 10) {
		FILE_LOG(logWARNING)
				<< "Read smart meter datagram with invalid structure. datagram is: "
				<< data << ". Number of elements (should be 11): " << c;
		return false;
	}
	return true;
}
