#!/bin/bash

while true; do
    version=$(psql -U postgres -d scorekeeper -A -t -c "select version from version")
    if [ -d $version ]; then
        echo "Converting $version"
        for f in /dbconversion-scripts/$version/*; do
            case "$f" in
                *.sql) echo "$0: running $f"; psql -U postgres -d scorekeeper -f "$f" ;;
                *)     echo "$0: ignoring $f" ;;
            esac
        done
    else
        echo "Finished at $version"
        break
    fi
done

