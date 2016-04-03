FROM ubuntu:12.04
RUN apt-get -y update && \
    apt-get -y upgrade && \
    apt-get -y install curl python3
RUN locale-gen en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
#RUN    curl -s https://packagecloud.io/install/repositories/mcree/syschangemon/script.deb.sh | sudo bash && \
#    sudo apt-get -y install syschangemon
ADD syschangemon*.deb /tmp
RUN dpkg -i /tmp/syschangemon*.deb
ENTRYPOINT syschangemon run && \
    syschangemon collect && \
    syschangemon diff && \
    syschangemon print-report


