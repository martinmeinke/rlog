BEGIN TRANSACTION;
INSERT INTO "charts_solarentrytickbackup" ("time","device_id","gV","gA","gW","lV","lA","lW","temp","total")SELECT "time","device_id","gV","gA","gW","lV","lA","lW","temp","total" FROM "charts_solarentrytick";
DELETE FROM "charts_solarentrytick";
END;
