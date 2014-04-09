#include "smartmeterReader.h"
#include "log.h"
#include <exception>

using namespace std;

SmartmeterReader::SmartmeterReader() :
		BaseSerialReader(), start_regex("1-0:1\\.8\\.0\\*255"), end_regex(
				"0-0:96\\.1\\.255\\*255"), reading_regex("1-0:1\\.8\\.0\\*255\\(([0-9]+\\.[0-9]+)\\*kWh\\)"),
				phase1_regex("1-0:21\\.7\\.255\\*255\\(([0-9]+\\.[0-9]+)\\*kW\\)"),
				phase2_regex("1-0:41\\.7\\.255\\*255\\(([0-9]+\\.[0-9]+)\\*kW\\)"),
				phase3_regex("1-0:61\\.7\\.255\\*255\\(([0-9]+\\.[0-9]+)\\*kW\\)"){

}

vector<string> SmartmeterReader::read() {
	string data = readData();
	if (dataValid(data))
		return split(data, ' ');
	else
		return vector<string>();
}

bool SmartmeterReader::openDevice(const string path) {
	serialPort.reset(new SerialPort(path));
	try {
		serialPort->Open(SerialPort::BAUD_9600, SerialPort::CHAR_SIZE_7,
				SerialPort::PARITY_EVEN, SerialPort::STOP_BITS_1,
				SerialPort::FLOW_CONTROL_DEFAULT);
	} catch (exception &e) {
		FILE_LOG(logWARNING) << "Can't open serial port " << path
				<< " because of " << e.what();
		return false;
	}
	if (dataValid(readData()))
		return true;
	return false;
}

string SmartmeterReader::readData() {
	return string();
}

inline bool SmartmeterReader::dataValid(const string& data) {
	//in my test there where 11 elements
	if (int c = split(data, '\n').size() != 11) {
		FILE_LOG(logWARNING)
				<< "Read smart meter datagram with invalid structure. datagram is: "
				<< data << ". Number of elements (should be 11): " << c;
		return false;
	}
	return true;
}
