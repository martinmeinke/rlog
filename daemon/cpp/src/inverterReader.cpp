#include "inverterReader.h"
#include <regex>
#include <string>
#include "log.h"

using namespace std;

vector<string> InverterReader::read() {
	string data = readData();
	if (dataValid(data))
		return split(data, ' ');
	else
		return vector<string>();
}

inline bool InverterReader::openDevice(const string path) {
	serialPort.reset(new SerialPort(path));
	try {
		serialPort->Open(SerialPort::BAUD_9600, SerialPort::CHAR_SIZE_8,
				SerialPort::PARITY_NONE, SerialPort::STOP_BITS_1,
				SerialPort::FLOW_CONTROL_DEFAULT);
	} catch (exception &e) {
		FILE_LOG(logWARNING) << "Can't open serial port " << path
				<< " because of " << e.what();
		return false;
	}
	if (typeValid(readType()))
		return true;
	if (dataValid(readData()))
		return true;
	return false;
}

string InverterReader::readType() {
	return string();
}

string InverterReader::readData() {
	// TODO: implement actual inverter request sequence
	string data;
	try {
		while (true)
			data += serialPort->ReadByte(250);
	} catch (runtime_error &e) {
		// most likely timeout
	}
	return data;
}

bool InverterReader::typeValid(const string& type) {
	return true;
}

bool InverterReader::dataValid(const string& data) {
	return true;
}
