#include "util.h"
#include <thread>
#include <chrono>
#include <algorithm>
#include <functional>
#include <cctype>
#include <locale>

using namespace std;

string& ltrim(string& s) {
        s.erase(s.begin(), find_if(s.begin(), s.end(), not1(ptr_fun<int, int>(isspace))));
        return s;
}

string& rtrim(string& s) {
        s.erase(find_if(s.rbegin(), s.rend(), not1(ptr_fun<int, int>(isspace))).base(), s.end());
        return s;
}

string& trim(string& s) {
        return ltrim(rtrim(s));
}

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
	if(token.length())
		elems.push_back(token);
	return elems;
}

BaseSerialReader::~BaseSerialReader() {
	if (serialPort->IsOpen()) {
		serialPort->Close();
	}
}
