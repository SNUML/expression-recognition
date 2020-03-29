from xml.etree import ElementTree
from copy import deepcopy
import numpy as np


def strip_namespace(tag):
    return tag.split('}')[-1]


class Symbol:
    def __init__(self, trace_group_id, truth, traces, MathML):
        self.trace_group_id = trace_group_id
        self.truth = truth
        self.traces = deepcopy(traces)  # list of lists
        self.MathML = MathML

    def points(self):
        return np.concatenate(self.traces)


class Expression:
    """Loads an inkml file of the dataset into a workable class containing all the data, ready for processing."""

    def __init__(self, inkml: str):
        self.root = ElementTree.fromstring(inkml)

        self.channels = {}

        self.UI = None
        self.age = None
        self.copyright = None
        self.gender = None
        self.hand = None
        self.writer = None
        self.truth = None

        self.MathML = None

        self.traces = {}  # contains traces as lists, indexed by trace_id

        self.root_trace_group_id = None
        self.root_trace_group_annotation = None
        self.trace_groups = {}  # contains {'truth', 'trace_ids', 'MathML'}, indexed by trace_group_id

        for child in self.root:
            if child.tag.endswith('traceFormat'):
                for channel in child:
                    self.channels[channel.attrib['name']] = channel.attrib['type']
            elif child.tag.endswith('annotation'):
                setattr(self, child.attrib['type'], child.text)
            elif child.tag.endswith('annotationXML'):
                self.MathML = ElementTree.tostring(child)
            elif child.tag.endswith('trace'):
                trace_id = child.attrib['id']
                trace = np.asarray([pair.split() for pair in child.text.split(',')], dtype=np.float32)
                self.traces[trace_id] = trace
            elif child.tag.endswith('traceGroup'):
                self.__initialize_trace_groups(child)

        assert self.UI is not None
        assert self.age is not None
        assert self.copyright is not None
        assert self.gender is not None
        assert self.hand is not None
        assert self.writer is not None
        assert self.truth is not None
        assert self.MathML is not None
        assert self.root_trace_group_id is not None
        assert self.root_trace_group_annotation is not None

    def __initialize_trace_groups(self, root_trace_group):
        # The root traceGroup
        for key in root_trace_group.attrib:
            if strip_namespace(key) == 'id':
                self.root_trace_group_id = root_trace_group.attrib[key]
                break
        # The child traceGroups, each representing a symbol
        for trace_group in root_trace_group:
            child_child_tag = strip_namespace(trace_group.tag)
            if child_child_tag == 'annotation':
                assert trace_group.attrib['type'] == 'truth'
                self.root_trace_group_annotation = trace_group.text
            else:
                assert child_child_tag == 'traceGroup'
                assert len(trace_group.attrib) == 1
                assert list(trace_group.attrib.keys())[0].endswith('id')

                trace_group_id = list(trace_group.attrib.values())[0]

                self.trace_groups[trace_group_id] = {'truth': None, 'trace_ids': [], 'MathML': None}

                for trace_group_property in trace_group:
                    tag = trace_group_property.tag

                    if tag.endswith('annotation'):
                        assert trace_group_property.attrib['type'] == 'truth'
                        self.trace_groups[trace_group_id]['truth'] = trace_group_property.text
                    elif tag.endswith('traceView'):
                        self.trace_groups[trace_group_id]['trace_ids'].append(
                            trace_group_property.attrib['traceDataRef'])
                    else:
                        assert tag.endswith('annotationXML')
                        self.trace_groups[trace_group_id]['MathML'] = trace_group_property.attrib['href']

    def symbols(self):
        symbols_list = []
        for trace_group_id in self.trace_groups:
            group = self.trace_groups[trace_group_id]
            truth, trace_ids, MathML = group['truth'], group['trace_ids'], group['MathML']
            traces = [self.traces[trace_id] for trace_id in trace_ids]
            symbols_list.append(Symbol(trace_group_id, truth, traces, MathML))
        return symbols_list


if __name__ == '__main__':
    with open('formulaire001-equation001.inkml', 'r') as f:
        inkml_str = f.read()
    test = Expression(inkml_str)
    symbols = test.symbols()
