
# Helper for sync and testing

def dosync(db, merge):
    with db.cursor() as cur:
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

