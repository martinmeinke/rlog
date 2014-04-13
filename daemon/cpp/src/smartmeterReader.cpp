#include "smartmeterReader.h"
#include "log.h"
#include "util.h"
#include <exception>
#include <vector>
#include <string>
#include <chrono>
#include <thread>
#include <iostream>

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
	try{
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
	} catch (exception& e){
		FILE_LOG(logERROR) << "smartmeter reader error: " << e.what();
		cerr << "smartmeter reader error: " << e.what() << endl;
	}
	return ret;
}

bool SmartmeterReader::openDevice(const string path) {
	serialPort.reset(new SerialPort(path));
	try {
		serialPort->Open(SerialPort::BAUD_9600, SerialPort::CHAR_SIZE_7,
				SerialPort::PARITY_EVEN, SerialPort::STOP_BITS_1,
				SerialPort::FLOW_CONTROL_NONE);
	} catch (exception &e) {
		FILE_LOG(logWARNING) << "Can't open smartmeter serial port at " << path
				<< " because of " << e.what();
		cerr << "Can't open smartmeter serial port at " << path
				<< " because of " << e.what() << endl;
		return false;
	}
	if (dataValid(readData()))
		return true;
	return false;
}


string SmartmeterReader::readData() {
	try{
		serialPort->Write(string("/?!\r\n"));
		try{
			while(true){
				serialPort->ReadByte(1000);
			}
		} catch (runtime_error& e){
			// cerr << "read smartmeter answer timed out" << endl;
		}
		// write ACK
		serialPort->Write(string(1, 6));
		// wait a bit
		this_thread::sleep_for(chrono::milliseconds(500));
		// send read command
		serialPort->Write(string("050\r\n"));
	} catch (runtime_error& e){
		FILE_LOG(logERROR) << "smartmeter command writing error: " << e.what();
		cerr << "smartmeter command writing error: " << e.what() << endl;
		return string();
	}
	return readMessage();
}

string SmartmeterReader::readMessage() {
	string buffer, data("1-0:1.8.0*255");
	try {
		// skip everything until total reading OBIS
		while (not boost::regex_search(buffer, start_regex))
			buffer += string(1, serialPort->ReadByte(1000));
		// skip everything until serial number OBIS
		while (not boost::regex_search(data, end_regex))
			data += string(1, serialPort->ReadByte(1000));
		// read until return character
		while (data.compare(data.length() - 1, 1, "\n") != 0)
			data += string(1, serialPort->ReadByte(1000));
		// write ACK
		serialPort->Write(string(1, 6));
	} catch (runtime_error& e) {
		FILE_LOG(logERROR) << "smartmeter read message failed: " << e.what();
		cerr << "smartmeter read message failed: " << e.what() << endl;
		data.clear();
	}
	return data;
}

bool SmartmeterReader::dataValid(const string& data) {
	// in my test there where 10 non-empty elements
	if (int c = split(data, '\n').size() != 10) {
		FILE_LOG(logWARNING)
				<< "Read smart meter datagram with invalid structure. datagram is: "
				<< data << ". Number of elements (should be 10): " << c;
		cerr << "Read smart meter datagram with invalid structure. datagram is: "
				<< data << ". Number of elements (should be 10): " << c << endl;
		return false;
	}
	return true;
}
