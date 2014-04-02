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
		if(callback.operator bool())
			callback();
	}

	function< void() > callback;
};

class Bim {
public:
	Bim(){
		t.callback = bind(&Bim::foo, this);
	}

	void operator()(){
		t.bar();
	}

	void foo(){
		cout << "BIM!" << endl;
	}

private:
	Test t;
};


int main(int argc, char* argv[]){
	// store the member function of an object:
	Bim b;
	b();
	exit(0);
}
