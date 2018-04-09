ALTER  TABLE weekendmembers ADD COLUMN uniqueid UUID NOT NULL PRIMARY KEY;
ALTER  TABLE weekendmembers DROP COLUMN area;
ALTER  TABLE weekendmembers DROP COLUMN region;
DROP   TRIGGER weekuni ON weekendmembers;
CREATE TRIGGER weekuni BEFORE UPDATE ON weekendmembers FOR EACH ROW EXECUTE PROCEDURE updatechecks('uniqueid');
