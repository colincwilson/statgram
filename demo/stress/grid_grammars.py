import re, sys
import numpy as np
from nltk import CFG
from nltk.parse import RecursiveDescentParser, generate
from nltk.tree import Tree, ParentedTree
sys.path.append('../..')
from statgram.harmony import Node, HGStat_, HGStat, OTStat_, OTStat

# Notes
# * t.pos() gives list of (leaf, preterminal) pairs in tree t

# # # # # # # # # #
# Gen
class GridGrammar():
    def __init__(self):
        PrWd_rules = []
        PrWd_rules_old = ['']
        for i in range(7): # set maximum level-1 length
            PrWd_rules_new = [x +' '+ y for x in PrWd_rules_old \
                for y in ['x', 'o']] # level-1 grid
            PrWd_rules += PrWd_rules_new
            PrWd_rules_old = PrWd_rules_new[:]

        PrWd_rules = ['PrWd -> '+ x for x in PrWd_rules]
        # Culminativity (at least one level-1 grid mark)
        PrWd_rules = [x for x in PrWd_rules if re.search('x', x)]

        # Expansions of syllable preterminals
        Term_rules = ['x -> "σ"', 'o -> "σ"']

        grammar_rules = PrWd_rules + Term_rules
        grammar_rulestr = '\n'.join(grammar_rules)
        grammar = CFG.fromstring(grammar_rulestr)
        print('# of productions in grammar:', len(grammar.productions()))

        self.grammar = grammar
        self.parser = RecursiveDescentParser(grammar)

    def parses(self, inpt):
        T = [t for t in self.parser.parse(inpt.split())]
        T = [ParentedTree.convert(t) for t in T]
        return T


# # # # # # # # # #
# Constraints
def NoClash0(t):
    # Assign -1.0 to x and +1.0 to o in the context / __ x
    s = t.right_sibling()
    if s is not None and s.label() == 'x':
        if t.label == 'x':
            return ('NoClash0', -1)
        if t.label == 'o':
            return ('NoClash0', +1)
    return ('NoClash0', 0)

def NoClash1(t):
    # Assign -1.0 to x and +1.0 to o in the context / x __
    s = t.left_sibling()
    if s is not None and s.label() == 'x':
        if t.label == 'x':
            return ('NoClash1', -1)
        if t.label == 'o':
            return ('NoClash1', +1)
    return ('NoClash0', 0)

def NoLapse0(t):
    # Assign -1.0 to o and +1.0 to x in the context / __ o
    s = t.right_sibling()
    if s is not None and s.label() == 'o':
        if t.label == 'o':
            return ('NoLapse0', -1)
        if t.label == 'x':
            return ('NoLapse0', +1)
    return ('NoLapse0', 0)

def NoLapse1(t):
    # Assign -1.0 to o and +1.0 to x in the context / o __
    s = t.left_sibling()
    if s is not None and s.label == 'o':
        if t.label == 'o':
            return ('NoLapse1', -1)
        if t.label == 'x':
            return ('NoLapse1', +1)
    return ('NoLapse1', 0)

def AlternateLR(t):
    # In the context x __ assign -1 to x and +1 to o,
    #                o __ assign -1 to o and -1 to x
    s = t.left_sibling()
    if t.label() in ['x', 'o'] and s is not None:
        m = -1 if t.label() == s.label() else +1
        return ('AlternateLR', m)
    return ('AlternateLR', 0)

def AlternateRL(t):
    # In the context __ x assign -1 to x and +1 to o
    #                __ o assign -1 to o and +1 to x
    s = t.right_sibling()
    if t.label() in ['x', 'o'] and s is not None:
        m = -1 if t.label() == s.label() else +1
        return ('AlternateRL', m)
    return ('AlternateRL', 0)

def StressInitial(t):
    # Assign -1.0 to o and +1.0 to x in initial position
    s = t.left_sibling()
    if t.label() in ['x', 'o'] and s is None:
        m = -1 if t.label() == 'o' else +1
        return ('StressInitial', m)
    return ('StressInitial', 0)

def StressFinal(t):
    # Assign -1.0 to o and +1.0 to x in final position
    s = t.right_sibling()
    if t.label() in ['x', 'o'] and s is None:
        m = -1 if t.label() == 'o' else +1
        return ('StressFinal', m)
    return ('StressInitial', 0)

def NonFinality(t):
    # Assign -1.0 to x and +1.0 to o in final position
    s = t.right_sibling()
    if t.label() in ['x', 'o'] and s is None:
        m = -1 if t.label() == 'x' else +1
        return ('NonFinality', m)
    return ('NonFinality', 0)


# # # # # # # # # #
# Eval
Con = [AlternateLR, AlternateRL,
       StressInitial, StressFinal, NonFinality]
weights = { 'AlternateLR': 2.0,
            'AlternateRL': 1.0,
            'StressInitial': 2.0,
            'StressFinal': 1.0,
            'NonFinality': 5.0 }

grid_grammar = GridGrammar()
inpt = ['σ σ σ σ σ σ σ'][0]
trees = grid_grammar.parses(inpt)

for tree in trees:
    nodes = []
    for t in tree.subtrees():
        marks = set()
        for constraint in Con:
            mark = constraint(t)
            if mark[1] != 0:
                marks.add(mark)
        nodes.append(Node(t, marks))
    harmony, _ = HGStat(nodes, weights)
    if harmony == 0.0:
        tree.pretty_print()
