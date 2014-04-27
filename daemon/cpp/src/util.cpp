#include "util.h"
#include <thread>
#include <chrono>
#include <algorithm>
#include <functional>
#include <cctype>
#include <locale>
#include <sstream>

using namespace std;

string& ltrim(string& s) {
        s.erase(s.begin(), find_if(s.begin(), s.end(), not1(ptr_fun<int, int>(isspace))));
        return s;
}

string& rtrim(string& s) {
        s.erase(find_if(s.rbegin(), s.rend(), not1(ptr_fun<int, int>(isspace))).base(), s.end());
        return s;
}

string trim(string s) {
        return ltrim(rtrim(s));
}

template<class T>
T fromString(const string& s){
     istringstream stream (s);
     T t;
     stream >> t;
     return t;
}

// Instantiate for double, int and unsigned short
template double fromString<double>(const string& s);
template int fromString<int>(const string& s);
template unsigned short fromString<unsigned short>(const string& s);


template<typename T>
string toString(const T& v){
    ostringstream strstr;
    strstr << v;
    return strstr.str();
}

// Instantiate for unsigned short
template string toString<unsigned short>(const unsigned short& v);
template string toString<double>(const double& v);


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


void BaseSerialReader::closeDevice() {
	if (serialPort->IsOpen()) {
		serialPort->Close();
	}
}
