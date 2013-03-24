BEGIN TRANSACTION;
INSERT INTO "charts_solarentrytickbackup" SELECT * FROM "charts_solarentrytick";
DELETE FROM "charts_solarentrytick";
END;
