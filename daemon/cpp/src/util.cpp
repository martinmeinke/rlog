#include "util.h"
#include <sstream>

using namespace std;

vector<string>& split(const string &s, char delimiter, vector<string> &elems) {
    stringstream stringstr(s);
    string item;
    while(getline(stringstr, item, delimiter)) {
        elems.push_back(item);
    }
    return elems;
}

vector<string> split(const string &s, char delim) {
    vector<string> elems;
    return split(s, delim, elems);
}
