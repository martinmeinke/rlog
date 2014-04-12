#include "inverterReader.h"
#include <string>
#include <sstream>
#include <iomanip>
#include "log.h"
#include <chrono>
#include <thread>

using namespace std;


// Read data from all inverters. Return string vector with lines all valid lines returned by each of the inverters.
vector<string> InverterReader::read() {
	vector<string> ret;
	ret.resize(inverterIDs.size());
	for (auto id : inverterIDs) {
		this_thread::sleep_for(chrono::milliseconds(200));
		string data = readData(id);
		if (dataValid(data))
			ret.push_back(data);
	}
	return ret;
}

bool InverterReader::openDevice(const string path) {
	serialPort.reset(new SerialPort(path));
	try {
		serialPort->Open(SerialPort::BAUD_9600, SerialPort::CHAR_SIZE_8,
				SerialPort::PARITY_NONE, SerialPort::STOP_BITS_1,
				SerialPort::FLOW_CONTROL_DEFAULT);
	} catch (exception &e) {
		FILE_LOG(logERROR) << "Can't open inverter serial port " << path
				<< " because of " << e.what();
		return false;
	}
	// TODO: do something if 1 is not the ID of an inverter on the bus (default argument of read*() is 1)
	if (typeValid(readType()))
		return true;
	if (dataValid(readData()))
		return true;
	return false;
}


string InverterReader::readMessage() {
	string line;
	try {
		// skip everything until line feed
		while (line.compare("\n") != 0)
			line = string(1, serialPort->ReadByte(2000));
		// read until return character
		while (line.compare(line.length() - 1, 1, "\r") != 0)
			line += string(1, serialPort->ReadByte(2000));
	} catch (runtime_error& e) {
		line.clear();
	}
	return line;
}

string InverterReader::readType(unsigned short id) {
	stringstream s;
	s << "#" << setfill('0') << setw(2) << id << "9\r";
	try{
		serialPort->Write(s.str());
	} catch (runtime_error& e){
		return string();
	}
	return readMessage();
}

string InverterReader::readData(unsigned short id) {
	stringstream s;
	s << "#" << setfill('0') << setw(2) << id << "0\r";
	try{
		serialPort->Write(s.str());
	} catch (runtime_error& e){
		return string();
	}
	return readMessage();
}


bool InverterReader::typeValid(const string& type) {
	if (type.length() != 15) { // that's the normal length of the type message I get
		FILE_LOG(logDEBUG) << "Type message with invalid length: " << type
				<< " Length is " << type.length() << " should be 15";
		return false;
	}
	unsigned char checksum = 0;
	for(string::size_type i = 1; i < type.length() - 2; i++) // second byte from behind is the checksum (sum of all previous bytes starting with the second and all that mod 256)
		checksum += type[i];
	if(type[type.length() - 2] != checksum){
		FILE_LOG(logDEBUG) << "Type message with invalid checksum: " << type;
		return false;
	}
	return true;
}


bool InverterReader::dataValid(const string& data) {
	if (data.length() != 66) { // that's the normal length of the type message I get
		FILE_LOG(logDEBUG) << "Data message with invalid length: " << data
				<< " Length is " << data.length() << " should be 66";
		return false;
	}
	unsigned char checksum = 0;
	for(string::size_type i = 1; i < data.length() - 9; i++)  // ninth byte from behind is the checksum (sum of all previous bytes starting with the second and all that mod 256)
		checksum += data[i];
	if(data[data.length() - 9] != checksum){
		FILE_LOG(logDEBUG) << "Data message with invalid checksum: " << data;
		return false;
	}
	return true;
}

void InverterReader::findInverter(unsigned short startID,
		unsigned short endID) {
	for (unsigned short id = startID; id <= endID; id++) {
		this_thread::sleep_for(chrono::milliseconds(200));
		if (typeValid(readType(id))) {
			FILE_LOG(logINFO) << "Found inverter with id " << id;
			inverterIDs.push_back(id);
			continue;
		}
		// second chance if type message got lost: data message
		if (dataValid(readData(id))) {
			FILE_LOG(logINFO) << "Found inverter with id " << id;
			inverterIDs.push_back(id);
		}
	}
}
