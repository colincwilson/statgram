import re, sys
import numpy as np
from nltk import CFG
from nltk.parse import RecursiveDescentParser, generate
from nltk.tree import Tree, ParentedTree

# Notes
# * t.pos() gives list of (leaf, preterminal) pairs in tree t

class GridGrammar():
    def __init__(self):
        PrWd_rules = []
        PrWd_rules_old = ['']
        for i in range(7):
            PrWd_rules_new = [x +' '+ y for x in PrWd_rules_old \
                for y in ['x', 'o']] # level-1 grid
            PrWd_rules += PrWd_rules_new
            PrWd_rules_old = PrWd_rules_new[:]

        PrWd_rules = ['PrWd -> '+ x for x in PrWd_rules]
        # Culminativity (at least one level-1 grid mark)
        PrWd_rules = [x for x in PrWd_rules if re.search('x', x)]

        # Expansions of syllable preterminals
        Term_rules = ['x -> "s"', 'o -> "s"']

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


# Create grammar and enumerate prosodic parses 
# for a given number of unmarked syllables
G = GridGrammar()
input0 = ['s s s s', 's s s s s', 's s s s s s s'][2]
trees0 = [t for t in G.parses(input0)]
#for t in trees0:
#    t.pretty_print()
print(len(trees0))
#trees0[0].pretty_print()

# # # # # # # # # #
# Initialize mark accumulators on nodes
def init_marks(t):
    for n in t.subtrees():
        n.marks = {}

# Print subtrees with their marks
def print_marks(t, w = None):
    i = 0
    for n in t.subtrees():
        if w is None:
            marks = n.marks
        else:
            marks = {}
            for c in n.marks:
                marks[c] = w[c] * n.marks[c]
        h = np.sum([marks[c] for c in marks])
        h = h if h < 0.0 else 0.0
        print (f'n{i}', n, marks, h)
        i += 1

# Sum marks over subtrees under min0 non-linearity
# xxx add strict domination option
def harmony(t, w):
    h_t = 0.0
    for n in t.subtrees():
        # Sum weighted marks within node
        h_n = 0.0
        for c in n.marks:
            h_n += w[c] * n.marks[c]
        # Apply min0 non-linearity within node
        h_n = h_n if h_n <= 0.0 else 0.0
        # Accumulate harmony over nodes
        h_t += h_n
    t.harmony = h_t


# # # # # # # # # #
# Define grid constraints as mark assigners
def clash0(t):
    # Assign -1.0 to x and +1.0 to o in the context / __ x
    for n1 in t.subtrees():
        n2 = n1.right_sibling()
        if n2 is None or n2.label() != 'x':
            continue
        if n1.label() == 'x':
            n1.marks['clash0'] = -1.0
        elif n1.label() == 'o':
            n1.marks['clash0'] = +1.0

def clash1(t):
    # Assign -1.0 to x and +1.0 to o in the context / x __
    for n1 in t.subtrees():
        n2 = n1.left_sibling()
        if n2 is None or n2.label() != 'x':
            continue
        if n1.label() == 'x':
            n1.marks['clash1'] = -1.0
        elif n1.label() == 'o':
            n1.marks['clash1'] = +1.0

def lapse0(t):
    # Assign -1.0 to o and +1.0 to x in the context / __ o
    for n1 in t.subtrees():
        n2 = n1.right_sibling()
        if n2 is None or n2.label() != 'o':
            continue
        if n1.label() == 'o':
            n1.marks['lapse0'] = -1.0
        elif n1.label() == 'x':
            n1.marks['lapse0'] = +1.0

def lapse1(t):
    # Assign -1.0 to o and +1.0 to x in the context / o __
    for n1 in t.subtrees():
        n2 = n1.left_sibling()
        if n2 is None or n2.label() != 'o':
            continue
        if n1.label() == 'o':
            n1.marks['lapse1'] = -1.0
        elif n1.label() == 'x':
            n1.marks['lapse1'] = +1.0

def alternate_LR(t):
    # In the context x __ assign -1 to x and +1 to o,
    #                o __ assign -1 to o and -1 to x
    for n1 in t.subtrees():
        if n1.label() not in ['x', 'o']:
            continue
        n2 = n1.left_sibling()
        if n2 is None:
            continue
        mark = -1.0 if n1.label() == n2.label() else +1.0
        n1.marks['alternate_LR'] = mark

def alternate_RL(t):
    # In the context __ x assign -1 to x and +1 to o
    #                __ o assign -1 to o and +1 to x
    for n1 in t.subtrees():
        if n1.label() not in ['x', 'o']:
            continue
        n2 = n1.right_sibling()
        if n2 is None:
            continue
        mark = -1.0 if n1.label() == n2.label() else +1.0
        n1.marks['alternate_RL'] = mark

def stress_initial(t):
    # Assign -1.0 to o and +1.0 to x in initial position
    n1 = t[0]
    if n1.label() == 'o':
        mark = -1.0
    elif n1.label() == 'x':
        mark = +1.0
    n1.marks['stress_initial'] = mark

def stress_final(t):
    # Assign -1.0 to o and +1.0 to x in final position
    n1 = t[-1]
    if n1.label() == 'o':
        mark = -1.0
    elif n1.label() == 'x':
        mark = +1.0
    n1.marks['stress_final'] = mark

def nonfinality(t):
    # Assign -1.0 to x and +1.0 to o in final position
    n1 = t[-1]
    if n1.label() == 'x':
        mark = -1.0
    elif n1.label() == 'o':
        mark = +1.0
    n1.marks['nonfinality'] = mark

# # # # # # # # # #
# Constraints and weights
constraints = [
    alternate_LR,
    alternate_RL,
    stress_initial,
    stress_final,
    nonfinality
]
weights = {
    'alternate_LR': 2.0,
    'alternate_RL': 1.0,
    'stress_initial': 2.0,
    'stress_final': 1.0,
    'nonfinality': 5.0
}

# # # # # # # # # #
# Evaluate trees and print optima
for t in trees0:
    init_marks(t)
    for constraint in constraints:
        constraint(t)
    harmony(t, weights)
    if t.harmony == 0.0:
        t.pretty_print()
        print_marks(t, weights)
sys.exit(0)




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
