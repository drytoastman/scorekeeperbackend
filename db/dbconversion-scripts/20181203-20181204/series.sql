ALTER TABLE runorder RENAME TO oldrunorder;
ALTER TABLE classorder RENAME TO oldclassorder;

CREATE TABLE runorder (
    eventid  UUID       NOT NULL REFERENCES events,
    course   INTEGER    NOT NULL CHECK (course > 0),
    rungroup INTEGER    NOT NULL CHECK (rungroup > 0),
    cars     UUID[]     NOT NULL,
    modified TIMESTAMP  NOT NULL DEFAULT now(),
    PRIMARY KEY (eventid, course, rungroup)
);
REVOKE ALL ON runorder FROM public;
GRANT  ALL ON runorder TO <seriesname>;
CREATE TRIGGER ordermod AFTER INSERT OR UPDATE OR DELETE ON runorder FOR EACH ROW EXECUTE PROCEDURE logmods('<seriesname>.serieslog');
CREATE TRIGGER ordercon BEFORE INSERT OR UPDATE ON runorder FOR EACH ROW EXECUTE PROCEDURE runorderconstraints('<seriesname>');
CREATE TRIGGER orderuni BEFORE UPDATE ON runorder FOR EACH ROW EXECUTE PROCEDURE updatechecks('eventid', 'course', 'rungroup', 'row');
COMMENT ON TABLE runorder IS 'This is the list of cars in each rungroup as seen in data entry';


CREATE TABLE classorder (
    eventid   UUID      NOT NULL REFERENCES events,
    rungroup  INTEGER   NOT NULL CHECK (rungroup > 0),
    classes   TEXT[]    NOT NULL,
    modified  TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (eventid, rungroup)
);
REVOKE ALL ON classorder FROM public;
GRANT  ALL ON classorder TO <seriesname>;
CREATE TRIGGER classordermod AFTER INSERT OR UPDATE OR DELETE ON classorder FOR EACH ROW EXECUTE PROCEDURE logmods('<seriesname>.serieslog');
CREATE TRIGGER classordercon BEFORE INSERT OR UPDATE ON classorder FOR EACH ROW EXECUTE PROCEDURE classorderconstraints('<seriesname>');
CREATE TRIGGER classorderuni BEFORE UPDATE ON classorder FOR EACH ROW EXECUTE PROCEDURE updatechecks('eventid', 'classcode');
COMMENT ON TABLE classorder IS 'the ordering of classes inside each run group, generally only used in the Pro event for grid ordering';


INSERT INTO runorder   (SELECT eventid, course, rungroup, array_agg(carid     ORDER BY row)    FROM oldrunorder   GROUP BY eventid, course, rungroup);
INSERT INTO classorder (SELECT eventid, rungroup,         array_agg(classcode ORDER BY gorder) FROM oldclassorder GROUP BY eventid, rungroup);
