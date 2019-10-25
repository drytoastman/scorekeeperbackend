DROP TRIGGER ordercon ON runorder;
CREATE CONSTRAINT TRIGGER ordercon AFTER INSERT OR UPDATE ON runorder DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE PROCEDURE runorderconstraints('<seriesname>');

DROP TRIGGER classordercon ON classorder;
CREATE CONSTRAINT TRIGGER classordercon AFTER INSERT OR UPDATE ON classorder DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE PROCEDURE classorderconstraints('<seriesname>');

ALTER TABLE events ADD COLUMN spclasses TEXT[] NOT NULL DEFAULT '{}';

DELETE FROM registered WHERE carid IN (SELECT carid FROM cars WHERE classcode='HOLD');
DELETE FROM runs       WHERE carid IN (SELECT carid FROM nwr2019.cars WHERE classcode='HOLD');
DELETE FROM cars       WHERE classcode='HOLD';
DELETE FROM classlist  WHERE classcode='HOLD';

INSERT INTO classlist (classcode, descrip, indexcode, caridxrestrict, classmultiplier, carindexed, usecarflag, eventtrophy, champtrophy, secondruns, countedruns) VALUES ('_HOLD', 'Unknown Class', '', '', 1.0, 'f', 'f', 'f', 'f', 'f', 0);
INSERT INTO classlist (classcode, descrip, indexcode, caridxrestrict, classmultiplier, carindexed, usecarflag, eventtrophy, champtrophy, secondruns, countedruns) VALUES ('_AM',   'AM Session',    '', '', 1.0, 'f', 'f', 't', 'f', 'f', 0);
INSERT INTO classlist (classcode, descrip, indexcode, caridxrestrict, classmultiplier, carindexed, usecarflag, eventtrophy, champtrophy, secondruns, countedruns) VALUES ('_PM',   'PM Session',    '', '', 1.0, 'f', 'f', 't', 'f', 'f', 0);
INSERT INTO classlist (classcode, descrip, indexcode, caridxrestrict, classmultiplier, carindexed, usecarflag, eventtrophy, champtrophy, secondruns, countedruns) VALUES ('_DAY',  'Day Session',   '', '', 1.0, 'f', 'f', 't', 'f', 'f', 0);
