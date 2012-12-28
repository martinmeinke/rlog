CREATE TRIGGER update_hourly AFTER  INSERT ON charts_solarentrytick
BEGIN
	INSERT OR REPLACE INTO charts_solarentryhour (time, device_id, lW) 
	VALUES (
		strftime('%Y-%m-%d %H', 'now') , 
		new.device_id,
		coalesce((select lW from charts_solarentryhour where device_id = new.device_id AND time = strftime('%Y-%m-%d %H', 'now')) + new.lW / 360.0, new.lW/360.0)
    );
END;

CREATE TRIGGER update_daily AFTER  INSERT ON charts_solarentrytick
BEGIN
	INSERT OR REPLACE INTO charts_solarentryday (time, device_id, lW) 
	VALUES (
		strftime('%Y-%m-%d', 'now') , 
		new.device_id,
		new.total
    );
END;

CREATE TRIGGER update_monthly AFTER  INSERT ON charts_solarentryday
BEGIN
	INSERT OR REPLACE INTO charts_solarentrymonth (time, device_id, lW) 
	VALUES (
		strftime('%Y-%m', 'now') , 
		new.device_id,
		(select SUM(lW) FROM charts_solarentryday WHERE device_id = new.device_id AND strftime('%Y-%m',  time) =  strftime('%Y-%m',  'now'))
    );
END;

CREATE TRIGGER update_yearly AFTER  INSERT ON charts_solarentrymonth
BEGIN
	INSERT OR REPLACE INTO charts_solarentryyear(time, device_id, lW) 
	VALUES (
		strftime('%Y', 'now') , 
		new.device_id,
		(select SUM(lW) FROM charts_solarentryday WHERE device_id = new.device_id AND strftime('%Y',  time) =  strftime('%Y',  'now'))
    );
END;

INSERT INTO charts_settings (active, kwhforsound, soundfile) VALUES (1, 1, "coin.mp3");