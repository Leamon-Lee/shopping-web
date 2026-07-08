FROM quay.io/centos/centos:7

ARG HADOOP_VERSION=3.3.6
ARG CENTOS_VAULT_MIRROR=https://mirror.iscas.ac.cn/centos-vault/7.9.2009
ARG HADOOP_DIST_MIRROR=https://repo.huaweicloud.com/apache/hadoop/common
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ARG PYTHON_PACKAGES=

ENV HADOOP_HOME=/opt/hadoop \
    HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop \
    JAVA_HOME=/usr/lib/jvm/jre-1.8.0-openjdk \
    PATH=/opt/hadoop/bin:/opt/hadoop/sbin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    PYTHONUNBUFFERED=1

RUN set -eux; \
    rm -f /etc/yum.repos.d/*.repo; \
    printf '[base]\nname=CentOS 7.9.2009 - Base\nbaseurl=%s/os/$basearch/\nenabled=1\ngpgcheck=0\n\n[updates]\nname=CentOS 7.9.2009 - Updates\nbaseurl=%s/updates/$basearch/\nenabled=1\ngpgcheck=0\n\n[extras]\nname=CentOS 7.9.2009 - Extras\nbaseurl=%s/extras/$basearch/\nenabled=1\ngpgcheck=0\n' "${CENTOS_VAULT_MIRROR}" "${CENTOS_VAULT_MIRROR}" "${CENTOS_VAULT_MIRROR}" > /etc/yum.repos.d/centos-vault-7.9.2009.repo; \
    yum clean all; \
    yum makecache fast; \
    yum install -y \
        java-1.8.0-openjdk-headless \
        ca-certificates \
        python3 \
        python3-pip \
        tar \
        gzip \
        hostname \
        procps-ng \
        which \
    && update-ca-trust force-enable \
    && update-ca-trust extract \
    && yum clean all

RUN set -eux; \
    curl -fL --retry 5 --retry-delay 5 --connect-timeout 20 \
        "${HADOOP_DIST_MIRROR}/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz" \
        -o /tmp/hadoop.tar.gz; \
    tar -tzf /tmp/hadoop.tar.gz >/dev/null; \
    tar -xzf /tmp/hadoop.tar.gz -C /opt; \
    mv "/opt/hadoop-${HADOOP_VERSION}" "${HADOOP_HOME}"; \
    rm -f /tmp/hadoop.tar.gz; \
    mkdir -p /hadoop/dfs/name /hadoop/dfs/data /hadoop/yarn/local /hadoop/yarn/logs /app

RUN set -eux; \
    if [ -n "${PYTHON_PACKAGES}" ]; then \
        pip3 install --no-cache-dir --timeout 120 --retries 10 -i "${PIP_INDEX_URL}" ${PYTHON_PACKAGES}; \
    else \
        echo "No extra Python packages requested."; \
    fi

COPY docker/hadoop/config/ ${HADOOP_CONF_DIR}/
COPY docker/hadoop/scripts/entrypoint.sh /usr/local/bin/hadoop-entrypoint

RUN chmod +x /usr/local/bin/hadoop-entrypoint

WORKDIR /app

EXPOSE 9000 9870 9864 8088 8042 19888

ENTRYPOINT ["hadoop-entrypoint"]
