import re, sys
import numpy as np
from nltk import CFG
from nltk.tree import ParentedTree
from nltk.parse import RecursiveDescentParser

sys.path.append('../..')
from statgram.harmony import Mark, MarkedNode, Eval, \
    HGStat, OTStat, Stat

# Notes
# * t.pos() gives list of (leaf, preterminal) pairs in tree t


# # # # # # # # # #
# Gen
class GridGen():

    def __init__(self):
        PrWd_rules = []
        PrWd_rules_old = ['']
        for i in range(7):  # set maximum level-1 length
            PrWd_rules_new = [x +' '+ y for x in PrWd_rules_old \
                for y in ['x', 'o']] # level-1 grid
            PrWd_rules += PrWd_rules_new
            PrWd_rules_old = PrWd_rules_new[:]

        PrWd_rules = ['PrWd -> ' + x for x in PrWd_rules]
        # Culminativity (at least one level-1 grid mark)
        PrWd_rules = [x for x in PrWd_rules if re.search('x', x)]

        # Expansions of syllable preterminals
        Term_rules = ['x -> "σ"', 'o -> "σ"']

        grammar_rules = PrWd_rules + Term_rules
        grammar_rulestr = '\n'.join(grammar_rules)
        grammar = CFG.fromstring(grammar_rulestr)
        print(f'# of productions in grammar: {len(grammar.productions())}')

        self.grammar = grammar
        self.parser = RecursiveDescentParser(grammar)

    def parses(self, inpt):
        T = [t for t in self.parser.parse(inpt.split())]
        T = [ParentedTree.convert(t) for t in T]
        return T


# # # # # # # # # #
# Constraints
def AlternateR(t):
    # In the context x __ assign -1 to x and +1 to o,
    #                o __ assign -1 to o and -1 to x
    s = t.left_sibling()
    if s is not None and t.label() in ['x', 'o']:
        v = -1 if t.label() == s.label() else +1
    else:
        v = 0
    return Mark('AlternateR', v)


def AlternateL(t):
    # In the context __ x assign -1 to x and +1 to o
    #                __ o assign -1 to o and +1 to x
    s = t.right_sibling()
    if s is not None and t.label() in ['x', 'o']:
        v = -1 if t.label() == s.label() else +1
    else:
        v = 0
    return Mark('AlternateL', v)


def StressInitial(t):
    # Assign -1.0 to o and +1.0 to x in initial position
    s = t.left_sibling()
    if s is None and t.label() in ['x', 'o']:
        v = -1 if t.label() == 'o' else +1
    else:
        v = 0
    return Mark('StressInitial', v)


def StressFinal(t):
    # Assign -1.0 to o and +1.0 to x in final position
    s = t.right_sibling()
    if s is None and t.label() in ['x', 'o']:
        v = -1 if t.label() == 'o' else +1
    else:
        v = 0
    return Mark('StressInitial', v)


def NonFinality(t):
    # Assign -1.0 to x and +1.0 to o in final position
    s = t.right_sibling()
    if s is None and t.label() in ['x', 'o']:
        v = -1 if t.label() == 'x' else +1
    else:
        v = 0
    return Mark('NonFinality', v)


# # # # # # # # # #
# Eval
Con = [AlternateR, AlternateL, StressInitial, StressFinal, NonFinality]
weights = {
    'AlternateR': 2.0,
    'AlternateL': 1.0,
    'StressInitial': 2.0,
    'StressFinal': 1.0,
    'NonFinality': 5.0
}

Gen = GridGen()
inpt = ['σ σ σ σ σ σ σ'][0]
trees = Gen.parses(inpt)

print(f'well-formed parses of {inpt}')
for tree in trees:
    markup = Eval(tree.subtrees(), Con)
    harmony, _ = Stat(markup, weights, HGStat)
    if harmony == 0.0:
        tree.pretty_print()


# # # # # # # # # #
# Extra constraints
def NoClashL(t):
    # Assign -1.0 to x and +1.0 to o in the context / __ x
    s = t.right_sibling()
    if s is not None and s.label() == 'x':
        if t.label == 'x':
            v = -1
        elif t.label == 'o':
            v = +1
    else:
        v = 0
    return Mark('NoClashL', v)


def NoClashR(t):
    # Assign -1.0 to x and +1.0 to o in the context / x __
    s = t.left_sibling()
    if s is not None and s.label() == 'x':
        if t.label == 'x':
            v = -1
        elif t.label == 'o':
            v = +1
    else:
        v = 0
    return Mark('NoClashR', v)


def NoLapseL(t):
    # Assign -1.0 to o and +1.0 to x in the context / __ o
    s = t.right_sibling()
    if s is not None and s.label() == 'o':
        if t.label == 'o':
            v = -1
        elif t.label == 'x':
            v = +1
    else:
        v = 0
    return Mark('NoLapseL', v)


def NoLapseR(t):
    # Assign -1.0 to o and +1.0 to x in the context / o __
    s = t.left_sibling()
    if s is not None and s.label == 'o':
        if t.label == 'o':
            v = -1
        elif t.label == 'x':
            v = +1
    return Mark('NoLapseR', v)
