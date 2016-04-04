#!/bin/bash

set -e

function prepare_test() {
    pushd "$1"
    cp -fv ../../../syschangemon*.{deb,rpm} .
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
#    make clean
#    rm -f syschangemon*.{deb,rpm}
    make
    popd
}

log=distro-tests.log
echo "saving log in $log"
> $log

#test ! -f ../../../syschangemon*.deb && build_package 2>&1 >>$log

echo -n "Building distribution packages ... "
build_package 2>&1 >>$log
echo "OK"

DISTS="
distrotest-centos-6
distrotest-centos-7
distrotest-debian-7
distrotest-debian-8
distrotest-ubuntu-12.04
distrotest-ubuntu-14.04
distrotest-ubuntu-16.04
distrotest-fedora-22
distrotest-fedora-23
"

for distro in $DISTS; do
    echo -n "testing in $distro ... "
    prepare_test $distro 2>&1 >>$log && run_test $distro 2>&1 >>$log
    cleanup_test $distro 2>&1 >>$log
    echo "OK"
done

