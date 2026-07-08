#!/usr/bin/env bash
set -euo pipefail

mkdir -p /hadoop/tmp /hadoop/dfs/name /hadoop/dfs/data /hadoop/yarn/local /hadoop/yarn/logs

if [[ "${HADOOP_ROLE:-worker}" == "master" ]]; then
  if [[ ! -f /hadoop/dfs/name/current/VERSION ]]; then
    hdfs namenode -format -force -nonInteractive
  fi

  hdfs --daemon start namenode
  yarn --daemon start resourcemanager
  mapred --daemon start historyserver
else
  until hdfs dfsadmin -fs hdfs://master:9000 -report >/dev/null 2>&1; do
    sleep 2
  done

  hdfs --daemon start datanode
  yarn --daemon start nodemanager
fi

tail -F "${HADOOP_HOME}"/logs/*.log
