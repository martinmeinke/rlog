#include "util.h"

using namespace std;

vector<string> split(const string &s, char delim) {
	vector<string> elems;
	string token;
	for (auto const c : s) {
		if (c != delim)
			token += c;
		else {
			if (token.length())
				elems.push_back(token);
			token.clear();
		}
	}
	return elems;
}

BaseSerialReader::~BaseSerialReader() {
	if (serialPort.IsOpen()) {
		serialPort.flush();
		serialPort.Close();
	}
}
