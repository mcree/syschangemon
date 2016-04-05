#!/bin/bash
#
# this script is not used by default - it is just a sample to install build dependencies
#
apt-get install -y curl build-essential rpm
rm -rf ~/.gnupg
gpg --keyserver hkp://keys.gnupg.net --recv-keys 409B6B1796C275462A1703113804BB82D39DC0E3
curl -L https://get.rvm.io | bash -s stable
source /etc/profile.d/rvm.sh
rvm install ruby
rvm use ruby --default
rvm rubygems current
gem install fpm
make
