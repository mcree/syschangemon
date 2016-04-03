FROM centos:6
RUN yum -y install https://centos6.iuscommunity.org/ius-release.rpm && yum -y install curl python34u
#RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && locale-gen
ENV LC_ALL=en_US.UTF-8
#RUN    curl -s https://packagecloud.io/install/repositories/mcree/syschangemon/script.deb.sh | sudo bash && \
#    sudo apt-get -y install syschangemon
ADD syschangemon*.rpm /tmp
RUN rpm --force -i /tmp/syschangemon*.rpm
RUN touch /var/log/wtmp
ENTRYPOINT syschangemon run && \
    syschangemon collect && \
    syschangemon diff && \
    syschangemon print-report


