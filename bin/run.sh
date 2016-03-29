#!/bin/bash
interpreters="
/usr/bin/python3.5
/usr/bin/python3.4
/usr/bin/python3.3
/usr/bin/python3.2
/usr/bin/python3
"

echo -e "$interpreters" | while read interpreter; do

    if [ -x "$interpreter" ]; then
	"$interpreter" /usr/share/syschangemon/run.py $@
	exit $?
    fi

done
