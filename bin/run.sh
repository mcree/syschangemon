#!/bin/bash
interpreters="
/usr/bin/python3.5
/usr/bin/python3.4
/usr/bin/python3.3
/usr/bin/python3.2
/usr/bin/python3
"

for interpreter in $interpreters; do

    if [ -x "$interpreter" ]; then
	PYTHONIOENCODING=utf8 "$interpreter" /usr/share/syschangemon/run.py $@
	exit $?
    fi

done

echo "python 3 interpreter not found" >&2
exit 1
