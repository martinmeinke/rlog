#include <cstdlib>
#include "rlogd.h"
#include <iostream>
#include <list>
#include <string>
#include <sqlite3.h>
#include <thread>
#include "util.h"
#include "log.h"


#define LOCATIONX "14.122994"
#define LOCATIONY "52.508519"

using namespace std;

RLogd::RLogd(const string& database, const string& mqtt_hostname,
		const unsigned int mqtt_port, const string& mqtt_clientID,
		const string& deviceBaseName, const string& inverterList,
		const unsigned int timing, const unsigned short maxDeviceID) :
		mqtt(mqtt_clientID, mqtt_hostname, mqtt_port), devBaseName(
				deviceBaseName), invList(inverterList), database(database), interval(timing), maxDevice(
				maxDeviceID + 1) {
}

void RLogd::init() {
	mqtt.ConnectCallback = bind(&RLogd::onConnect, this);
	mqtt.DisconnectCallback = bind(&RLogd::onDisconnect, this);
	mqtt.ConnectionLostCallback = bind(&RLogd::onConnectionLost, this, placeholders::_1);

	try{
		mqtt.connect();
	} catch (runtime_error &e){
		FILE_LOG(logERROR) << "mqtt connect failed: " << e.what();
		cerr << "mqtt connect failed: " << e.what() << endl;
	}

	if(sqlite3_open(database.c_str(), &db_connection) != SQLITE_OK)
		throw runtime_error(string("Cannot open database: ") + string(sqlite3_errmsg(db_connection)));
	FILE_LOG(logINFO) << "opened database " << database;
	if(sqlite3_prepare_v2(db_connection, "INSERT OR REPLACE INTO charts_device (id, model) VALUES (?, ?)", -1, &insertDevice, NULL) != SQLITE_OK)
		throw runtime_error(string("Cannot prepare statement to insert inverter devices: ") + string(sqlite3_errmsg(db_connection)));
	if(sqlite3_prepare_v2(db_connection, "INSERT INTO charts_solarentrytick VALUES (NULL, datetime('now', 'localtime'), ?, ?, ?, ?, ?, ?, ?, ?, ?)", -1, &insertInverterTick, NULL) != SQLITE_OK)
		throw runtime_error(string("Cannot prepare statement to insert inverter ticks: ") + string(sqlite3_errmsg(db_connection)));
	if(sqlite3_prepare_v2(db_connection, "INSERT INTO charts_smartmeterentrytick VALUES (NULL, datetime('now', 'localtime'), ?, ?, ?, ?)", -1, &insertSmartmeterTick, NULL) != SQLITE_OK)
		throw runtime_error(string("Cannot prepare statement to insert smartmeter ticks: ") + string(sqlite3_errmsg(db_connection)));
}

