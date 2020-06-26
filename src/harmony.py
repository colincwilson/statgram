#!/usr/bin/env python
# -*- coding: utf-8 -*-

def harmony_HG(nodes, weight):
    """
    Static HG harmony function: sum marks within each node, 
    apply min0 ('minnow') nonlinearity
    """
    h_total, nodes_ill = 0.0, []
    for n in nodes:
        # Reduce (sum) weighted marks
        h_n = 0.0
        for (c,m) in n.marks:
            h_n = h_n + (weight[c] * m)
        # Apply min0 non-linearity
        h_n = h_n if h_n <= 0.0 else 0.0
        # Accumulate total harmony
        h_total = h_total + h_n
        # Track ill-formed nodes
        if h_n < 0.0:
            nodes_bad.append(n)
    return (h_total, nodes_ill)


def harmony_OT(nodes, rank):
    """Static OT harmony function: a node is well-formed iff 
    every constraint that assigns it a negative mark is 
    dominated by some constraint that assigns it a positive mark
    """
    h_total, nodes_ill = 0.0, []
    for n in nodes:
        # Reduce ranked marks
        c_dom, h_n = None, 0.0
        for (c,m) in n.marks:
            if (c_dom is None) \
                or rank[c] > rank[c_dom]:
                c_dom, h_n = c, m
        # Accumulate total harmony, count 
        # and track ill-formed nodes
        if h_n < 0.0:
            h_total = h_total + 1.0
            nodes_ill.append(n)
    return (h_total, nodes_ill)
