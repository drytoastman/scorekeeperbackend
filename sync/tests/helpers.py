
# Helper for sync and testing

def dosync(db, merge):
    with db.cursor() as cur:
        cur.execute("UPDATE mergeservers SET lastcheck='epoch', nextcheck='epoch'")
    db.commit()
    merge.runonce()


def verify_object(synca, syncb, pid, coltuple, attrtuple, sqlget):
    with synca.cursor() as cura, syncb.cursor() as curb:
        cura.execute(sqlget, (pid,))
        curb.execute(sqlget, (pid,))
        obja = cura.fetchone()
        objb = curb.fetchone()

    if coltuple:
        for key, expected in coltuple: 
            assert obja[key] == expected
            assert objb[key] == expected
    else:
        assert obja == None
        assert objb == None

    if attrtuple:
        for key, expected in attrtuple: 
            assert obja['attr'].get(key, None) == expected
            assert objb['attr'].get(key, None) == expected


def verify_driver(synca, syncb, driverid, coltuple, attrtuple):
    verify_object(synca, syncb, driverid, coltuple, attrtuple, "SELECT * FROM drivers WHERE driverid=%s")

def    verify_car(synca, syncb, carid, coltuple, attrtuple):
    verify_object(synca, syncb, carid, coltuple, attrtuple, "SELECT * FROM cars WHERE carid=%s")

def verify_index(synca, syncb, indexcode, coltuple):
    verify_object(synca, syncb, indexcode, coltuple, (), "SELECT * FROM indexlist WHERE indexcode=%s")

def verify_account(synca, syncb, accountid, coltuple):
    verify_object(synca, syncb, accountid, coltuple, (), "SELECT * FROM paymentaccounts WHERE accountid=%s")

def verify_item(synca, syncb, itemid, coltuple):
    verify_object(synca, syncb, itemid, coltuple, (), "SELECT * FROM paymentitems WHERE itemid=%s")

def verify_weekend(synca, syncb, uid, coltuple):
    verify_object(synca, syncb, uid, coltuple, (), "SELECT * FROM weekendmembers WHERE uniqueid=%s")

