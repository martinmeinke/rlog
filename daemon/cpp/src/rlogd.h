#include <string>
#include "mqtt.h"
#include "inverterReader.h"
#include "smartmeterReader.h"
#include <sqlite3.h>
#include <map>
#include <chrono>

#ifndef RLOGD_H
#define RLOGD_H

class RLogd {
public:
	explicit RLogd(const std::string& database = "/home/stephan/test.db",
			const std::string& mqtt_hostname = "localhost",
			const unsigned int mqtt_port = 1883,
			const std::string& mqtt_clientID = "MQTTRLOGD",
			const std::string& deviceBaseName = "/dev/ttyUSB",
			const std::string& inverterList = "1,2,3",
			const unsigned int timing = 10000,
			const unsigned short maxDeviceID = 1);
	void init();
	void start();
	void stop();

	static bool running;

private:
	bool findDevices();
	void onConnect();
	void onDisconnect();
	void onConnectionLost(std::string reason);
	inline void saveInverterTick(int deviceID, std::vector<std::string>& values);
	inline void saveSmartmeterTick(double reading, double phase1, double phase2, double phase3);
	// In order to calculate the minutely production we save the first tick of every minute (pair.first) and its time stamp (pair.second).
	// When the first tick of the next minute arrives the amount of energy is:
	// the current reading - initial reading and corrected by the time in between so that and average for 60 seconds is saved
	// this method must be called when the first tick in every minute arrives
	// this method stores the calculated value to the database
	inline void calculateMinutelyInverterReading(std::pair<double, std::chrono::system_clock::time_point> & minute, double current_reading);
	// similar here for hours but it would only need to be called on the first tick every hour.
	// to give the web interface a chance to be more up to date this can also be called more often (like every 10 minutes).
	// this method stores the calculated value to the database
	inline void calculateHourlyInverterReading(std::pair<double, std::chrono::system_clock::time_point> & hour, double current_reading);
	// We calculate the minutely smart meter production with the weighted sum of individual ticks.
	// this works as the database triggers worked and assumes constant power consumption within a tick period
	// this function does not save the value to database (the caller must do that whenever a minute is over)
	inline void calculateMinutelySmartmeterReading(std::pair<double, std::chrono::system_clock::time_point> & minute, double current_reading);
	// similar to calculateMinutelySmartmeterReading()
	inline void calculateHourlySmartmeterReading(std::pair<double, std::chrono::system_clock::time_point> & hour, double current_reading);

	// publish values on MQTT
	inline void publishInvertertick(unsigned short deviceID, const std::string& deviceName, const std::string& value);
	inline void publishSmartMeterTick(double phase1, double phase2, double phase3);


	MQTT_Client mqtt;
	InverterReader invReader;
	SmartmeterReader smReader;
	std::string devBaseName;
	std::string invList;
	std::string database;
	unsigned int interval;
	unsigned short maxDevice;

	sqlite3 * db_connection = nullptr;
	sqlite3_stmt * insertDevice = nullptr;
	sqlite3_stmt * insertInverterTick = nullptr;
	sqlite3_stmt * insertSmartmeterTick = nullptr;

	// map of device ID to reading at first tick of minute and its time point
	std::map<unsigned short, std::pair<double, std::chrono::system_clock::time_point> > inverterMinute;
	// map of device ID to reading at first tick of hour and its time point
	std::map<unsigned short, std::pair<double, std::chrono::system_clock::time_point> > inverterHour;
	// map of device ID to accumulated sum during this minute and the last tick time point
	std::map<unsigned short, std::pair<double, std::chrono::system_clock::time_point> > smartmeterMinute;
	// map of device ID to accumulated sum during this hour and the last tick time point
	std::map<unsigned short, std::pair<double, std::chrono::system_clock::time_point> > smartmeterHour;
};

#endif
