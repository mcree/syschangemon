#!/usr/bin/make -f
# makefile for syschangemon

DEST = build
PROGDIR = "$(DEST)"/usr/share/syschangemon
CONFDIR = "$(DEST)"/etc/syschangemon
CRONDIR = "$(DEST)"/etc/cron.d
DOCDIR = "$(DEST)"/usr/share/doc/syschangemon
LOGDIR = "$(DEST)"/var/log/syschangemon
DATADIR = "$(DEST)"/var/lib/syschangemon/storage
TEMPLATEDIR = "$(DEST)"/var/lib/syschangemon/templates
SBINDIR = "$(DEST)"/usr/sbin
STAMPS = stamp-dest stamp-pip stamp-progdir stamp-confdir stamp-crondir stamp-docdir stamp-logdir stamp-datadir stamp-templatedir stamp-sbindir stamp-deb stamp-rpm

all: $(STAMPS)

stamp-dest:
	install -d "$(DEST)"
	touch stamp-dest

stamp-pip:
	install -d "$(PROGDIR)"
	pip3 install --target "$(PROGDIR)" -r requirements.txt
	touch stamp-pip

stamp-progdir: stamp-pip
	install -d "$(PROGDIR)"
	cp -r syschangemon "$(PROGDIR)"
	chmod u=rwX,go=rx "$(PROGDIR)/syschangemon"
	install -m 0755 -t "$(PROGDIR)" bin/*
	touch stamp-progdir

stamp-confdir:
	install -d "$(CONFDIR)"
	install -m u=rw,go=r config/*.conf -t "$(CONFDIR)"
	install -d "$(CONFDIR)/plugins.d"
	install -m u=rw,go=r config/plugins.d/* "$(CONFDIR)/plugins.d"
	touch stamp-confdir

stamp-crondir:
	install -d "$(CRONDIR)"
	install -m u=rw,go=r cron/* "$(CRONDIR)"
	touch stamp-crondir

stamp-docdir:
	install -d "$(DOCDIR)"
	install README.md "$(DOCDIR)"
	install LICENSE "$(DOCDIR)"
	touch stamp-docdir

stamp-logdir:
	install -d "$(LOGDIR)"
	touch stamp-logdir

stamp-datadir:
	install -d "$(DATADIR)"
	touch stamp-datadir

stamp-templatedir:
	install -d "$(TEMPLATEDIR)"
	install syschangemon/cli/templates/*.html "$(TEMPLATEDIR)"
	touch stamp-templatedir

stamp-sbindir:
	mkdir -p "$(SBINDIR)"
	ln -s ../share/syschangemon/run.sh "$(SBINDIR)/syschangemon"
	touch stamp-sbindir

ifeq ($(origin TRAVIS_TAG), undefined)
VERSION = 1.0+snapshot
else
VERSION = ${TRAVIS_TAG}+release
endif

ITERATION = `date +%Y%m%d%H%M%S`

DESCRIPTION= \
Periodically collects system configuration (eg. conffiles in /etc, binary files in /sbin, etc.)\n\
for changes, it can even run external commands and store their stdout and stderr for change monitoring.\n\
\n\
This can be useful as a HIDS (host based intrusion detection system) as well as in a shared working environment\n\
where several users have administrative access to system configuration.\n\
\n\
If changes are found it sends text and html reports to predefined email addresses. It also includes relevant wtmp\n\
information in the reports.\n\
\n\
Similar software: tripwire, samhain, fcheck, changetrack, systraq\n

stamp-deb:
	fpm -s dir -t deb -C "$(DEST)" \
	    --package syschangemon_$(VERSION)-$(ITERATION).deb \
	    --name syschangemon \
	    --version $(VERSION) \
	    --iteration $(ITERATION) \
	    --description '$(DESCRIPTION)' \
	    --license GPLv3+ \
	    --vendor syschangemon \
	    --category Administration \
	    --depends "python3.2|python3.3|python3.4|python3.5" \
	    --config-files etc \
	    --directories usr/share/syschangemon \
	    --directories var/lib/syschangemon \
	    --directories var/log/syschangemon \
	    --architecture all \
	    --maintainer "Erno Rigo <erno@rigo.info>" \
	    --url https://github.com/mcree/syschangemon
	touch stamp-deb

stamp-rpm:
	fpm -s dir -t rpm -C "$(DEST)" \
	    --package syschangemon_$(VERSION)-$(ITERATION).rpm \
	    --name syschangemon \
	    --version $(VERSION) \
	    --iteration $(ITERATION) \
	    --description '$(DESCRIPTION)' \
	    --license GPLv3+ \
	    --vendor syschangemon \
	    --category Administration \
	    --config-files etc \
	    --directories usr/share/syschangemon \
	    --directories var/lib/syschangemon \
	    --directories var/log/syschangemon \
	    --architecture all \
	    --maintainer "Erno Rigo <erno@rigo.info>" \
	    --url https://github.com/mcree/syschangemon
	touch stamp-rpm

clean:
	rm -rf "$(DEST)"
	rm -f $(STAMPS)
