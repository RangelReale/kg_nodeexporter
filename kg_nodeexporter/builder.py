from typing import Optional, Sequence

from kubragen import KubraGen
from kubragen.builder import Builder
from kubragen.data import ValueData
from kubragen.exception import InvalidNameError
from kubragen.helper import QuotedStr
from kubragen.object import ObjectItem, Object
from kubragen.types import TBuild, TBuildItem

from .option import NodeExporterOptions


class NodeExporterBuilder(Builder):
    """
    Node Exporter builder.

    Based on `Kubernetes: monitoring with Prometheus — exporters, a Service Discovery, and its roles <https://itnext.io/kubernetes-monitoring-with-prometheus-exporters-a-service-discovery-and-its-roles-ce63752e5a1>`_.

    .. list-table::
        :header-rows: 1

        * - build
          - description
        * - BUILD_SERVICE
          - creates DaemonSet

    .. list-table::
        :header-rows: 1

        * - build item
          - description
        * - BUILDITEM_DAEMONSET
          - DaemonSet

    .. list-table::
        :header-rows: 1

        * - object name
          - description
          - default value
        * - daemonset
          - DaemonSet
          - ```<basename>```
        * - pod-label-all
          - label *app* to be used by selection
          - ```<basename>```
    """
    options: NodeExporterOptions
    _namespace: str

    SOURCE_NAME = 'kg_nodeexporter'

    BUILD_SERVICE = TBuild('service')

    BUILDITEM_DAEMONSET = TBuildItem('daemonset')

    def __init__(self, kubragen: KubraGen, options: Optional[NodeExporterOptions] = None):
        super().__init__(kubragen)
        if options is None:
            options = NodeExporterOptions()
        self.options = options

        self.object_names_init({
            'daemonset': self.basename(),
            'pod-label-app': self.basename(),
        })
        self._namespace = self.option_get('namespace')

    def option_get(self, name: str):
        return self.kubragen.option_root_get(self.options, name)

    def basename(self, suffix: str = ''):
        return '{}{}'.format(self.option_get('basename'), suffix)

    def namespace(self):
        return self._namespace

    def build_names(self) -> Sequence[TBuild]:
        return [self.BUILD_SERVICE]

    def build_names_required(self) -> Sequence[TBuild]:
        return [self.BUILD_SERVICE]

    def builditem_names(self) -> Sequence[TBuildItem]:
        return [
            self.BUILDITEM_DAEMONSET,
        ]

    def internal_build(self, buildname: TBuild) -> Sequence[ObjectItem]:
        if buildname == self.BUILD_SERVICE:
            return self.internal_build_service()
        else:
            raise InvalidNameError('Invalid build name: "{}"'.format(buildname))

    def internal_build_service(self) -> Sequence[ObjectItem]:
        ret = [Object({
            'apiVersion': 'apps/v1',
            'kind': 'DaemonSet',
            'metadata': {
                'name': self.object_name('daemonset'),
                'namespace': self.namespace(),
                'labels': {
                    'app': self.object_name('pod-label-app'),
                },
            },
            'spec': {
                'selector': {
                    'matchLabels': {
                        'app': self.object_name('pod-label-app'),
                    }
                },
                'template': {
                    'metadata': {
                        'labels': {
                            'app': self.object_name('pod-label-app'),
                        },
                        'annotations': ValueData({
                            'prometheus.io/scrape': QuotedStr('true'),
                            'prometheus.io/path': QuotedStr('/metrics'),
                            'prometheus.io/port': QuotedStr('9100'),
                        }, enabled=self.option_get('config.prometheus_annotation') is not False),
                    },
                    'spec': {
                        'hostPID': True,
                        'hostIPC': True,
                        'hostNetwork': True,
                        'containers': [{
                            'name': 'node-exporter',
                            'ports': [{
                                'containerPort': 9100,
                                'protocol': 'TCP'
                            }],
                            'securityContext': {
                                'privileged': True
                            },
                            'image': self.option_get('container.node-exporter'),
                            'args': [
                                '--path.procfs',
                                '/host/proc',
                                '--path.sysfs',
                                '/host/sys',
                                '--collector.filesystem.ignored-mount-points',
                                '"^/(sys|proc|dev|host|etc)($|/)"'
                            ],
                            'volumeMounts': [{
                                'name': 'dev',
                                'mountPath': '/host/dev'
                            },
                            {
                                'name': 'proc',
                                'mountPath': '/host/proc'
                            },
                            {
                                'name': 'sys',
                                'mountPath': '/host/sys'
                            },
                            {
                                'name': 'rootfs',
                                'mountPath': '/rootfs'
                            }],
                            'resources': ValueData(value=self.option_get('kubernetes.resources.daemonset'),
                                                   disabled_if_none=True),
                        }],
                        'volumes': [{
                            'name': 'proc',
                            'hostPath': {'path': '/proc'}
                        },
                        {
                            'name': 'dev',
                            'hostPath': {'path': '/dev'}
                        },
                        {
                            'name': 'sys',
                            'hostPath': {'path': '/sys'}
                        },
                        {
                            'name': 'rootfs',
                            'hostPath': {'path': '/'}
                        }]
                    }
                }
            }
        }, name=self.BUILDITEM_DAEMONSET, source=self.SOURCE_NAME, instance=self.basename())]
        return ret
