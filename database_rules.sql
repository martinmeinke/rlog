-- Rule: upsert_eigenverbrauch ON charts_eigenverbrauch
-- DROP RULE upsert_eigenverbrauch ON charts_eigenverbrauch;
CREATE OR REPLACE RULE upsert_eigenverbrauch AS
    ON INSERT TO charts_eigenverbrauch
   WHERE (EXISTS ( SELECT 1
           FROM charts_eigenverbrauch charts_eigenverbrauch_1
          WHERE charts_eigenverbrauch_1."time" = new."time")) DO INSTEAD  UPDATE charts_eigenverbrauch SET eigenverbrauch = new.eigenverbrauch
  WHERE charts_eigenverbrauch."time" = new."time";

-- Rule: upsert_device ON charts_device
-- DROP RULE upsert_device ON charts_device;
CREATE OR REPLACE RULE upsert_device AS
    ON INSERT TO charts_device
   WHERE (EXISTS ( SELECT 1
           FROM charts_device charts_device_1
          WHERE charts_device_1.id = new.id)) DO INSTEAD  UPDATE charts_device SET model = new.model
  WHERE charts_device.id = new.id;
  
-- Rule: upsert_smartmeterentrymaxima ON charts_smartmeterdailymaxima
-- DROP RULE upsert_smartmeterentrymaxima ON charts_smartmeterdailymaxima;
CREATE OR REPLACE RULE upsert_smartmeterentrymaxima AS
    ON INSERT TO charts_smartmeterdailymaxima
   WHERE (EXISTS ( SELECT 1
           FROM charts_smartmeterdailymaxima charts_smartmeterdailymaxima_1
          WHERE charts_smartmeterdailymaxima_1."time" = new."time")) DO INSTEAD  UPDATE charts_smartmeterdailymaxima SET exacttime = new.exacttime, maximum = new.maximum
  WHERE charts_smartmeterdailymaxima."time" = new."time";
  
-- Rule: upsert_smartmeterentryday ON charts_smartmeterentryday
-- DROP RULE upsert_smartmeterentryday ON charts_smartmeterentryday;
CREATE OR REPLACE RULE upsert_smartmeterentryday AS
    ON INSERT TO charts_smartmeterentryday
   WHERE (EXISTS ( SELECT 1
           FROM charts_smartmeterentryday charts_smartmeterentryday_1
          WHERE charts_smartmeterentryday_1."time" = new."time")) DO INSTEAD  UPDATE charts_smartmeterentryday SET reading = new.reading, phase1 = new.phase1, phase2 = new.phase2, phase3 = new.phase3
  WHERE charts_smartmeterentryday."time" = new."time";
  
-- Rule: upsert_smartmeterentryhour ON charts_smartmeterentryhour
-- DROP RULE upsert_smartmeterentryhour ON charts_smartmeterentryhour;
CREATE OR REPLACE RULE upsert_smartmeterentryhour AS
    ON INSERT TO charts_smartmeterentryhour
   WHERE (EXISTS ( SELECT 1
           FROM charts_smartmeterentryhour charts_smartmeterentryhour_1
          WHERE charts_smartmeterentryhour_1."time" = new."time")) DO INSTEAD  UPDATE charts_smartmeterentryhour SET reading = new.reading, phase1 = new.phase1, phase2 = new.phase2, phase3 = new.phase3
  WHERE charts_smartmeterentryhour."time" = new."time";
  
-- Rule: upsert_smartmeterentryminute ON charts_smartmeterentryminute
-- DROP RULE upsert_smartmeterentryminute ON charts_smartmeterentryminute;
CREATE OR REPLACE RULE upsert_smartmeterentryminute AS
    ON INSERT TO charts_smartmeterentryminute
   WHERE (EXISTS ( SELECT 1
           FROM charts_smartmeterentryminute charts_smartmeterentryminute_1
          WHERE charts_smartmeterentryminute_1."time" = new."time")) DO INSTEAD  UPDATE charts_smartmeterentryminute SET exacttime = new.exacttime, reading = new.reading, phase1 = new.phase1, phase2 = new.phase2, phase3 = new.phase3
  WHERE charts_smartmeterentryminute."time" = new."time";
  
-- Rule: upsert_smartmeterentrymonth ON charts_smartmeterentrymonth
-- DROP RULE upsert_smartmeterentrymonth ON charts_smartmeterentrymonth;
CREATE OR REPLACE RULE upsert_smartmeterentrymonth AS
    ON INSERT TO charts_smartmeterentrymonth
   WHERE (EXISTS ( SELECT 1
           FROM charts_smartmeterentrymonth charts_smartmeterentrymonth_1
          WHERE charts_smartmeterentrymonth_1."time" = new."time")) DO INSTEAD  UPDATE charts_smartmeterentrymonth SET reading = new.reading, phase1 = new.phase1, phase2 = new.phase2, phase3 = new.phase3
  WHERE charts_smartmeterentrymonth."time" = new."time";

