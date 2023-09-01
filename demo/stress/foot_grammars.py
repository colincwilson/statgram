import re, sys
import numpy as np
from nltk import CFG
from nltk.parse import RecursiveDescentParser
from nltk.tree import ParentedTree

sys.path.append('../..')
from statgram.harmony import Mark, MarkedNode, Eval, \
    HGStat, OTStat, Stat


# # # # # # # # # # #
# Gen
class FootGen():

    def __init__(self):
        # Expansions of PrWd
        PrWd_rules = []
        PrWd_rules_old = ['']
        for i in range(5):
            PrWd_rules_new = [x+' '+y for x in PrWd_rules_old \
                for y in ['MainFt', 'Ft', 'Syll']]
            PrWd_rules += PrWd_rules_new
            PrWd_rules_old = PrWd_rules_new[:]

        PrWd_rules = ['PrWd -> ' + x for x in PrWd_rules]
        # Culminativity (exactly one main-stress foot)
        PrWd_rules = [x for x in PrWd_rules if re.search('Main', x) \
                                and not re.search('Main.*Main', x)]
        #print(len(PrWd_rules))

        # Expansions of (Main)Ft
        MainFt_rules = ['MainFt -> '+y for y in \
            ['MainStressSyll', 'MainStressSyll Syll', 'Syll MainStressSyll']]

        Ft_rules = ['Ft -> '+y for y in \
            ['StressSyll', 'StressSyll Syll', 'Syll StressSyll']]

        # Expansions of (Main)(Stress)Syll
        Syll_rules = ['MainStressSyll -> s1', 'StressSyll -> s2', 'Syll -> s0']

        # Expansions of syllable preterminals
        Term_rules = ['s1 -> "σ"', 's2 -> "σ"', 's0 -> "σ"']

        grammar_rules = PrWd_rules + MainFt_rules \
                        + Ft_rules + Syll_rules + Term_rules
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
# Con
is_foot = lambda s: re.search('Ft', s.label())


def Iambic(s):
    if is_foot(s) and len(s) > 1:
        if re.search('StressSyll', s[1].label()):  # right-headed Ft
            v = +1
        else:
            v = -1
    else:
        v = 0
    return Mark('Iambic', v, subnode='lower')


def Trochaic(s):
    if is_foot(s) and len(s) > 1:
        if re.search('StressSyll', s[0].label()):  # left-headed Ft
            v = +1
        else:
            v = -1
    else:
        v = 0
    return Mark('Trochaic', v, subnode='lower')


def ParseSyll(s):
    # Assign -1.0 to immed. syllable dependents of PrWd
    if s.label() == 'Syll':
        v = -1
    else:
        v = 0
    return Mark('ParseSyll', v)


def FootBinarity(s):
    # Assign -1.0 to subminimal/supermaximal Feet
    if is_foot(s):
        if len(s) == 2:
            v = +1
        else:
            v = -1
    else:
        v = 0
    return Mark('FootBinarity', v, subnode='lower')


# MainFoot-Left/-Right
def MainFootLeft(s):
    # Assign -1.0 to main-stress foot that is not leftmost foot
    v = 0
    if is_foot(s):
        t = s
        while (t.left_sibling() is not None):
            t = t.left_sibling()
            if is_foot(t):
                v = -1
                break
    return Mark('MainFootLeft', v, subnode='upper')


def MainFootRight(s):
    # Assign -1.0 to main-stress foot that is not rightmost foot
    v = 0
    if is_foot(s):
        t = s
        while (t.right_sibling() is not None):
            t = t.right_sibling()
            if is_foot(t):
                v = -1
                break
    return Mark('MainFootRight', v, subnode='upper')


# AllFeet-Left/Right [categorical as in McCarthy 2003]
def AllFeetLeft(s):
    # Assign -1.0 to each foot that is immed. preceded by
    # an unfooted syllable
    if is_foot(s) and s.left_sibling() is not None \
      and s.left_sibling().label() == 'Syll':
        v = -1
    else:
        v = 0
    return Mark('AllFeetLeft', v, subnode='upper')


def AllFeetRight(s):
    # Assign -1.0 to each foot that is immed. followed by
    # an unfooted syllable
    if is_foot(s) and s.right_sibling() is not None \
      and s.right_sibling().label() == 'Syll':
        v = -1
    else:
        v = 0
    return Mark('AllFeetRight', v, subnode='upper')


# # # # # # # # # #
# Eval
Con = [
    Iambic, Trochaic, ParseSyll, FootBinarity, MainFootLeft, MainFootRight,
    AllFeetLeft, AllFeetRight
]
weights = {
    'Iambic': 10.0,
    'Trochaic': 0.0,
    'ParseSyll': 0.0,
    'FootBinarity': 1.0,
    'MainFootLeft': 10.0,
    'MainFootRight': 0.0,
    'AllFeetLeft': 10.0,
    'AllFeetRight': 0.0
}

# Create grammar and enumerate prosodic parses
# for a given number of unmarked syllables
Gen = FootGen()
inpt = 'σ σ σ σ σ'
trees = [t for t in Gen.parses(inpt)]
print(f'# of trees in Gen({inpt}): {len(trees)}')

print(f'well-formed parses of {inpt}')
for tree in trees:
    markup = Eval(tree.subtrees(), Con)
    harmony, _ = Stat(markup, weights, HGStat)
    if harmony == 0.0:
        tree.pretty_print()

sys.exit(0)


# # # # # # # # # #
# Initialize mark accumulators on nodes
def init_marks(t):
    for s in t.subtrees():
        s.marks = {}


# Print subtrees with their marks
def print_marks(t):
    for s in t.subtrees():
        print(s, s.marks)


# Sum marks over subtrees under min0 non-linearity
# xxx add constraint weights and strict domination option
def harmony(t):
    h_t = 0.0
    for s in t.subtrees():
        h_s = 0.0
        for c in s.marks:
            h_s += s.marks[c]
        h_s = h_s if h_s <= 0.0 else 0.0
        h_t += h_s
    return h_t


# # # # # # # # # #
# Define stress constraints as mark assigners

tree0 = trees0[0]
tree0.pretty_print()
init_marks(tree0)

t_max_harmony = []
max_harmony = -np.inf
for t in trees0:
    init_marks(t)
    for constraint in constraints:
        constraint(t)
    h_t = harmony(t)
    if h_t > max_harmony:
        t_max_harmony = [
            t,
        ]
        max_harmony = h_t
    elif h_t == max_harmony:
        t_max_harmony += [
            t,
        ]
    print(t, h_t)

print('max harmony: ', max_harmony)
for t in t_max_harmony:
    stress = t.pos()
    stress = [x[1] for x in stress]
    print(' '.join(stress))
