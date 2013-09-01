DROP TRIGGER IF EXISTS update_minutely;
DROP TRIGGER IF EXISTS update_maxima;
DROP TRIGGER IF EXISTS update_hourly;
DROP TRIGGER IF EXISTS update_daily;
DROP TRIGGER IF EXISTS update_monthly;
DROP TRIGGER IF EXISTS update_yearly;

--TODO: determine automatically!
INSERT INTO charts_device VALUES (1, "Device 1");
INSERT INTO charts_device VALUES (2, "Device 2");
INSERT INTO charts_device VALUES (3, "Device 3");

--CREATE TRIGGER update_minutely AFTER  INSERT ON charts_solarentrytick
--BEGIN
--	INSERT OR REPLACE INTO charts_solarentryminute (time, device_id, lW) 
--	VALUES (
--		strftime('%Y-%m-%d %H:%M:00', 'now') , 
--		new.device_id,
--		coalesce((select lW from charts_solarentryminute where device_id = new.device_id AND time = strftime('%Y-%m-%d %H:%M:00', 'now')) + new.lW / 360.0, new.lW/360.0)
--  );
--END;

CREATE TRIGGER update_minutely AFTER INSERT ON charts_solarentrytick
BEGIN
	INSERT OR REPLACE INTO charts_solarentryminute (time, exacttime, device_id, lW) 
	VALUES (
		strftime('%Y-%m-%d %H:%M:00', 'now', 'localtime'), 		
		strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime'), 
		new.device_id,
--		COALESCE(
--	            (select lW 
--	                * (select CAST(strftime('%S', exacttime) AS FLOAT)/60
--	                    from charts_solarentryminute 
--	                    where device_id = new.device_id 
--	                        AND time = strftime('%Y-%m-%d %H:%M:00', 'now', 'localtime'))
--	                        
--	                + (select (60 - CAST(strftime('%S', exacttime) AS FLOAT))/60 * (new.lW/60)
--                        from charts_solarentryminute 
--                        where device_id = new.device_id 
--                            AND time = strftime('%Y-%m-%d %H:%M:00', 'now', 'localtime'))
--                            
--		            from charts_solarentryminute 
--		            where device_id = new.device_id 
--		                AND time = strftime('%Y-%m-%d %H:%M:00', 'now', 'localtime')
--		        )
--		    ,
		    new.lW/60.0
--) -- no data for this minute yet available
    );
END;

CREATE TRIGGER update_maxima AFTER INSERT ON charts_solarentrytick
BEGIN
	INSERT OR REPLACE INTO charts_solardailymaxima (time, device_id, lW, exacttime) 
	VALUES (
		strftime('%Y-%m-%d', new.time) , 
		new.device_id,
		max(new.lW,
			ifnull((SELECT lW
               	FROM charts_solardailymaxima
               	WHERE device_id = new.device_id
               		AND time = strftime('%Y-%m-%d', new.time)
               	),
            0)
        ),
        ifnull((SELECT exacttime 
			FROM charts_solardailymaxima 	
			WHERE device_id = new.device_id
				AND lW >= new.lW
            	AND time = strftime('%Y-%m-%d', new.time)), datetime('now', 'localtime'))
    );
END;

CREATE TRIGGER update_hourly AFTER INSERT ON charts_solarentryminute
BEGIN
	INSERT OR REPLACE INTO charts_solarentryhour (time, device_id, lW) 
	VALUES (
		strftime('%Y-%m-%d %H:00:00', 'now', 'localtime') , 
		new.device_id,
		(select SUM(lW) 
			from charts_solarentryminute 
			where device_id = new.device_id 
				AND strftime('%Y-%m-%d %H:00:00', time) = strftime('%Y-%m-%d %H:00:00', 'now', 'localtime'))
    );
END;

CREATE TRIGGER update_daily AFTER INSERT ON charts_solarentrytick
BEGIN
	INSERT OR REPLACE INTO charts_solarentryday (time, device_id, lW) 
	VALUES (
		strftime('%Y-%m-%d', 'now', 'localtime') , 
		new.device_id,
		new.total
    );
END;

CREATE TRIGGER update_monthly AFTER INSERT ON charts_solarentryday
BEGIN
	INSERT OR REPLACE INTO charts_solarentrymonth (time, device_id, lW) 
	VALUES (
		strftime('%Y-%m-01', 'now', 'localtime') , 
		new.device_id,
		(select SUM(lW) 
			FROM charts_solarentryday 
			WHERE device_id = new.device_id 
				AND strftime('%Y-%m-01',  time) = strftime('%Y-%m-01',  'now', 'localtime'))
    );
END;

CREATE TRIGGER update_yearly AFTER INSERT ON charts_solarentrymonth
BEGIN
	INSERT OR REPLACE INTO charts_solarentryyear(time, device_id, lW) 
	VALUES (
		strftime('%Y-01-01', 'now', 'localtime') , 
		new.device_id,
		(select SUM(lW) 
			FROM charts_solarentryday 
			WHERE device_id = new.device_id 
				AND strftime('%Y-01-01',  time) =  strftime('%Y-01-01',  'now', 'localtime'))
    );
END;

--a basic configuration entry
INSERT INTO charts_settings (active, kwhforsound, soundfile) VALUES (1, 1, "coin.mp3");

CREATE INDEX IF NOT EXISTS IDX_DEV_ID ON charts_solarentrytick (device_id);

PRAGMA main.page_size = 4096;
PRAGMA main.cache_size=10000;
PRAGMA main.locking_mode=EXCLUSIVE;
PRAGMA main.synchronous=NORMAL;
PRAGMA main.journal_mode=WAL;
PRAGMA main.cache_size=5000;
PRAGMA main.temp_store = MEMORY;
