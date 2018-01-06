SELECT verify_user('testseries', 'testseries');
SELECT verify_series('testseries');
SET search_path='testseries','public';

INSERT INTO indexlist (indexcode, descrip, value) VALUES ('',   '', 1.000);
INSERT INTO indexlist (indexcode, descrip, value) VALUES ('i1', '', 1.000);
INSERT INTO classlist (classcode, descrip, indexcode, caridxrestrict, classmultiplier, carindexed, usecarflag, eventtrophy, champtrophy, secondruns, countedruns, modified) VALUES ('c1', '', '', '', 1.0, 't', 'f', 't', 't', 'f', 0, now());

INSERT INTO drivers (driverid, firstname, lastname, email) VALUES ('00000000-0000-0000-0000-000000000001', 'first', 'last', 'email');
INSERT INTO cars    (carid, driverid, classcode, indexcode, number, useclsmult, attr, modified) VALUES ('00000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001', 'c1', 'i1', 1, 'f', '{}', now());
INSERT INTO cars    (carid, driverid, classcode, indexcode, number, useclsmult, attr, modified) VALUES ('00000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000001', 'c1', 'i1', 1, 'f', '{}', now());
INSERT INTO events (eventid, name, date, regclosed, attr) VALUES ('00000000-0000-0000-0000-000000000010', 'name', now(), now(), '{}');

INSERT INTO runorder (eventid, course, rungroup, row, carid) VALUES ('00000000-0000-0000-0000-000000000010', 1, 1, 1, '00000000-0000-0000-0000-000000000002');

INSERT INTO runs (eventid, carid, course, run, raw, status, attr) VALUES ('00000000-0000-0000-0000-000000000010', '00000000-0000-0000-0000-000000000002', 1, 1, 1.0, 'OK', '{}');
INSERT INTO runs (eventid, carid, course, run, raw, status, attr) VALUES ('00000000-0000-0000-0000-000000000010', '00000000-0000-0000-0000-000000000002', 1, 2, 2.0, 'OK', '{}');
INSERT INTO runs (eventid, carid, course, run, raw, status, attr) VALUES ('00000000-0000-0000-0000-000000000010', '00000000-0000-0000-0000-000000000002', 1, 3, 3.0, 'OK', '{}');
INSERT INTO runs (eventid, carid, course, run, raw, status, attr) VALUES ('00000000-0000-0000-0000-000000000010', '00000000-0000-0000-0000-000000000002', 1, 4, 4.0, 'OK', '{}');

