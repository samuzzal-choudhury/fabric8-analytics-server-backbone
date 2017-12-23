FROM registry.centos.org/centos/centos:7

RUN useradd -d /coreapi coreapi
# python3-pycurl is needed for Amazon SQS (boto lib), we need CentOS' rpm - installing it from pip results in NSS errors
RUN yum install -y epel-release &&\
    yum install -y gcc patch git python34-pip python34-requests httpd httpd-devel python34-devel postgresql-devel redhat-rpm-config libxml2-devel libxslt-devel python34-pycurl &&\
    yum clean all

RUN mkdir -p /coreapi
COPY ./requirements.txt /coreapi
RUN pushd /coreapi && \
    pip3 install -r requirements.txt && \
    rm requirements.txt && \
    popd

COPY ./coreapi-httpd.conf /etc/httpd/conf.d/

ENTRYPOINT ["/usr/bin/coreapi-server.sh"]

COPY ./ /coreapi
RUN pushd /coreapi && \
    pip3 install . && \
    popd

COPY .git/ /tmp/.git
# date and hash of last commit
RUN cd /tmp/.git &&\
    git show -s --format="COMMITTED_AT=%ai%nCOMMIT_HASH=%h%n" HEAD | tee /etc/coreapi-release &&\
    rm -rf /tmp/.git/
