INSERT INTO indexlist (indexcode, descrip, value) VALUES ('', 'No Index', 1.0) ON CONFLICT DO NOTHING;
INSERT INTO classlist (classcode,descrip,indexcode,caridxrestrict,classmultiplier,carindexed,usecarflag,eventtrophy,champtrophy,secondruns,countedruns) VALUES ('HOLD','PlaceHolder Class','','',1.0,'f','f','f','f','f',0) ON CONFLICT DO NOTHING;

ALTER TABLE events ADD COLUMN regtype INTEGER NOT NULL DEFAULT 0;

ALTER TABLE runs ADD COLUMN rungroup INTEGER NOT NULL DEFAULT 0;
DROP TRIGGER rununi ON runs;
WITH sub AS (SELECT eventid,course,rungroup,cars FROM runorder) UPDATE runs SET rungroup=sub.rungroup FROM sub WHERE runs.eventid=sub.eventid AND runs.course=sub.course and runs.carid=ANY(sub.cars); 
ALTER TABLE runs DROP CONSTRAINT runs_pkey;
ALTER TABLE runs ADD PRIMARY KEY (eventid, carid, course, rungroup, run);
CREATE TRIGGER rununi BEFORE UPDATE ON runs FOR EACH ROW EXECUTE PROCEDURE updatechecks('eventid', 'carid', 'course', 'rungroup', 'run');

ALTER TABLE registered ADD COLUMN session TEXT NOT NULL DEFAULT '';
ALTER TABLE registered DROP CONSTRAINT registered_pkey;
ALTER TABLE registered ADD PRIMARY KEY (eventid, carid, session);
DROP TRIGGER reguni ON registered;
CREATE TRIGGER reguni BEFORE UPDATE ON registered FOR EACH ROW EXECUTE PROCEDURE updatechecks('eventid', 'carid', 'session');

ALTER TABLE payments ADD COLUMN session TEXT NOT NULL DEFAULT '';

ALTER TABLE runorder DROP CONSTRAINT runorder_pkey;
ALTER TABLE runorder ADD PRIMARY KEY (eventid, course, rungroup);
DROP TRIGGER ordercon ON runorder;
CREATE CONSTRAINT TRIGGER ordercon AFTER INSERT OR UPDATE ON runorder DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE PROCEDURE runorderconstraints();
DROP TRIGGER orderuni ON runorder;
CREATE TRIGGER orderuni BEFORE UPDATE ON runorder FOR EACH ROW EXECUTE PROCEDURE updatechecks('eventid', 'course', 'rungroup');

DROP TRIGGER classordercon ON classorder;
CREATE CONSTRAINT TRIGGER classordercon AFTER INSERT OR UPDATE ON classorder DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE PROCEDURE classorderconstraints();
