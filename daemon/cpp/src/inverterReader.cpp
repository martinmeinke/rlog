#include "inverterReader.h"
#include "util.h"
#include <string>
#include <sstream>
#include <iomanip>
#include "log.h"
#include <chrono>
#include <thread>
#include <iostream>

using namespace std;


// Read data from all inverters. Return string vector with lines all valid lines returned by each of the inverters.
vector<string> InverterReader::read() {
	vector<string> ret;
	try{
		for (auto id : inverterIDs) {
			this_thread::sleep_for(chrono::milliseconds(200));
			string data = readData(id);
			if (dataValid(data))
				ret.push_back(data);
		}
	} catch (exception& e){
		FILE_LOG(logERROR) << "inverter reader error: " << e.what();
		cerr << "inverter reader error: " << e.what() << endl;
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
		FILE_LOG(logWARNING) << "Can't open inverter serial port at" << path
				<< " because of " << e.what();
		cerr << "Can't open inverter serial port at" << path
				<< " because of " << e.what() << endl;
		return false;
	}
	return true;
}


string InverterReader::readMessage() {
	string line;
	try {
		// skip everything until line feed
		while (line.compare("\n") != 0)
			line = string(1, serialPort->ReadByte(1000));
		// read until return character
		while (line.compare(line.length() - 1, 1, "\r") != 0)
			line += string(1, serialPort->ReadByte(1000));
	} catch (runtime_error& e) {
		FILE_LOG(logERROR) << "Inverter serial port read error: " << e.what();
		cerr << "Inverter serial port read error: " << e.what() << endl;
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
		FILE_LOG(logERROR) << "Error writing inverter type command: " << e.what();
		cerr << "Error writing inverter type command: " << e.what() << endl;
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
		FILE_LOG(logERROR) << "Error writing inverter data command: " << e.what();
		cerr << "Error writing inverter data command: " << e.what() << endl;
		return string();
	}
	return readMessage();
}


bool InverterReader::typeValid(const string& type) {
	if (type.length() != 15) { // that's the normal length of the type message I get
		FILE_LOG(logDEBUG) << "Type message with invalid length: " << type
				<< " Length is " << type.length() << " should be 15";
		cerr << "Type message with invalid length: " << type
				<< " Length is " << type.length() << " should be 15" << endl;	
		return false;
	}
	unsigned char checksum = 0;
	for(string::size_type i = 1; i < type.length() - 2; i++) // second byte from behind is the checksum (sum of all previous bytes starting with the second and all that mod 256)
		checksum += type[i];
	if(type[type.length() - 2] != checksum){
		FILE_LOG(logDEBUG) << "Type message with invalid checksum: " << type;
		cerr << "Type message with invalid checksum: " << type << endl;
		return false;
	}
	return true;
}


bool InverterReader::dataValid(const string& data) {
	if (data.length() != 66) { // that's the normal length of the type message I get
		FILE_LOG(logDEBUG) << "Data message with invalid length: " << data
				<< " Length is " << data.length() << " should be 66";
		cerr << "Data message with invalid length: " << data
				<< " Length is " << data.length() << " should be 66" << endl;
		return false;
	}
	unsigned char checksum = 0;
	for(string::size_type i = 1; i < data.length() - 9; i++)  // ninth byte from behind is the checksum (sum of all previous bytes starting with the second and all that mod 256)
		checksum += data[i];
	if(data[data.length() - 9] != checksum){
		FILE_LOG(logDEBUG) << "Data message with invalid checksum: " << data;
		cerr << "Data message with invalid checksum: " << data << endl;
		return false;
	}
	return true;
}

// returns vector with names of responding inverters
map<unsigned short, string> InverterReader::findInverter(const string& inverterlist) {
	map<unsigned short, string> ret;
	for(string element : split(inverterlist, ',')) {
		this_thread::sleep_for(chrono::milliseconds(200));
		unsigned short id = fromString<unsigned short>(element);
		string type = readType(id);
		if (typeValid(type)) {
			FILE_LOG(logINFO) << "Found inverter with id " << id << " of type" << trim(split(type, ' ')[1]);
			cerr << "Found inverter with id " << id << " of type" << trim(split(type, ' ')[1]) << endl;
			inverterIDs.push_back(id);
			ret[id] = trim(split(type, ' ')[1]);
			continue;
		}
		this_thread::sleep_for(chrono::milliseconds(200));
		// second chance if type message got lost: data message
		string data = readData(id);
		if (dataValid(data)) {
			FILE_LOG(logINFO) << "Found inverter with id " << id << " of type" << trim(split(data, ' ')[9]);
			cerr << "Found inverter with id " << id << " of type" << trim(split(data, ' ')[9]) << endl;
			inverterIDs.push_back(id);
			ret[id] = trim(split(data, ' ')[9]);
			continue;
		}
	}
	return ret;
}