void RLogd::start(){
	if(not findDevices())
		return;
	// initialize minutely and hourly data structures
	// make a reading to get entries
	vector<string> inverterValues = invReader.read();
	// complain if less values arrived than where expected
	if(inverterValues.size() != split(invList, ',').size()){
		FILE_LOG(logWARNING) << "Initialized only inverters " << [&inverterValues](){stringstream s; for(auto element: inverterValues) s << element.substr(2, 2) << " "; return s.str();}() << " but was supposed to find " << invList;
		cerr << "WARNING: Initialized only inverters " << [&inverterValues](){stringstream s; for(auto element: inverterValues) s << element.substr(2, 2) << " "; return s.str();}() << " but was supposed to find " << invList << endl;
	}
	for(auto element : inverterValues){
		vector<string> values = split(element, ' ');
		unsigned short deviceID = fromString<unsigned short>(values[0].substr(2, 2)); // values[0] looks like: "\n\*\d\d\d" and first two digits are device id
		double reading = fromString<double>(trim(values[9]));
		smartmeterMinute[deviceID] = make_pair(reading, chrono::system_clock::now());
		smartmeterHour[deviceID] = make_pair(reading, chrono::system_clock::now());
		FILE_LOG(logINFO) << "initialized inverter " << deviceID << " with value " << reading;
		cerr << "initialized inverter " << deviceID << " with value " << reading << endl;
	}
	// for the smart meter it is sufficient to initialize accumulated sum with 0 and set the current time stamp
	smartmeterMinute[1] = make_pair<double, chrono::system_clock::time_point>(0.0f, chrono::system_clock::now());
	smartmeterMinute[2] = make_pair<double, chrono::system_clock::time_point>(0.0f, chrono::system_clock::now());
	smartmeterMinute[3] = make_pair<double, chrono::system_clock::time_point>(0.0f, chrono::system_clock::now());
	smartmeterHour[1] = make_pair<double, chrono::system_clock::time_point>(0.0f, chrono::system_clock::now());
	smartmeterHour[2] = make_pair<double, chrono::system_clock::time_point>(0.0f, chrono::system_clock::now());
	smartmeterHour[3] = make_pair<double, chrono::system_clock::time_point>(0.0f, chrono::system_clock::now());

	// main loop
	FILE_LOG(logINFO) << "starting main loop";
	cerr << "starting main loop" << endl;
	running = true;
	while(running){
		chrono::system_clock::time_point start = chrono::system_clock::now();
		// read inverter
		for(auto element : invReader.read()){
			// FILE_LOG(logDEBUG) << "got from inverter: " << element;
			cerr << "got from inverter: " << element << endl;
			vector<string> values = split(element, ' ');
			int deviceID = fromString<int>(values[0].substr(2, 2)); // values[0] looks like: "\n\*\d\d\d" and first two digits are device id
			publishInvertertick(deviceID, trim(values[values.size() - 1]), values[7]);
			saveInverterTick(deviceID, values);
		}
		// read smartmeter
		vector<string> smartMeterValues = smReader.read();
		if(smartMeterValues.size() != 0){
			double 	reading = fromString<double>(smartMeterValues[0]),
					phase1 = fromString<double>(smartMeterValues[1]) * 1000.0f,
					phase2 = fromString<double>(smartMeterValues[2]) * 1000.0f,
					phase3 = fromString<double>(smartMeterValues[3]) * 1000.0f;
			publishSmartMeterTick(phase1, phase2, phase3);
			saveSmartmeterTick(reading, phase1, phase2, phase3);
		} else {
			FILE_LOG(logERROR) << "did not read anything from smart meter";
			cerr << "did not read anything from smart meter" << endl;
		}

		chrono::milliseconds duration = chrono::duration_cast<chrono::milliseconds>(chrono::system_clock::now() - start);
		if(duration > chrono::milliseconds(interval)){
			FILE_LOG(logDEBUG) << "timing critical. iteration took " << duration.count() / 1000 << " seconds";
			cerr << "timing critical. iteration took " << duration.count() / 1000 << " seconds" << endl;
		} else {
			this_thread::sleep_for(chrono::milliseconds(interval) - duration);
		}
	}
}

void RLogd::stop() {
	running = false;
	try{
		mqtt.disconnect();
	} catch (runtime_error &e){
		FILE_LOG(logERROR) << "mqtt disconnect  error: " << e.what();
		cerr << "mqtt disconnect  error: " << e.what() << endl;
	}
}

