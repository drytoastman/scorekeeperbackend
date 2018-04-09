ALTER  TABLE weekendmembers ADD COLUMN uniqueid UUID NOT NULL PRIMARY KEY;
DROP   TRIGGER weekuni ON weekendmembers;
CREATE TRIGGER weekuni BEFORE UPDATE ON weekendmembers FOR EACH ROW EXECUTE PROCEDURE updatechecks('uniqueid');
