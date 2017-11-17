#!/bin/bash

while true; do
    curversion=$(psql -U postgres -d scorekeeper -A -t -c "select version from version")
    found=0
    for ent in *; do
        if [ -d "${ent}" ]; then
            IFS='-' read -ra SCHEMA <<< "${ent}"
            inversion=${SCHEMA[0]}
            outversion=${SCHEMA[1]}
            if [ "$inversion" == "$curversion" ] && [ "X$outversion" != "X" ]; then
                public=""
                series=""
                if [ -f "$ent/public.sql" ]; then
                    public=`cat $ent/public.sql | tr -d "\n" | sed "s/'/''/g"`
                fi
                if [ -f "$ent/series.sql" ]; then
                    public=`cat $ent/series.sql | tr -d "\n" | sed "s/'/''/g"`
                fi
                echo "Converting $inversion"
                psql -U postgres -d scorekeeper -c "SELECT upgrade('$series', '$public', '$outversion');"
                found=1
            fi
        fi
    done

    if [ $found -lt 1 ]; then
        break
    fi
done

echo "Finished at $curversion"
