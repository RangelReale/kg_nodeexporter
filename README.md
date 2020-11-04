# KubraGen Builder: Node Exporter

[![PyPI version](https://img.shields.io/pypi/v/kg_nodeexporter.svg)](https://pypi.python.org/pypi/kg_nodeexporter/)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/kg_nodeexporter.svg)](https://pypi.python.org/pypi/kg_nodeexporter/)

kg_nodeexporter is a builder for [KubraGen](https://github.com/RangelReale/kubragen) that deploys 
a [Node Exporter](https://github.com/prometheus/node_exporter) service in Kubernetes.

[KubraGen](https://github.com/RangelReale/kubragen) is a Kubernetes YAML generator library that makes it possible to generate
configurations using the full power of the Python programming language.

* Website: https://github.com/RangelReale/kg_nodeexporter
* Repository: https://github.com/RangelReale/kg_nodeexporter.git
* Documentation: https://kg_nodeexporter.readthedocs.org/
* PyPI: https://pypi.python.org/pypi/kg_nodeexporter

## Example

```python
from kubragen import KubraGen
from kubragen.consts import PROVIDER_GOOGLE, PROVIDERSVC_GOOGLE_GKE
from kubragen.object import Object
from kubragen.option import OptionRoot
from kubragen.options import Options
from kubragen.output import OutputProject, OD_FileTemplate, OutputFile_ShellScript, OutputFile_Kubernetes, \
    OutputDriver_Print
from kubragen.provider import Provider

from kg_nodeexporter import NodeExporterBuilder, NodeExporterOptions

kg = KubraGen(provider=Provider(PROVIDER_GOOGLE, PROVIDERSVC_GOOGLE_GKE), options=Options({
    'namespaces': {
        'mon': 'app-monitoring',
    },
}))

out = OutputProject(kg)

shell_script = OutputFile_ShellScript('create_gke.sh')
out.append(shell_script)

shell_script.append('set -e')

#
# OUTPUTFILE: app-namespace.yaml
#
file = OutputFile_Kubernetes('app-namespace.yaml')

file.append([
    Object({
        'apiVersion': 'v1',
        'kind': 'Namespace',
        'metadata': {
            'name': 'app-monitoring',
        },
    }, name='ns-monitoring', source='app', instance='app')
])

out.append(file)
shell_script.append(OD_FileTemplate(f'kubectl apply -f ${{FILE_{file.fileid}}}'))

shell_script.append(f'kubectl config set-context --current --namespace=app-monitoring')

#
# SETUP: node-exporter
#
nodeexporter_config = NodeExporterBuilder(kubragen=kg, options=NodeExporterOptions({
    'namespace': OptionRoot('namespaces.mon'),
    'basename': 'mynodeexporter',
    'config': {
        'prometheus_annotation': True,
    },
    'kubernetes': {
        'resources': {
            'daemonset': {
                'requests': {
                    'cpu': '150m',
                    'memory': '300Mi'
                },
                'limits': {
                    'cpu': '300m',
                    'memory': '450Mi'
                },
            },
        },
    }
}))

nodeexporter_config.ensure_build_names(nodeexporter_config.BUILD_SERVICE)

#
# OUTPUTFILE: node-exporter.yaml
#
file = OutputFile_Kubernetes('node-exporter.yaml')
out.append(file)

file.append(nodeexporter_config.build(nodeexporter_config.BUILD_SERVICE))

shell_script.append(OD_FileTemplate(f'kubectl apply -f ${{FILE_{file.fileid}}}'))

#
# Write files
#
out.output(OutputDriver_Print())
# out.output(OutputDriver_Directory('/tmp/build-gke'))
```

Output:

```text
****** BEGIN FILE: 001-app-namespace.yaml ********
apiVersion: v1
kind: Namespace
metadata:
  name: app-monitoring

****** END FILE: 001-app-namespace.yaml ********
****** BEGIN FILE: 002-node-exporter.yaml ********
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: mynodeexporter
  namespace: app-monitoring
  labels:
    app: mynodeexporter
spec:
  selector:
    matchLabels:
      app: mynodeexporter
  template:
    metadata:
      labels:
        app: mynodeexporter
      annotations:
        prometheus.io/scrape: 'true'
        prometheus.io/path: '/metrics'
        prometheus.io/port: '9100'
    spec:
      hostPID: true
      hostIPC: true
      hostNetwork: true
      containers:
      - name: node-exporter
        ports:
        - containerPort: 9100
          protocol: TCP
        securityContext:
          privileged: true
        image: prom/node-exporter:v1.0.1
        args: [--path.procfs, /host/proc, --path.sysfs, /host/sys, --collector.filesystem.ignored-mount-points,
          '"^/(sys|proc|dev|host|etc)($|/)"']
        volumeMounts:
        - name: dev
          mountPath: /host/dev
        - name: proc
          mountPath: /host/proc
        - name: sys
          mountPath: /host/sys
        - name: rootfs
          mountPath: /rootfs
        resources:
          requests:
            cpu: 150m
            memory: 300Mi
          limits:
            cpu: 300m
            memory: 450Mi
      volumes:
      - name: proc
        hostPath:
          path: /proc
      - name: dev
        hostPath:
          path: /dev
      - name: sys
        hostPath:
          path: /sys
      - name: rootfs
        hostPath:
          path: /

****** END FILE: 002-node-exporter.yaml ********
****** BEGIN FILE: create_gke.sh ********
#!/bin/bash

set -e
kubectl apply -f 001-app-namespace.yaml
kubectl config set-context --current --namespace=app-monitoring
kubectl apply -f 002-node-exporter.yaml

****** END FILE: create_gke.sh ********
```

### Credits

Based on

[Kubernetes: monitoring with Prometheus — exporters, a Service Discovery, and its roles](https://itnext.io/kubernetes-monitoring-with-prometheus-exporters-a-service-discovery-and-its-roles-ce63752e5a1)

## Author

Rangel Reale (rangelspam@gmail.com)