bool RLogd::findDevices() {
	FILE_LOG(logINFO) << "start discovering devices";
	cerr  << "start discovering devices" << endl;
	bool smartMeterDeviceFound = false, inverterDeviceFound = false;
	for (unsigned short i = 0; (i < maxDevice) and not (smartMeterDeviceFound and inverterDeviceFound); i++) {
		cerr << "trying device number " << i << endl;
		this_thread::sleep_for(chrono::milliseconds(200));
		if ((not smartMeterDeviceFound) and smReader.openDevice(devBaseName + toString<unsigned short>(i))) {
			smartMeterDeviceFound = true;
			// fake 3 smart meter
			try{
				mqtt.publish("/devices/RLog/controls/VSM-102 (1)/meta/type", "text", 0, true);
				mqtt.publish("/devices/RLog/controls/VSM-102 (2)/meta/type", "text", 0, true);
				mqtt.publish("/devices/RLog/controls/VSM-102 (3)/meta/type", "text", 0, true);
			} catch (runtime_error &e){
				FILE_LOG(logERROR) << "mqtt publish error in " << __func__ << " line " << __LINE__ << ": " << e.what();
				cerr << "mqtt publish error in " << __func__  << " line " << __LINE__ << ": " << e.what() << endl;
			}
			FILE_LOG(logINFO) << "Discovered smart meter at " << devBaseName << i;
			cerr  << "Discovered smart meter at " << devBaseName << i << endl;
			continue;
		} else if(not smartMeterDeviceFound){
			smReader.closeDevice();
			FILE_LOG(logINFO) << "closing port after unsuccessful smartmeter discovery attempt";
			cerr << "closing port after unsuccessful smartmeter discovery attempt" << endl;
		}
		if ((not inverterDeviceFound) and invReader.openDevice(devBaseName + toString<unsigned short>(i))) {
			map<unsigned short, string> inverterResponses = invReader.findInverter(invList);
			if((inverterResponses.size() > 0) and (inverterResponses.size() != split(invList, ',').size())){
				FILE_LOG(logWARNING) << "You wanted me to detect inverters " << invList << " but I only found " << [&inverterResponses](){stringstream s; for(auto element: inverterResponses) s << element.first << " "; return s.str();}();
				cerr << "WARNING: You wanted me to detect inverters " << invList << " but I only found " << [&inverterResponses](){stringstream s; for(auto element: inverterResponses) s << element.first << " "; return s.str();}() << endl;
			}
			for(auto element : inverterResponses){ // this means there is at least one inverter found. We could add a check here that requires all to be found ...
				inverterDeviceFound = true;
				try{
					mqtt.publish(string("/devices/RLog/controls/") + element.second + string(" (") + toString<unsigned short>(element.first) + string(")/meta/type"), "text", 0, true);
				}catch (runtime_error &e){
					FILE_LOG(logERROR) << "mqtt publish error in " << __func__  << " line " << __LINE__ << ": " << e.what();
					cerr << "mqtt publish error in " << __func__  << " line " << __LINE__ << ": " << e.what() << endl;
				}
				if(sqlite3_clear_bindings(insertDevice) == SQLITE_OK && sqlite3_reset(insertDevice) == SQLITE_OK){
					if(sqlite3_bind_int(insertDevice, 1, element.first) == SQLITE_OK && sqlite3_bind_text(insertDevice, 2, element.second.c_str(), -1, SQLITE_STATIC) == SQLITE_OK){
						int rc;
						if((rc = sqlite3_step(insertDevice)) != SQLITE_DONE){
							FILE_LOG(logERROR) << "database error while inserting device. Error code: " << rc << " : " << sqlite3_errmsg(db_connection) << ". Values: " << element.first << ", " << element.second;
							cerr << "database error while inserting device. Error code: " << rc << " : " << sqlite3_errmsg(db_connection) << ". Values: " << element.first << ", " << element.second << endl;
						}
					} else {
						FILE_LOG(logERROR) << "database error while binding values when inserting device: " << sqlite3_errmsg(db_connection) << ". Values: " << element.first << ", " << element.second;
						cerr << "database error while binding values when inserting device: " << sqlite3_errmsg(db_connection) << ". Values: " << element.first << ", " << element.second << endl;
					}
				} else {
					FILE_LOG(logERROR) << "database error while resetting statement before inserting device: " << sqlite3_errmsg(db_connection) << ". Values: " << element.first << ", " << element.second;
					cerr << "database error while resetting statement before inserting device: " << sqlite3_errmsg(db_connection) << ". Values: " << element.first << ", " << element.second << endl;
				}
			}
		} else if(not inverterDeviceFound){
			invReader.closeDevice();
			FILE_LOG(logINFO) << "closing port after unsuccessful inverter discovery attempt";
			cerr << "closing port after unsuccessful inverter discovery attempt" << endl;
		}
	}
	return smartMeterDeviceFound and inverterDeviceFound;
}


