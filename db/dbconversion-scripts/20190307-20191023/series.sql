DROP TRIGGER ordercon ON runorder;
CREATE CONSTRAINT TRIGGER ordercon AFTER INSERT OR UPDATE ON runorder DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE PROCEDURE runorderconstraints('<seriesname>');

DROP TRIGGER classordercon ON classorder;
CREATE CONSTRAINT TRIGGER classordercon AFTER INSERT OR UPDATE ON classorder DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE PROCEDURE classorderconstraints('<seriesname>');

ALTER TABLE events ADD COLUMN session TEXT[] NOT NULL DEFAULT '{}';

ALTER TABLE registered ADD COLUMN session TEXT NOT NULL DEFAULT '';
ALTER TABLE registered DROP CONSTRAINT registered_pkey;
ALTER TABLE registered ADD PRIMARY KEY (eventid, carid, session);
DROP TRIGGER reguni ON registered;
CREATE TRIGGER reguni BEFORE UPDATE ON registered FOR EACH ROW EXECUTE PROCEDURE updatechecks('eventid', 'carid', 'session');

INSERT INTO classlist (classcode,descrip,indexcode,caridxrestrict,classmultiplier,carindexed,usecarflag,eventtrophy,champtrophy,secondruns,countedruns) VALUES ('HOLD','PlaceHolder Class','','',1.0,'f','f','f','f','f',0) ON CONFLICT DO NOTHING;
INSERT INTO indexlist (indexcode, descrip, value) VALUES ('', 'No Index', 1.0) ON CONFLICT DO NOTHING;
