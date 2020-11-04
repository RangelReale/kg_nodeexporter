import unittest

from kubragen import KubraGen
from kubragen.jsonpatch import FilterJSONPatches_Apply, ObjectFilter, FilterJSONPatch
from kubragen.provider import Provider_Generic

from kg_nodeexporter import NodeExporterBuilder, NodeExporterOptions


class TestBuilder(unittest.TestCase):
    def setUp(self):
        self.kg = KubraGen(provider=Provider_Generic())

    def test_empty(self):
        nodeexporter_config = NodeExporterBuilder(kubragen=self.kg)
        self.assertEqual(nodeexporter_config.object_name('daemonset'), 'node-exporter')

    def test_basedata(self):
        nodeexporter_config = NodeExporterBuilder(kubragen=self.kg, options=NodeExporterOptions({
            'namespace': 'myns',
            'basename': 'mynodeexporter',
        }))
        self.assertEqual(nodeexporter_config.object_name('daemonset'), 'mynodeexporter')

        FilterJSONPatches_Apply(items=nodeexporter_config.build(nodeexporter_config.BUILD_SERVICE), jsonpatches=[
            FilterJSONPatch(filters=ObjectFilter(names=[nodeexporter_config.BUILDITEM_DAEMONSET]), patches=[
                {'op': 'check', 'path': '/metadata/name', 'cmp': 'equals', 'value': 'mynodeexporter'},
                {'op': 'check', 'path': '/metadata/namespace', 'cmp': 'equals', 'value': 'myns'},
            ]),
        ])
