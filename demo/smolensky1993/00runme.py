import re, sys
import numpy as np
from nltk import CFG
from nltk.tree import ParentedTree
from nltk.parse import RecursiveDescentParser

sys.path.append('../..')
from statgram.harmony import Mark, MarkedNode, Eval, \
    HGStat, OTStat, Stat

# Grammar G0 in Harmonic Normal Form (HNF)
#   A[0] -> B C
#   A[1] -> D E
#   F[0] -> B E

# # # # # # # # # #
# Gen
root = 'S'
non_terminals = ['A0', 'A1', 'F0', 'B', 'C', 'D', 'E']
gen_rules = [root + ' -> ' + y for y in non_terminals]
gen_rules += [
    x + ' -> ' + y + ' ' + z
    for x in non_terminals
    for y in non_terminals
    for z in non_terminals
]
gen_rules += [x + ' -> ' + x.lower() for x in non_terminals]
gen_rulestr = '\n'.join(gen_rules)
Gen = CFG.fromstring(gen_rulestr)
print(f'# of productions in grammar: {len(Gen.productions())}')

# # # # # # # # # #
# Grammar
rules = [
    'S -> A0', 'S -> A1', 'S -> F0', 'A0 -> B C', 'A1 -> D E', 'F0 -> B E',
    'B -> b', 'C -> c', 'D -> d', 'E -> e'
]
legal_parent = {x: set() for x in [root] + non_terminals}
legal_daught0 = {x: set() for x in [root] + non_terminals}
legal_daught1 = {x: set() for x in [root] + non_terminals}
for rule in rules:
    syms = rule.split(' ')
    parent = syms[0]
    daught0 = syms[2]
    daught1 = syms[3] if len(syms) > 3 else None
    legal_daught0[parent].add(daught0)
    if daught0 in non_terminals:
        legal_parent[daught0].add(parent)
    if daught1 is not None:
        legal_daught1[parent].add(daught1)
        legal_parent[daught1].add(parent)


# # # # # # # #
# Con
# negative constraints
def need_parent(x):
    xlab = x.label()
    v = -1 if xlab in non_terminals else 0
    return Mark('need_parent', v)


def need_daught0(x):
    xlab = x.label()
    v = -1 if xlab in non_terminals else 0
    return Mark('need_daught0', v)


def need_daught1(x):
    xlab = x.label()
    v = -1 if xlab in non_terminals \
        and re.search('[0-9]', xlab) \
            else 0
    return Mark('need_daught1', v)


# positive constraints
def good_parent(x):
    v = 0
    xlab = x.label()
    if xlab in non_terminals \
      and x.parent() is not None \
      and x.parent().label() in legal_parent[xlab]:
        v = +1
    return Mark('good_parent', v)


def good_daught0(x):
    v = 0
    xlab = x.label()
    if xlab in non_terminals and len(x) > 0:
        daught0 = x[0]
        dlab = daught0 if isinstance(daught0, str) \
                        else daught0.label()
        if dlab in legal_daught0[xlab]:
            v = +1
    return Mark('good_daught0', v)


def good_daught1(x):
    v = 0
    xlab = x.label()
    if xlab in non_terminals and len(x) > 1:
        daught1 = x[1]
        dlab = daught1 if isinstance(daught1, str) \
                        else daught1.label()
        if dlab in legal_daught1[xlab]:
            v = +1
    return Mark('good_daught1', v)


# # # # # # # # # #
# Eval
Con = [
    need_parent, need_daught0, need_daught1, good_parent, good_daught0,
    good_daught1
]
weights = {x.__name__: 1.0 for x in Con}

trees = [
    ParentedTree.fromstring('(S (A0 (B b) (C c)))'),  # legal
    ParentedTree.fromstring('(S (A1 (D d) (E e)))'),  # legal
    ParentedTree.fromstring('(S (F0 (B b) (E e)))'),  # legal
    ParentedTree.fromstring('(S (A0 (B b) (E e)))'),  # frankenevil
    ParentedTree.fromstring('(S (A1 (D d) (C c)))')  # frankenevil
]
print('evaluation of trees')
for tree in trees:
    markup = Eval(tree.subtrees(), Con)
    harmony, ill_nodes = Stat(markup, weights, HGStat)
    print(tree.pformat(), f'harmony = {harmony}')
    if harmony < 0:
        print('ill-formed nodes:')
        for node in ill_nodes:
            print(node.n)
            for (key, val) in node.marks.items():
                print(key, val)
    print()