
# Helper for sync and testing

def dosync(db, merge, hosts=None):
    with db.cursor() as cur:
        if hosts:
            cur.execute("UPDATE mergeservers SET lastcheck='epoch', nextcheck='epoch' WHERE hostname in %s", (hosts,))
        else:
            cur.execute("UPDATE mergeservers SET lastcheck='epoch', nextcheck='epoch'")
    db.commit()
    merge.runonce()


def verify_object(syncx, pid, coltuple, attrtuple, sqlget):
    obj = {}
    for k in syncx:
        with syncx[k].cursor() as cur:
            cur.execute(sqlget, (pid,))
            obj[k] = cur.fetchone()

    if coltuple:
        for db in obj:
            for key, expected in coltuple: 
                assert obj[db][key] == expected
    else:
        for db in obj:
            if obj[db] is not None:
                import logging
                logging.getLogger(__name__).warning("Obj not none in {}".format(db))
                import pdb
                pdb.set_trace()
            assert obj[db] == None

    if attrtuple:
        for key, expected in attrtuple: 
            for db in obj:
                assert obj[db]['attr'].get(key, None) == expected


def verify_driver(syncx, driverid, coltuple, attrtuple):
    verify_object(syncx, driverid, coltuple, attrtuple, "SELECT * FROM drivers WHERE driverid=%s")

def    verify_car(syncx, carid, coltuple, attrtuple):
    verify_object(syncx, carid, coltuple, attrtuple, "SELECT * FROM cars WHERE carid=%s")

def verify_index( syncx, indexcode, coltuple):
    verify_object(syncx, indexcode, coltuple, (), "SELECT * FROM indexlist WHERE indexcode=%s")

def verify_account(syncx, accountid, coltuple):
    verify_object( syncx, accountid, coltuple, (), "SELECT * FROM paymentaccounts WHERE accountid=%s")

def verify_item( syncx,  itemid, coltuple):
    verify_object(syncx, itemid, coltuple, (), "SELECT * FROM paymentitems WHERE itemid=%s")

def verify_weekend(syncx, uid, coltuple):
    verify_object( syncx, uid, coltuple, (), "SELECT * FROM weekendmembers WHERE uniqueid=%s")

def verify_update_logs_only_changes(syncx):
    for db in syncx:
        with syncx[db].cursor() as cur:
            cur.execute("SELECT * from publiclog where tablen='drivers' and action='U'")
            for row in cur.fetchall():
                old = row['olddata']
                new = row['newdata']

                for k in list(old.get('attr', dict()).keys()):
                    old[k] = old['attr'].pop(k)
                for k in list(new.get('attr', dict()).keys()):
                    new[k] = new['attr'].pop(k)

                diff = {}
                for k in new:
                    if k not in old:
                       diff[k] = (None, new[k])
                    elif old[k] != new[k]:
                       diff[k] = (old[k], new[k])
                for k in old.keys() - new.keys():
                    diff[k] = (old[k], None)

                assert(set(diff.keys()) != set(['modified']))

def verify_totalhash(syncx):
    hashes = {}
    for db in syncx:
        with syncx[db].cursor() as cur:
            cur.execute("SELECT hostname,mergestate from mergeservers")
            for row in cur.fetchall():
                hashes[db,row['hostname']] = row['mergestate']['testseries']['totalhash']

    ref = next(iter(hashes.values()))
    if not all(x == ref for x in hashes.values()):
        log.error("Non-matching hashes: {}".format(hashes))
        assert False
