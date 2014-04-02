#include <getopt_pp.h>
#include <sqlite3.h>
#include <SerialStream.h>
#include <cstdlib>
#include "util.h"
#include "mqtt.h"
#include <functional>
#include <iostream>

using namespace std;

class Test {
public:
	void bar() {
		if(callback) // equivalent to 'callback.operator bool()' <== c++11 magic!
			callback();
	}

	function< void() > callback;
};

class Bim {
public:
	Bim() : baz(42) {
		t.callback = bind(&Bim::foo, this);
	}

	void operator()(){
		t.bar();
	}

	void foo(){
		cout << "BIM!" << baz << endl;
	}

private:
	int baz;

private:
	Test t;
};


int main(int argc, char* argv[]){
	Bim b;
	b();
	exit(0);
}
