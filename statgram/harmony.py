# -*- coding: utf-8 -*-

from collections import namedtuple


# Mark with value v assigned by constraint c, 
# optionally specifying subnode to which mark is assigned 
# (default subnode is the 'root' denoted with '•')
Mark = namedtuple('Mark', ['c', 'v', 'subnode'],
                    defaults = [None, 0, '•'])

# Node n and mapping from attributes (subnodes) to marks
MarkedNode = namedtuple('MarkedNode', ['n', 'marks'])


def Eval(M, Con, fignore=None):
    """
    Evaluate each node of structure M with constraints in Con.
    (Nodes for which fignore evaluates to true are not marked.)
    """
    markup = []
    ignore = (fignore is not None)
    for node in M:
        if ignore and fignore(node):
            continue
        marks = dict()
        for constraint in Con:
            mark = constraint(node)
            if mark.v == 0:
                continue
            subnode = mark.subnode
            if not subnode in marks:
                marks[subnode] = set()
            marks[subnode].add(mark)
        markup.append(MarkedNode(node, marks))
    return markup


def HGStat(marks, weights):
    """
    Static HG harmony function: sum marks within a (sub)node, 
    apply min0 ("minnow") threshold non-linearity
    """
    score = 0.0
    for (c, v, _) in marks:
        score += weights[c] * v
    harmony = score if score < 0.0 else 0.0
    return harmony


def OTStat(marks, ranks):
    """
    Static OT harmony function: a (sub)node is well-formed iff 
    every constraint that assigns it a negative mark is 
    dominated by some constraint that assigns it a 
    positive mark
    """
    c_max, v_max = None, 0.0
    for (c, v, _) in marks:
        if c_max is None or ranks[c] > ranks[c_max]:
            c_max, v_max = c, v
    harmony = -1.0 if v_max < 0.0 else 0.0
    return harmony


def Stat1(node, weights, fstat=HGStat):
    """
    Apply static HG or OT harmony function to a single node.
    (For OTStat pass in ranks in place of weights.)
    """
    harmony_total = 0.0
    for (subnode, marks) in node.marks.items():
        harmony = fstat(marks, weights)
        harmony_total += harmony
    return harmony_total


def Stat(markup, weights, fstat=HGStat):
    """
    Apply static HG or OT harmony function to each marked node of 
    structure M, tracking which nodes are ill-formed (harmony < 0).
    (For OTStat pass in ranks instead of weights.)
    """
    harmony_total = 0.0
    ill_nodes = []
    for node in markup:
        harmony = Stat1(node, weights, fstat)
        if harmony < 0.0:
            harmony_total += harmony
            ill_nodes.append(node)
    return (harmony_total, ill_nodes)
