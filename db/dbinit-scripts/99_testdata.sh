SERIES=pro2017
if [ -f /tmp/$SERIES.pgdump ]; then
    psql -U postgres -c "CREATE ROLE $SERIES WITH PASSWORD '$SERIES'"
    psql -U postgres -c "GRANT $SERIES TO localuser"
    pg_restore -d postgres -U postgres -C -c -e /tmp/$SERIES.pgdump
fi

