syschangemon - System Change Monitor
==============================================================================

[![Build Status](https://travis-ci.org/mcree/syschangemon.svg?branch=master)](https://travis-ci.org/mcree/syschangemon)

Introduction
------------

Periodically collects system configuration (eg. conffiles in /etc, binary files in /sbin, etc.) for changes, 
it can even run external commands and store their stdout and stderr for change monitoring.

This can be useful as a HIDS (host based intrusion detection system) as well as in a shared
working environment where several users have administrative access to system configuration.

If changes are found it sends text and html reports to predefined email addresses. It also includes
relevant wtmp information in the reports.

For now only Linux/Unix based systems are supported. Support for Windows is not planned at the moment.

Similar software:

* [tripwire] (https://sourceforge.net/projects/tripwire/)
* [samhain] (http://la-samhna.de/samhain/index.html)
* [fcheck] (http://web.archive.org/web/20050415074059/www.geocities.com/fcheck2000/)
* [changetrack] (http://changetrack.sourceforge.net)
* [systraq] (http://www.systraq.com)

Requirements
------------

Python 3.4 or above with PIP. The project aims to have no external binary dependencies. 
You are welcome to backport to python 2.

Installation
------------

For all python based systems:

```
$ pip install -r requirements.txt

$ python setup.py install
```

For debian and ubuntu (tested under ubuntu trusty):

```
$ sudo apt-add-repository ppa:dh-virtualenv/daily

$ sudp apt-get update

$ sudo apt-get install -y debhelper dh-virtualenv python3.4

$ dpkg-buildpackage -uc -ub

$ dpkg -i ../syschangemon_*_all.deb
```

(PPA repository is planned)

Help with RPM package creation would be appreciated.

Configuration
-------------

Configuration files need to be placed under `/etc/syschangemon`. This directory contains the following files:

* `syschangemon.conf` - main configuration file, configures default paths, data retention, email sending and logging
* `plugins.d` - plugin configuration directory with the following files:
    * `command.conf` - configuration for external commands to be run during system state collection
    * `conffile.conf` - configuration for text file collection (depends on `file.conf`)
    * `file.conf` - configuration for filesystem data collection (specifies files to be included and excluded)
    * `storage.conf` - configuration for data storage, specifies sqlite3 database storage path
    * `sysinfo.conf` - configuration for basic system information collection
    * `wtmp.conf` - configuration for wtmp data collection
    
Refer to included sample configuration files for additional information.

The program is mainly meant to be run from CRON with a configuration similar to:

```
0 * * * * root [ -x /usr/sbin/syschangemon ] && /usr/sbin/syschangemon run --skip-empty-mail 2>&1 >/dev/null
```

Running with root privileges is not explicitly needed but is usually necessary to collect all the information.

Default paths:

* `/etc/syschangemon` - configuration files
* `/var/lib/syschangemon/storage/db.sqlite` - SQLite3 database file
* `/var/lib/syschangemon/templates` - text and html [Jinja2] (http://jinja.pocoo.org/docs/dev/templates/) templates for console and e-mail reporting
* `/etc/cron.d/syschangemon` - CRON configuration

Usage
-----

```
usage: syschangemon (sub-commands ...) [options ...] {arguments ...}

System change monitor

commands:

  cleanup
    clean up database, expunge old sessions and reports

  collect
    run collect session, store current system state to database

  diff
    diff two sessions and save report in database (default: most recent sessions)

   email-report
    email report from database (default: last report)

  export
    export system state stored in session as CSV (default: most recent session)

  list-reports
    list reports stored in database

  list-sessions
    list sessions stored in database

  print-report
    print report from database (default: last report)

  reset
    reset database - drop all sessions then run initial collect phase

  run
    run collect, diff, cleanup, print-report, email-report in this order

optional arguments:
  -h, --help            show this help message and exit
  --debug               toggle debug output
  --quiet               suppress all output
  -s, --skip-empty-mail
                        skip email sending if report contains no differences
  -t, --html            prefer HTML output when possible
  -r UUID, --report-uuid UUID
                        choose report by uuid (instead of most recent)
  -o UUID, --old-session-uuid UUID
                        choose old session by uuid (instead of second most
                        recent)
  -u UUID, --session-uuid UUID
                        choose session by uuid (instead of most recent)
  -V, --version         show version information and exit
```