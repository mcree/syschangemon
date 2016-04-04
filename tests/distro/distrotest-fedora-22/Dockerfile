FROM fedora:22
RUN dnf -y install python3
#RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && locale-gen
ENV LC_ALL=en_US.UTF-8
#RUN    curl -s https://packagecloud.io/install/repositories/mcree/syschangemon/script.deb.sh | sudo bash && \
#    sudo apt-get -y install syschangemon
ADD syschangemon*.rpm /tmp
RUN rpm -i /tmp/syschangemon*.rpm
RUN touch /var/log/wtmp
ENTRYPOINT syschangemon run && \
    syschangemon collect && \
    syschangemon diff && \
    syschangemon print-report


