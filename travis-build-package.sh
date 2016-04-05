#!/bin/bash

set -e

[ "$TRAVIS_PYTHON_VERSION" != "3.4" ] && exit

#apt-get -y install rpm
#make
package_cloud push mcree/syschangemon/debian/wheezy *.deb
package_cloud push mcree/syschangemon/el/6 *.rpm
