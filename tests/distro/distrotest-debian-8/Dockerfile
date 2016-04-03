FROM debian:8
RUN apt-get -y update && \
    apt-get -y upgrade && \
    apt-get -y install curl python3 locales
RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && locale-gen
ENV LC_ALL=en_US.UTF-8
#RUN    curl -s https://packagecloud.io/install/repositories/mcree/syschangemon/script.deb.sh | sudo bash && \
#    sudo apt-get -y install syschangemon
ADD syschangemon*.deb /tmp
RUN dpkg -i /tmp/syschangemon*.deb
ENTRYPOINT syschangemon run && \
    syschangemon collect && \
    syschangemon diff && \
    syschangemon print-report


