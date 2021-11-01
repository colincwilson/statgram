# -*- coding: utf-8 -*-

import collections, itertools, re, sys
from pathlib import Path

sys.path.append(str(Path.home() / 'Code/Python/fst_util'))
from fst_util import fst_config
from fst_util.fst import *

sys.path.append(str(Path.home() / 'Code/Python/statgram'))
from statgram.harmony import Mark, MarkedNode, Eval, HGStat, OTStat, Stat

StrArc = collections.namedtuple('StrArc', \
    ['src', 'ilabel', 'olabel', 'dest'])
fstat = {0: HGStat, 1: OTStat}[0]

# # # # # # # # # #
# Alphabet
sigma = {
    'p',
    't',
    'tʃ',
    'k',
    'q',  # plain
    'pʰ',  # aspirate
    'tʰ',
    'tʃʰ',
    'kʰ',
    'qʰ',
    'pʼ',  # ejective
    'tʼ',
    'tʃʼ',
    'kʼ',
    'qʼ',
    's',  # fricative
    'ʃ',
    'h',
    'm',  # nasal
    'n',
    'ɲ',
    'l',  # liquid
    'ɾ',
    'ʎ',  # glide
    'j',
    'w',
    'i',  # vowel
    'e',
    'a',
    'o',
    'u'
}
sigma = ['p', 'q', 'u', 'o', 'a']  # small Sigma for testing
fst_config.init({'sigma': list(sigma)})
print(f'|Sigma| = {len(sigma)}')
print(fst_config.sigma)
vowels = ['i', 'e', 'a', 'o', 'u']
consonants = [x for x in fst_config.sigma \
                if x not in vowels]

# # # # # # # # # #
# Gen
# Left-context machine with one-segment history
M_left = left_context_acceptor(context_length=1)
print(f'M_left: {M_left.num_states()} states, ' \
      f'{M_left.num_arcs()} arcs')
M_left.draw('Left_context.dot')
# dot -Tpdf Left_context.dot > Left_context.pdf

# Right-context machine with one-segment lookahead
M_right = right_context_acceptor(context_length=1)
print(f'M_right: {M_right.num_states()} states, ' \
      f'{M_right.num_arcs()} arcs')
M_right.draw('Right_context.dot')
# dot -Tpdf Right_context.dot > Right_context.pdf

# Combined machine with one-segment history and lookahead
Gen = compose(M_left, M_right)
#M = fst_util.map_states(M, lambda q: (q[0][0], q[1][0]))
print(f'Gen: {Gen.num_states()} states, ' \
      f'{Gen.num_arcs()} arcs')
Gen.draw('Gen.dot')
# dot -Tpdf Gen_nasal.dot > Gen_nasal.pdf

# # # # # # # # # #
# Con
# Preceding symbol (last symbol of left-hand context)
get_prec = lambda t: t.src[0][-1]
# Following symbol (first symbol of right-hand context)
get_succ = lambda t: t.dest[1][0]


def Lower(t):
    # Vowels should be [-high] when adjacent to uvulars
    v = 0
    prec, x, succ = \
        get_prec(t), t.olabel, get_succ(t)
    if re.search('[q]', prec) or re.search('[q]', succ):
        if re.search('[eoa]', x):
            v = +1
        elif re.search('[iu]', x):
            v = -1
    return Mark('Lower', v, subnode='high')


def NoMid(t):
    # Non-low vowels should be [+high]
    v = 0
    x = t.olabel
    if re.search('[iu]', x):
        v = +1
    elif re.search('[eo]', x):
        v = -1
    return Mark('NoMid', v, subnode='high')


def SyllStruc(t):
    v = 0
    prec, x, succ = get_prec(t), t.olabel, get_succ(t)
    if (prec == fst_config.bos or prec in consonants) \
      and (succ == fst_config.eos or succ in consonants) \
      and x in consonants: # No #CC, CC#, #C#, CCC
        v = -1
    elif (prec == fst_config.bos or prec in vowels) \
      and x in vowels: # No <V, VV
        v = -1
    return Mark('SyllStruc', v)


# # # # # # # # # #
# Eval
Con = [Lower, NoMid, SyllStruc]
weights = {'Lower': 2.0, 'NoMid': 1.0, 'SyllStruc': 10.0}

# Assign marks to transitions and prune
arc_map = {}
for src in Gen.states():
    for t in Gen.arcs(src):
        s = StrArc(
            Gen.state_label(src), Gen.input_label(t.ilabel),
            Gen.output_label(t.olabel), Gen.state_label(t.nextstate))
        arc_map[s] = (src, t)

fignore = lambda t: (t.olabel in [fst_config.bos, fst_config.eos])
T = arc_map.keys()
markup = Eval(T, Con, fignore)
_, nodes_ill = Stat(markup, weights, fstat)
dead_arcs = [marked_node.n for marked_node in nodes_ill]
dead_arcs = [arc_map[s] for s in dead_arcs]
Lang = Gen.delete_arcs(dead_arcs)
print(f'Lang: {Lang.num_states()} states, ' \
      f'{Lang.num_arcs()} arcs')
Lang.draw('Lang_nasal.dot')

# dot -Tpdf Lang.dot > Lang.pdf

# # # # # # # # # #
# Outputs
#Output = fst_util.intersect(Lang, fst_util.trellis(4))
#fst_util.draw(Output, 'Output.dot')
outputs = accepted_strings(Lang, max_len=4)
print('All legal words with <= 4 segments:')
print(outputs)
