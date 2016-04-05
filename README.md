syschangemon - System Change Monitor
==============================================================================

[![Build Status](https://travis-ci.org/mcree/syschangemon.svg?branch=master)](https://travis-ci.org/mcree/syschangemon)
[![codecov.io](https://codecov.io/github/mcree/syschangemon/coverage.svg?branch=master)](https://codecov.io/github/mcree/syschangemon?branch=master)

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

Python 3.2 or above with PIP. The project aims to have no external binary dependencies.
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
$ sudo apt-get install -y debhelper python3.4

$ dpkg-buildpackage -uc -ub

$ dpkg -i ../syschangemon_*_all.deb
```

Or you can use our packagecloud.io repository:
```
$ curl -s https://packagecloud.io/install/repositories/mcree/syschangemon/script.deb.sh | sudo bash

$ sudo apt-get -y install syschangemon
```

Alternatively add this to your `/etc/apt/sources.list` file:

```
deb https://packagecloud.io/mcree/syschangemon/ubuntu/ trusty main
deb-src https://packagecloud.io/mcree/syschangemon/ubuntu/ trusty main
```

then run:

```
$ sudo apt-get update

$ sudo apt-get -y install syschangemon
```

You can use the same package for:
* debian/wheezy
* debian/jessie
* ubuntu/precise
* ubuntu/trusty

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

Sample Report
-------------

```
session         | 2016-03-29 10:00:01 CEST (old)                     | 2016-03-29 11:00:01 CEST (new)                    
================+====================================================+===================================================
uuid            | 4aba3e8b-e633-4ef4-8a67-f21f02a619d4               | f4caa782-80a6-4c3e-838a-430ae3cf88ce              
start_time      | 2016-03-29 10:00:01.449584+02:00                   | 2016-03-29 11:00:01.585507+02:00                  
end_time        | 2016-03-29 10:01:03.464166+02:00                   | 2016-03-29 11:01:02.276819+02:00                  
item_count      | 8878                                               | 8878                                              
----------------+----------------------------------------------------+---------------------------------------------------
changed item    | file:///etc/cups/subscriptions.conf                                                                 
----------------+----------------------------------------------------+---------------------------------------------------
mtime           | 2016-03-29 09:37:34.623646+02:00                   | 2016-03-29 10:35:54.672467+02:00                  
hash            | b'0801aeb6c2eefec024778f68882277a2d5e239fec5e7c38b | b'f4ade9a35369d7aaadec9aa174f4cc42f4308828bbfd1ebb
                | 680e3850f82a99a3'                                  | 5b7f6cd4df681d0a'                                 
ctime           | 2016-03-29 09:37:34.675645+02:00                   | 2016-03-29 10:35:54.740465+02:00                  
----------------+----------------------------------------------------+---------------------------------------------------
diff of content | @@ -445,34 +445,34 @@                                                                               
                |  l 0                                                                                                
                | -ExpirationTime 1459240623                                                                          
                | +ExpirationTime 1459244123                                                                          
                |  Next                                                                                               
----------------+----------------------------------------------------+---------------------------------------------------
changed item    | file:///etc/cups/subscriptions.conf.O                                                               
----------------+----------------------------------------------------+---------------------------------------------------
mtime           | 2016-03-29 08:39:14.175013+02:00                   | 2016-03-29 09:37:34.623646+02:00                  
hash            | b'f80c4cd6b72b55ec36adba15b632ca856a1601d70646369d | b'0801aeb6c2eefec024778f68882277a2d5e239fec5e7c38b
                | c8ada6cf8211a6b6'                                  | 680e3850f82a99a3'                                 
ctime           | 2016-03-29 09:37:34.675645+02:00                   | 2016-03-29 10:35:54.740465+02:00                  
----------------+----------------------------------------------------+---------------------------------------------------
diff of content | @@ -445,34 +445,34 @@                                                                               
                |  l 0                                                                                                
                | -ExpirationTime 1459237123                                                                          
                | +ExpirationTime 1459240623                                                                          
                |  Next                                                                                               
----------------+----------------------------------------------------+---------------------------------------------------
changed item    | file:///etc/syschangemon/plugins.d/file.conf                                                        
----------------+----------------------------------------------------+---------------------------------------------------
mtime           | 2016-03-29 08:10:12.866575+02:00                   | 2016-03-29 10:06:18.740916+02:00                  
hash            | b'd30ad7c06ac5dd0deaca154914272a9c0c9c4fcacbf5f19f | b'4e96d6bbffc444a25e6be9286e664edcd9f875bf15de53e5
                | 1a87716d4aee37ef'                                  | 5cf875e851a00d1b'                                 
size            | 1266                                               | 1301                                              
ctime           | 2016-03-29 08:10:12.866575+02:00                   | 2016-03-29 10:06:18.740916+02:00                  
----------------+----------------------------------------------------+---------------------------------------------------
diff of content | @@ -1213,16 +1213,51 @@                                                                             
                |  s.conf*                                                                                            
                | + /etc/etc/cups/subscriptions.conf*                                                                 
                |   **.bak                                                                                            
================+====================================================+===================================================
relevant_wtmp   | 2016-03-29 07:40:00 CEST - 2016-03-29 11:00:01 CEST mcree :0@:0                                     
                | 2016-03-29 07:41:09 CEST - 2016-03-29 11:00:01 CEST mcree pts/1@:0                                  
                | 2016-03-29 08:06:49 CEST - 2016-03-29 11:00:01 CEST mcree pts/3@:0                                  
                | 2016-03-29 08:10:19 CEST - 2016-03-29 11:00:01 CEST mcree pts/8@:0                                  
                | 2016-03-29 09:09:16 CEST - 2016-03-29 11:00:01 CEST mcree pts/11@:0                                 
                | 2016-03-29 09:41:55 CEST - 2016-03-29 11:00:01 CEST mcree pts/13@:0                                 
                | 2016-03-29 10:06:01 CEST - 2016-03-29 11:00:01 CEST mcree pts/14@:0                                 
```