void RLogd::onConnect() {
	FILE_LOG(logINFO) << "MQTT connected";
	try{
		mqtt.publish("/devices/RLog/meta/name", "Rlog", 0, true);
		mqtt.publish("/devices/RLog/meta/locationX", LOCATIONX, 0, true);
		mqtt.publish("/devices/RLog/meta/locationY", LOCATIONY, 0, true);
	} catch (runtime_error &e){
		FILE_LOG(logERROR) << "mqtt publish error in " << __func__ << ": " << e.what();
		cerr << "mqtt publish error in " << __func__ << ": " << e.what() << endl;
	}
}

void RLogd::onDisconnect() {
	FILE_LOG(logINFO) << "MQTT disconnected";
	cerr << "MQTT disconnected" << endl;
}

void RLogd::onConnectionLost(string reason) {
	FILE_LOG(logERROR) << "MQTT connection lost because of " << reason;
	cerr << "MQTT connection lost because of " << reason << endl;
}

inline void RLogd::saveInverterTick(int deviceID,vector<string>& values) {
	if(sqlite3_clear_bindings(insertInverterTick) == SQLITE_OK && sqlite3_reset(insertInverterTick) == SQLITE_OK){
		int rc = SQLITE_OK;
		rc |= sqlite3_bind_int(insertInverterTick, 1, deviceID); // bind device id
		rc |= sqlite3_bind_double(insertInverterTick, 2, fromString<double>(trim(values[2]))); // bind gV
		rc |= sqlite3_bind_double(insertInverterTick, 3, fromString<double>(trim(values[3]))); // bind gA
		rc |= sqlite3_bind_double(insertInverterTick, 4, fromString<double>(trim(values[4]))); // bind gW
		rc |= sqlite3_bind_double(insertInverterTick, 5, fromString<double>(trim(values[5]))); // bind lV
		rc |= sqlite3_bind_double(insertInverterTick, 6, fromString<double>(trim(values[6]))); // bind lA
		rc |= sqlite3_bind_double(insertInverterTick, 7, fromString<double>(trim(values[7]))); // bind lW
		rc |= sqlite3_bind_double(insertInverterTick, 8, fromString<double>(trim(values[8]))); // bind temp
		rc |= sqlite3_bind_double(insertInverterTick, 9, fromString<double>(trim(values[9]))); // bind total
		if(rc == SQLITE_OK){
			if((rc = sqlite3_step(insertInverterTick)) != SQLITE_DONE){
				FILE_LOG(logERROR) << "database error while inserting inverter tick. Error code: " << rc << " : " << sqlite3_errmsg(db_connection);
				cerr << "database error while inserting inverter tick. Error code: " << rc << " : " << sqlite3_errmsg(db_connection) << endl;
			}
		} else {
			FILE_LOG(logERROR) << "database error while binding values when inserting inverter tick: " << sqlite3_errmsg(db_connection);
			cerr << "database error while binding values when inserting inverter tick: " << sqlite3_errmsg(db_connection) << endl;
		}
	} else {
		FILE_LOG(logERROR) << "database error while resetting statement before inserting inverter tick: " << sqlite3_errmsg(db_connection);
		cerr << "database error while resetting statement before inserting inverter tick: " << sqlite3_errmsg(db_connection) << endl;
	}
}

