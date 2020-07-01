# -*- coding: utf-8 -*-

from collections import namedtuple

Node = namedtuple('Node', ['t', 'marks'])


def HGStat_(node, weights):
    """
    Static HG harmony function: sum marks within a node, 
    apply min0 ('minnow') nonlinearity
    """
    score = 0.0
    for (c, m) in node.marks:
        score += weights[c] * m
    harmony = score if score < 0.0 else 0.0
    return harmony


def HGStat(nodes, weights):
    """
    Apply static HG harmony function to a set of nodes, 
    tracking which ones are ill-formed (harmony < 0)
    """
    harmony_total = 0.0
    ill_nodes = []
    for node in nodes:
        harmony = HGStat_(node, weights)
        if harmony < 0.0:
            harmony_total += harmony
            ill_nodes.append(node)
    return (harmony_total, ill_nodes)


def OTStat_(node, ranks):
    """
    Static OT harmony function: a node is well-formed iff 
    every constraint that assigns it a negative mark is 
    dominated by some constraint that assigns it a 
    positive mark
    """
    c_max, score = None, 0.0
    for (c, m) in node.marks:
        if c_max is None or ranks[c] > ranks[c_max]:
            c_max, score = c, m
    harmony = -1.0 if score < 0.0 else 0.0
    return harmony


def OTStat(nodes, ranks):
    """
    Apply static OT harmony function to a set of nodes, 
    tracking which ones are ill-formed (harmony < 0)
    """
    harmony_total = 0.0
    ill_nodes = []
    for node in nodes:
        harmony = OTStat_(node, ranks)
        if harmony < 0.0:
            harmony_total += harmony
            ill_nodes.append(node)
    return (harmony_total, ill_nodes)
