ALTER TABLE mergeservers ADD COLUMN quickruns TEXT;

CREATE TABLE localeventstream (
    etype TEXT      NOT NULL,
    event JSONB     NOT NULL,
    time  TIMESTAMP NOT NULL
);
CREATE INDEX ON localeventstream(time);
REVOKE ALL   ON localeventstream FROM public;
GRANT  ALL   ON localeventstream TO mergeaccess;
COMMENT ON TABLE localeventstream IS 'Local events useful for serving up to the announcer interface, not merged';

