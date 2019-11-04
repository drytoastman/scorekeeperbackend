INSERT INTO indexlist (indexcode, descrip, value) VALUES ('',   '', 1.000);
INSERT INTO indexlist (indexcode, descrip, value) VALUES ('i1', '', 1.000);
INSERT INTO classlist (classcode, descrip, indexcode, caridxrestrict, classmultiplier, carindexed, usecarflag, eventtrophy, champtrophy, secondruns, countedruns, modified) VALUES ('c1', '', '', '', 1.0, 't', 'f', 't', 't', 'f', 0, now());
INSERT INTO classlist (classcode, descrip, indexcode, caridxrestrict, classmultiplier, carindexed, usecarflag, eventtrophy, champtrophy, secondruns, countedruns, modified) VALUES ('c2', '', '', '', 1.0, 't', 'f', 't', 't', 'f', 0, now());
INSERT INTO classlist (classcode, descrip, indexcode, caridxrestrict, classmultiplier, carindexed, usecarflag, eventtrophy, champtrophy, secondruns, countedruns, modified) VALUES ('c3', '', '', '', 1.0, 't', 'f', 't', 't', 'f', 0, now());
INSERT INTO classlist (classcode, descrip, indexcode, caridxrestrict, classmultiplier, carindexed, usecarflag, eventtrophy, champtrophy, secondruns, countedruns, modified) VALUES ('c4', '', '', '', 1.0, 't', 'f', 't', 't', 'f', 0, now());
INSERT INTO classlist (classcode, descrip, indexcode, caridxrestrict, classmultiplier, carindexed, usecarflag, eventtrophy, champtrophy, secondruns, countedruns, modified) VALUES ('c5', '', '', '', 1.0, 't', 'f', 't', 't', 'f', 0, now());

INSERT INTO drivers (driverid, firstname, lastname, email, username, password, created) VALUES ('00000000-0000-0000-0000-000000000001', 'first', 'last', 'email', 'username', '$2b$12$g0z0JiGEuCudjhUF.5aawOlho3fpnPqKrV1EALTd1Cl/ThQQpFi2K', '1970-01-01T00:00:00');
INSERT INTO cars    (carid, driverid, classcode, indexcode, number, useclsmult, attr, modified) VALUES ('00000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001', 'c1', 'i1', 1, 'f', '{}', now());
INSERT INTO cars    (carid, driverid, classcode, indexcode, number, useclsmult, attr, modified) VALUES ('00000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000001', 'c1', 'i1', 1, 'f', '{}', now());
INSERT INTO cars    (carid, driverid, classcode, indexcode, number, useclsmult, attr, modified) VALUES ('00000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000001', 'c1', 'i1', 1, 'f', '{}', now());
INSERT INTO events (eventid, name, date, regclosed, attr) VALUES ('00000000-0000-0000-0000-000000000010', 'name', now(), now(), '{}');

INSERT INTO runorder (eventid, course, rungroup, cars) VALUES ('00000000-0000-0000-0000-000000000010', 1, 1, '{00000000-0000-0000-0000-000000000002}');

INSERT INTO runs (eventid, carid, course, rungroup, run, raw, status, attr) VALUES ('00000000-0000-0000-0000-000000000010', '00000000-0000-0000-0000-000000000002', 1, 1, 1, 1.0, 'OK', '{}');
INSERT INTO runs (eventid, carid, course, rungroup, run, raw, status, attr) VALUES ('00000000-0000-0000-0000-000000000010', '00000000-0000-0000-0000-000000000002', 1, 1, 2, 2.0, 'OK', '{}');
INSERT INTO runs (eventid, carid, course, rungroup, run, raw, status, attr) VALUES ('00000000-0000-0000-0000-000000000010', '00000000-0000-0000-0000-000000000002', 1, 1, 3, 3.0, 'OK', '{}');
INSERT INTO runs (eventid, carid, course, rungroup, run, raw, status, attr) VALUES ('00000000-0000-0000-0000-000000000010', '00000000-0000-0000-0000-000000000002', 1, 1, 4, 4.0, 'OK', '{}');
