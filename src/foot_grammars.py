import re, sys
import numpy as np
from nltk import CFG
from nltk.parse import RecursiveDescentParser, generate
from nltk.tree import Tree, ParentedTree # xxx switch to ParentedTree!

# Notes
# * t.pos() gives list of (leaf, preterminal) pairs in tree t


class ProsodicGrammar():
    def __init__(self):
        # Expansions of PrWd
        PrWd_rules = []
        PrWd_rules_old = ['']
        for i in range(5):
            PrWd_rules_new = [x+' '+y for x in PrWd_rules_old \
                for y in ['MainFt', 'Ft', 'Syll']]
            PrWd_rules += PrWd_rules_new
            PrWd_rules_old = PrWd_rules_new[:]

        PrWd_rules = ['PrWd -> '+ x for x in PrWd_rules]
        # Culminativity (exactly one main-stress foot)
        PrWd_rules = [x for x in PrWd_rules if re.search('Main', x)]
        PrWd_rules = [x for x in PrWd_rules if not re.search('Main.*Main', x)]
        #print(len(PrWd_rules))

        # Expansions of (Main)Ft
        MainFt_rules = ['MainFt -> '+y for y in \
            ['MainStressSyll', 'MainStressSyll Syll', 'Syll MainStressSyll']]

        Ft_rules = ['Ft -> '+y for y in \
            ['StressSyll', 'StressSyll Syll', 'Syll StressSyll']]

        # Expansions of (Main)(Stress)Syll
        Syll_rules = ['MainStressSyll -> s1', 'StressSyll -> s2', 'Syll -> s0']

        # Expansions of syllable preterminals
        Term_rules = ['s1 -> "s"', 's2 -> "s"', 's0 -> "s"']

        grammar_rules = PrWd_rules + MainFt_rules + Ft_rules + Syll_rules + Term_rules
        grammar_rulestr = '\n'.join(grammar_rules)
        grammar = CFG.fromstring(grammar_rulestr)
        print('# of productions in grammar:', len(grammar.productions()))

        self.grammar = grammar
        self.parser = RecursiveDescentParser(grammar)

    def parses(self, inpt):
        T = [t for t in self.parser.parse(inpt.split())]
        T = [ParentedTree.convert(t) for t in T]
        return T


# Create grammar and enumerate prosodic parses 
# for a given number of unmarked syllables
G = ProsodicGrammar()
input0 = 's s s s s'
trees0 = [t for t in G.parses(input0)]
#for t in trees0:
#    t.pretty_print()
print(len(trees0))


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
# Parse-syll
def iambic(t):
    # Assign -1.0 to feet that are not iambic
    for s in t.subtrees():
        if not s.label() in ['MainFt', 'Ft']:
            continue
        if len(s) == 1:
            continue
        if s[0].label() in ['MainStressSyll', 'StressSyll']:
            s.marks['Iambic'] = -1.0

def trochaic(t):
    # Assign -1.0 to feet that are not trochaic
    for s in t.subtrees():
        if not s.label() in ['MainFt', 'Ft']:
            continue
        if len(s) == 1:
            continue
        if s[1].label() in ['MainStressSyll', 'StressSyll']:
            s.marks['Trochaic'] = -1.0

def parse_syll(t):
    # Assign -1.0 to immed. syllable dependents of PrWd
    for s in t:
        if s.label() == 'Syll':
            s.marks['ParseSyll'] = -1.0

# Foot Binarity
def foot_bin(t):
    # Assign -1.0 to subminimal/supermaximal Feet
    for s in t.subtrees():
        if not s.label() in ['MainFt', 'Ft']:
            continue
        if len(s) != 2:
            s.marks['FootBin'] = -1.0

# MainFoot-Left/-Right
def mainfoot_left(t):
    # Assign -1.0 to main-stress foot that is not leftmost foot
    previous_foot = False
    for s in t:
        #print('***', s)
        if previous_foot and s.label() == 'MainFt':
            s.marks['MainFoot-L'] = -1.0
        if s.label() in ['MainFt', 'Ft']:
            previous_foot = True

def mainfoot_right(t):
    # Assign -1.0 to main-stress foot that is not rightmost foot
    following_foot = False
    for s in t[::-1]:
        #print('***', s)
        if following_foot and s.label() == 'MainFt':
            s.marks['MainFoot-R'] = -1.0
        if s.label() in ['MainFt', 'Ft']:
            following_foot = True

# AllFoot-Left/Right [categorical as in McCarthy xxxx]
def allfoot_left(t):
    # Assign -1.0 to each foot that is preceded by  
    # an unfooted syllable
    preceding_unparsed = False
    for s in t:
        if preceding_unparsed and s.label() in ['MainFt', 'Ft']:
            s.marks['AllFoot-L'] = -1.0
        preceding_unparsed = (s.label() == 'Syll')

def allfoot_right(t):
    # Assign -1.0 to each foot that is followed by 
    # an unfooted syllable
    following_unparsed = False
    for s in t[::-1]:
        if following_unparsed and s.label() in ['MainFt', 'Ft']:
            s.marks['AllFoot-R'] = -1.0
        following_unparsed = (s.label() == 'Syll')

tree0 = trees0[0]
tree0.pretty_print()
init_marks(tree0)
constraints = [
    iambic,
    trochaic,
    parse_syll,
    foot_bin,
    mainfoot_left,
    mainfoot_right,
    allfeet_left,
    allfeet_right
]

t_max_harmony = []
max_harmony = -np.inf
for t in trees0:
    init_marks(t)
    for constraint in constraints:
        constraint(t)
    h_t = harmony(t)
    if h_t > max_harmony:
        t_max_harmony = [t,]
        max_harmony = h_t
    elif h_t == max_harmony:
        t_max_harmony += [t,]
    print(t, h_t)

print('max harmony: ', max_harmony)
for t in t_max_harmony:
    stress = t.pos()
    stress = [x[1] for x in stress]
    print(' '.join(stress))
