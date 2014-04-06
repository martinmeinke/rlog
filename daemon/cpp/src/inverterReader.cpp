#include "inverterReader.h"
#include <regex>
#include <string>
#include <sstream>
#include <iomanip>
#include "log.h"

using namespace std;


// Read data from all inverters. Return string vector with line returned by each device (empty string if the device did not answer).
vector<string> InverterReader::read() {
	string data = readData();
	if (dataValid(data))
		return split(data, ' ');
	else
		return vector<string>();
}

bool InverterReader::openDevice(const string path) {
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


string InverterReader::readMessage() {
	string line;
	try {
		// skip everything until line feed
		while (line.compare("\n") != 0)
			line = string(1, serialPort->ReadByte(2000));
		// read until return character
		while (line.compare(line.length() - 1, 1, "\r") != 0)
			line = string(1, serialPort->ReadByte(2000));
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

/*
# checks checksum in type message
def type_valid(self, typ_string):
    if len(typ_string) != 15: # so lang sind meine typen normalerweise
        if DEBUG_ENABLED:
            log("Read type message with invalid length. message is: " + typ_string + " length was: " + str(len(typ_string)))
        return False
    summe = 0
    for i in range(1, len(typ_string) - 2): # 2. zeichen von hinten ist pruefsumme bei mir
        summe += ord(typ_string[i])
    if ord(typ_string[-2]) != summe % 256:
        if DEBUG_ENABLED:
            log("Read invalid type message: " + typ_string)
        return False
    return True
*/
bool InverterReader::typeValid(const string& type) {
	return true;
}


/*
# checks checksum in data message
def data_valid(self, data_string):
    if DEBUG_SERIAL:
        return True
    if len(data_string) != 66: # so lang sind meine daten normalerweise
        if DEBUG_ENABLED:
            log("Read data message with invalid length. message is: " + data_string + " length was: " + str(len(data_string)))
        return False
    summe = 0
    for i in range(1, len(data_string) - 9): # 9. zeichen von hinten ist pruefsumme bei mir
        summe += ord(data_string[i])
    if ord(data_string[-9]) != summe % 256:
        if DEBUG_ENABLED:
            log("Read invalid data message: " + data_string)
        return False
    return True
*/
bool InverterReader::dataValid(const string& data) {
	return true;
}
