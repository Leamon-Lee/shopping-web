# Hadoop Docker Cluster

This setup runs three CentOS containers:

- `master`: HDFS NameNode, YARN ResourceManager, MapReduce JobHistoryServer
- `slaver1`: HDFS DataNode, YARN NodeManager
- `slaver2`: HDFS DataNode, YARN NodeManager

The base image is `quay.io/centos/centos:7`, and package downloads use China-friendly mirrors by default:

- CentOS 7.9.2009 packages: ISCAS CentOS Vault
- PyPI packages: Tsinghua Tuna
- Hadoop tarball: Huawei Cloud Apache mirror

The Dockerfile uses the CentOS Vault yum repository path under `https://mirror.iscas.ac.cn/centos-vault/7.9.2009`. The `isos/x86_64` path contains installer images and is not a yum repository.

The Hadoop image includes Python 3. Extra Python packages are optional because PyPI network access can make Docker builds flaky.

## Start

```powershell
docker compose -f docker-compose.hadoop.yml up -d --build
```

To switch the OS mirror, edit `CENTOS_VAULT_MIRROR` in `docker-compose.hadoop.yml`:

```yaml
CENTOS_VAULT_MIRROR: https://mirror.iscas.ac.cn/centos-vault/7.9.2009
```

To switch the Hadoop download mirror, edit `HADOOP_DIST_MIRROR`:

```yaml
HADOOP_DIST_MIRROR: https://mirrors.tuna.tsinghua.edu.cn/apache/hadoop/common
```

To install Python data packages during build, edit `PYTHON_PACKAGES`:

```yaml
PYTHON_PACKAGES: hdfs
```

For a Python backend, it is usually better to install client packages such as `hdfs`, `pandas`, or `pyarrow` in the backend service image or virtual environment, then connect to `hdfs://master:9000`.

## Useful URLs

- HDFS NameNode: http://localhost:9870
- YARN ResourceManager: http://localhost:8088
- JobHistory Server: http://localhost:19888

## Python Backend Access

Use HDFS from containers with:

```text
hdfs://master:9000
```

From the host, the NameNode RPC port is published as `localhost:9000`.

## Checks

```powershell
docker exec master hdfs dfsadmin -report
docker exec master yarn node -list
docker exec master hdfs dfs -mkdir -p /apps/online-shopping
docker exec master hdfs dfs -put /app/src /apps/online-shopping/src
```
