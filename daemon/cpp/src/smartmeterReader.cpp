#include "smartmeterReader.h"

using namespace std;

SmartmeterReader::SmartmeterReader() {
}

vector<string> SmartmeterReader::read() {
	string data = readData();
	if (dataValid(data))
		return split(data, ' ');
	else
		return vector<string>();
}

bool SmartmeterReader::openDevice(string path) {
	return false;
}

string SmartmeterReader::readData() {
	return string();
}

bool SmartmeterReader::dataValid(string& data) {
	return false;
}
