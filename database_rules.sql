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
