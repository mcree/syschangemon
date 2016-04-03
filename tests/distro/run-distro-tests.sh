#!/bin/bash

set -e

function prepare_test() {
    pushd "$1"
    cp -fv ../../../../syschangemon*.{deb,rpm} .
    sudo docker build -t "$1" .
    popd
}

function run_test() {
    pushd "$1"
    sudo docker run "$1"
    popd
}

function cleanup_test() {
    pushd "$1"
    rm -f syschangemon*.{deb,rpm}
    popd
}

function build_package {
    pushd ../..
    dpkg-buildpackage -us -uc
    cd ..
    sudo alien -r syschangemon*.deb
    popd
}

log=distro-tests.log
echo "saving log in $log"
> $log

test ! -f ../../../syschangemon*.deb && build_package 2>&1 >>$log

DISTS="
distrotest-centos-6
distrotest-centos-7
distrotest-debian-7
distrotest-debian-8
distrotest-ubuntu-12.04
distrotest-ubuntu-14.04
distrotest-ubuntu-16.04
"

for distro in $DISTS; do
    echo -n "testing in $distro ... "
    prepare_test $distro 2>&1 >>$log && run_test $distro 2>&1 >>$log
    cleanup_test $distro 2>&1 >>$log
    echo "OK"
done

