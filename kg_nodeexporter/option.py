from typing import Mapping

from kubragen.option import OptionDef
from kubragen.options import Options


class NodeExporterOptions(Options):
    """
    Options for the Node Exporter builder.

    .. list-table::
        :header-rows: 1

        * - option
          - description
          - allowed types
          - default value
        * - basename
          - object names prefix
          - str
          - ```node-exporter```
        * - namespace
          - namespace
          - str
          - ```default```
        * - config |rarr| prometheus_annotation
          - add prometheus annotations
          - bool
          - ```False```
        * - container |rarr| node-exporter
          - node exporter container image
          - str
          - ```prom/node-exporter:<version>```
        * - kubernetes |rarr| resources |rarr| daemonset
          - Kubernetes DaemonSet resources
          - Mapping
          -
    """
    def define_options(self):
        """
        Declare the options for the Node Exporter builder.

        :return: The supported options
        """
        return {
            'basename': OptionDef(required=True, default_value='node-exporter', allowed_types=[str]),
            'namespace': OptionDef(required=True, default_value='default', allowed_types=[str]),
            'config': {
                'prometheus_annotation': OptionDef(required=True, default_value=False, allowed_types=[bool]),
            },
            'container': {
                'node-exporter': OptionDef(required=True, default_value='prom/node-exporter:v1.0.1', allowed_types=[str]),
            },
            'kubernetes': {
                'resources': {
                    'daemonset': OptionDef(allowed_types=[Mapping]),
                }
            },
        }