-- Rule: upsert_smartmeterentryyear ON charts_smartmeterentryyear
-- DROP RULE upsert_smartmeterentryyear ON charts_smartmeterentryyear;
CREATE OR REPLACE RULE upsert_smartmeterentryyear AS
    ON INSERT TO charts_smartmeterentryyear
   WHERE (EXISTS ( SELECT 1
           FROM charts_smartmeterentryyear charts_smartmeterentryyear_1
          WHERE charts_smartmeterentryyear_1."time" = new."time")) DO INSTEAD  UPDATE charts_smartmeterentryyear SET reading = new.reading, phase1 = new.phase1, phase2 = new.phase2, phase3 = new.phase3
  WHERE charts_smartmeterentryyear."time" = new."time";

-- Rule: upsert_solardailymaxima ON charts_solardailymaxima
-- DROP RULE upsert_solardailymaxima ON charts_solardailymaxima;
CREATE OR REPLACE RULE upsert_solardailymaxima AS
    ON INSERT TO charts_solardailymaxima
   WHERE (EXISTS ( SELECT 1
           FROM charts_solardailymaxima charts_solardailymaxima_1
          WHERE charts_solardailymaxima_1."time" = new."time" AND charts_solardailymaxima_1.device_id = new.device_id)) DO INSTEAD  UPDATE charts_solardailymaxima SET "lW" = new."lW", exacttime = new.exacttime
  WHERE charts_solardailymaxima."time" = new."time" AND charts_solardailymaxima.device_id = new.device_id;

-- Rule: upsert_solarentryday ON charts_solarentryday
-- DROP RULE upsert_solarentryday ON charts_solarentryday;
CREATE OR REPLACE RULE upsert_solarentryday AS
    ON INSERT TO charts_solarentryday
   WHERE (EXISTS ( SELECT 1
           FROM charts_solarentryday charts_solarentryday_1
          WHERE charts_solarentryday_1."time" = new."time" AND charts_solarentryday_1.device_id = new.device_id)) DO INSTEAD  UPDATE charts_solarentryday SET "lW" = new."lW"
  WHERE charts_solarentryday."time" = new."time" AND charts_solarentryday.device_id = new.device_id;

-- Rule: upsert_solarentryhour ON charts_solarentryhour
-- DROP RULE upsert_solarentryhour ON charts_solarentryhour;
CREATE OR REPLACE RULE upsert_solarentryhour AS
    ON INSERT TO charts_solarentryhour
   WHERE (EXISTS ( SELECT 1
           FROM charts_solarentryhour charts_solarentryhour_1
          WHERE charts_solarentryhour_1."time" = new."time" AND charts_solarentryhour_1.device_id = new.device_id)) DO INSTEAD  UPDATE charts_solarentryhour SET "lW" = new."lW"
  WHERE charts_solarentryhour."time" = new."time" AND charts_solarentryhour.device_id = new.device_id;

-- Rule: upsert_solarentryminute ON charts_solarentryminute
-- DROP RULE upsert_solarentryminute ON charts_solarentryminute;
CREATE OR REPLACE RULE upsert_solarentryminute AS
    ON INSERT TO charts_solarentryminute
   WHERE (EXISTS ( SELECT 1
           FROM charts_solarentryminute charts_solarentryminute_1
          WHERE charts_solarentryminute_1."time" = new."time" AND charts_solarentryminute_1.device_id = new.device_id)) DO INSTEAD  UPDATE charts_solarentryminute SET exacttime = new.exacttime, "lW" = new."lW"
  WHERE charts_solarentryminute."time" = new."time" AND charts_solarentryminute.device_id = new.device_id;

-- Rule: upsert_solarentrymonth ON charts_solarentrymonth
-- DROP RULE upsert_solarentrymonth ON charts_solarentrymonth;
CREATE OR REPLACE RULE upsert_solarentrymonth AS
    ON INSERT TO charts_solarentrymonth
   WHERE (EXISTS ( SELECT 1
           FROM charts_solarentrymonth charts_solarentrymonth_1
          WHERE charts_solarentrymonth_1."time" = new."time" AND charts_solarentrymonth_1.device_id = new.device_id)) DO INSTEAD  UPDATE charts_solarentrymonth SET "lW" = new."lW"
  WHERE charts_solarentrymonth."time" = new."time" AND charts_solarentrymonth.device_id = new.device_id;

-- Rule: upsert_solarentryyear ON charts_solarentryyear
-- DROP RULE upsert_solarentryyear ON charts_solarentryyear;
CREATE OR REPLACE RULE upsert_solarentryyear AS
    ON INSERT TO charts_solarentryyear
   WHERE (EXISTS ( SELECT 1
           FROM charts_solarentryyear charts_solarentryyear_1
          WHERE charts_solarentryyear_1."time" = new."time" AND charts_solarentryyear_1.device_id = new.device_id)) DO INSTEAD  UPDATE charts_solarentryyear SET "lW" = new."lW"
  WHERE charts_solarentryyear."time" = new."time" AND charts_solarentryyear.device_id = new.device_id;