inline void RLogd::saveSmartmeterTick(double reading, double phase1, double phase2, double phase3) {
	if(sqlite3_clear_bindings(insertSmartmeterTick) == SQLITE_OK && sqlite3_reset(insertSmartmeterTick) == SQLITE_OK){
		int rc = SQLITE_OK;
		// FILE_LOG(logDEBUG) << "got from smartmeter: " << reading << ", " << phase1 << ", " << phase2 << ", " << phase3;
		cerr  << "got from smartmeter: " << reading << ", " << phase1 << ", " << phase2 << ", " << phase3 << endl;
		rc |= sqlite3_bind_double(insertSmartmeterTick, 1, reading); // bind reading
		rc |= sqlite3_bind_double(insertSmartmeterTick, 2, phase1); // bind phase 1
		rc |= sqlite3_bind_double(insertSmartmeterTick, 3, phase2); // bind phase 2
		rc |= sqlite3_bind_double(insertSmartmeterTick, 4, phase3); // bind phase 3
		if(rc == SQLITE_OK){
			if((rc = sqlite3_step(insertSmartmeterTick)) != SQLITE_DONE){
				FILE_LOG(logERROR) << "database error while inserting smartmeter tick. Error code: " << rc << " : " << sqlite3_errmsg(db_connection);
				cerr << "database error while inserting smartmeter tick. Error code: " << rc << " : " << sqlite3_errmsg(db_connection) << endl;
			}
		} else {
			FILE_LOG(logERROR) << "database error while binding values when inserting smartmeter tick: " << sqlite3_errmsg(db_connection);
			cerr << "database error while binding values when inserting smartmeter tick: " << sqlite3_errmsg(db_connection) << endl;
		}
	} else {
		FILE_LOG(logERROR) << "database error while resetting statement before inserting smartmeter tick: " << sqlite3_errmsg(db_connection);
		cerr << "database error while resetting statement before inserting smartmeter tick: " << sqlite3_errmsg(db_connection) << endl;
	}
}

inline void RLogd::calculateMinutelyInverterReading(
		pair<double, std::chrono::system_clock::time_point>& minute,
		double current_reading) {
}

inline void RLogd::calculateHourlyInverterReading(
		pair<double, std::chrono::system_clock::time_point>& hour,
		double current_reading) {
}

inline void RLogd::calculateMinutelySmartmeterReading(
		pair<double, std::chrono::system_clock::time_point>& minute,
		double current_reading) {
}

inline void RLogd::calculateHourlySmartmeterReading(
		pair<double, std::chrono::system_clock::time_point>& hour,
		double current_reading) {
}

inline void RLogd::publishInvertertick(unsigned short deviceID, const std::string& deviceName, const std::string& value) {
	try{
		stringstream topic;
		topic << "/devices/RLog/controls/" << deviceName << " (" << deviceID << ")";
		mqtt.publish(topic.str(), toString(fromString<double>(trim(value))), 0, true);
	} catch(runtime_error &e){
		FILE_LOG(logERROR) << "MQTT publish error in " << __func__  << " line " << __LINE__ << ": " << e.what();
		cerr << "MQTT publish error in " << __func__  << " line " << __LINE__ << ": " << e.what() << endl;
	}
}

inline void RLogd::publishSmartMeterTick(double phase1, double phase2, double phase3) {
	try{
		mqtt.publish(string("/devices/RLog/controls/VSM-102 (1)"), toString<double>(phase1), 0, true);
		mqtt.publish(string("/devices/RLog/controls/VSM-102 (2)"), toString<double>(phase2), 0, true);
		mqtt.publish(string("/devices/RLog/controls/VSM-102 (3)"), toString<double>(phase3), 0, true);
	} catch(runtime_error &e){
		FILE_LOG(logERROR) << "MQTT publish error in " << __func__  << " line " << __LINE__ << ": " << e.what();
		cerr << "MQTT publish error in " << __func__  << " line " << __LINE__ << ": " << e.what() << endl;
	}
}
