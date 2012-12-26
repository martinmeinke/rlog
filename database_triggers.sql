CREATE TRIGGER update_hourly AFTER  INSERT ON charts_solarentrytick
BEGIN
	INSERT OR REPLACE INTO charts_solarentryhour (time, device, lW) 
	VALUES (
		strftime('%Y-%m-%d %H', 'now') , 
		new.device,
		--maybe inconsistent... (although unlikely) use descending order and limit 1
		coalesce((select lW from charts_solarentryhour where time = strftime('%Y-%m-%d %H', 'now')) + new.lW / 360.0, new.lW/360.0)
    );
END

CREATE TRIGGER update_daily AFTER  INSERT ON charts_solarentrytick
BEGIN
	INSERT OR REPLACE INTO charts_solarentryday (time, device, lW) 
	VALUES (
		strftime('%Y-%m-%d', 'now') , 
		new.device,
		--maybe inconsistent... (although unlikely) use descending order and limit 1
		new.total
        );
END

CREATE TRIGGER update_monthly AFTER  INSERT ON charts_solarentryday
BEGIN
	INSERT OR REPLACE INTO charts_solarentrymonth (time, device, lW) 
	VALUES (
		strftime('%Y-%m', 'now') , 
		new.device,
		--maybe inconsistent... (although unlikely) use descending order and limit 1
		(select SUM(lW) FROM charts_solarentryday WHERE strftime('%Y-%m',  time) =  strftime('%Y-%m',  'now'))
    );
END

CREATE TRIGGER update_yearly AFTER  INSERT ON charts_solarentrymonth
BEGIN
	INSERT OR REPLACE INTO charts_solarentryyear(time, device, lW) 
	VALUES (
		strftime('%Y', 'now') , 
		new.device,
		--maybe inconsistent... (although unlikely) use descending order and limit 1
		(select SUM(lW) FROM charts_solarentryday WHERE strftime('%Y',  time) =  strftime('%Y',  'now'))
        );
END




