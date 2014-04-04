#include "inverterReader.h"
#include <regex>
#include <string>

using namespace std;

InverterReader::InverterReader() : BaseSerialReader(){

}

vector<string> InverterReader::read() {
	string data = readData();
	if(dataValid(data))
		return split(data, ' ');
	else
		return vector<string>();
}

bool InverterReader::openDevice(string path) {
	return false;
}

string InverterReader::readType() {
	return string();
}

string InverterReader::readData() {
	return string();
}

bool InverterReader::typeValid(string& type) {
	return false;
}

bool InverterReader::dataValid(string& data) {
	return false;
}
