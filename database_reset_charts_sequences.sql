BEGIN;
SELECT setval(pg_get_serial_sequence('"charts_device"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "charts_device";
SELECT setval(pg_get_serial_sequence('"charts_solarentrytick"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "charts_solarentrytick";
SELECT setval(pg_get_serial_sequence('"charts_solarentryminute"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "charts_solarentryminute";
SELECT setval(pg_get_serial_sequence('"charts_solarentryhour"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "charts_solarentryhour";
SELECT setval(pg_get_serial_sequence('"charts_solarentryday"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "charts_solarentryday";
SELECT setval(pg_get_serial_sequence('"charts_solarentrymonth"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "charts_solarentrymonth";
SELECT setval(pg_get_serial_sequence('"charts_solarentryyear"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "charts_solarentryyear";
SELECT setval(pg_get_serial_sequence('"charts_solardailymaxima"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "charts_solardailymaxima";
SELECT setval(pg_get_serial_sequence('"charts_smartmeterentrytick"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "charts_smartmeterentrytick";
SELECT setval(pg_get_serial_sequence('"charts_reward"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "charts_reward";
SELECT setval(pg_get_serial_sequence('"charts_settings"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "charts_settings";

COMMIT;
