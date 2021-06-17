# -*- coding: utf-8 -*-

import re, sys
import itertools

sys.path.append('../../../fst_util')
sys.path.append('../..')
from statgram.harmony import *
from fst_util import fst_config, fst_util

FST, Transition = fst_util.FST, fst_util.Transition

fstat = {0: HGStat, 1: OTStat}[0]

# # # # # # # # # #
# Alphabet
fst_config.Sigma = {
    'p',  # plain
    't',
    'tʃ',
    'k',
    'q',
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
#fst_config.Sigma = {    # simplified for testing
#    'p', 'q',
#    'i', 'e', 'a', 'o', 'u'
#    }
print(f'|Sigma| = {len(fst_config.Sigma)}')
vowels = ['i', 'e', 'a', 'o', 'u']
consonants = [x for x in fst_config.Sigma \
                if x not in vowels]

# # # # # # # # # #
# Gen
# Left-context machine with one-segment history
M_left = fst_util.left_context_acceptor(length=1)
print(f'M_left: {len(M_left.Q)} states, {len(M_left.T)} transitions')
fst_util.draw(M_left, 'Left_context.dot')
# dot -Tpdf Left_context.dot > Left_context.pdf

# Right-context machine with one-segment lookahead
M_right = fst_util.right_context_acceptor(length=1)
print(f'M_right: {len(M_right.Q)} states, {len(M_right.T)} transitions')
fst_util.draw(M_right, 'Right_context.dot')
# dot -Tpdf Right_context.dot > Right_context.pdf

# Combined machine with one-segment history and lookahead
M = fst_util.intersect(M_left, M_right)
M = fst_util.map_states(M, lambda q: (q[0][0], q[1][0]))
print(f'M: {len(M.Q)} states, {len(M.T)} transitions')
Gen = M

# # # # # # # # # #
# Con
left_context = lambda t: t.src[0]  # label of state in M_left
right_context = lambda t: t.dest[1]  # label of state in M_right


def Lower(t):
    v = 0
    prec, x, succ = \
        left_context(t), t.olabel, right_context(t)
    if re.search('[q]', prec) or \
      re.search('[q]', succ):
        if re.search('[eoa]', x):
            v = +1
        elif re.search('[iu]', x):
            v = -1
    return Mark('Lower', v, subnode='high')


def NoMid(t):
    v = 0
    x = t.olabel
    if re.search('[iu]', x):
        v = +1
    elif re.search('[eo]', x):
        v = -1
    return Mark('NoMid', v, subnode='high')


def SyllStruc(t):
    v = 0
    prec, x, succ = \
        left_context(t), t.olabel, right_context(t)
    if (prec == fst_config.bos or prec in consonants) \
      and (succ == fst_config.eos or succ in consonants) \
      and x in consonants: # no <CC, CC>, <C>, CCC
        v = -1
    elif (prec == fst_config.bos or prec in vowels) \
      and x in vowels: # no <V, VV
        v = -1
    return Mark('SyllStruc', v)


# # # # # # # # # #
# Eval
Con = [Lower, NoMid, SyllStruc]
weights = {'Lower': 2.0, 'NoMid': 1.0, 'SyllStruc': 10.0}

# Assign marks to transitions and prune
fignore = lambda t: (t.olabel in [fst_config.bos, fst_config.eos])
markup = Eval(Gen.T, Con, fignore)
_, nodes_ill = Stat(markup, weights, fstat)
for node in nodes_ill:
    Gen.T.remove(node.n)
Lang = fst_util.connect(Gen)
print(f'Lang: {len(Lang.Q)} states, {len(Lang.T)} transitions')
fst_util.draw(Lang, 'Lang.dot')
# dot -Tpdf Lang.dot > Lang.pdf

# # # # # # # # # #
# Outputs
#Output = fst_util.intersect(Lang, fst_util.trellis(4))
#fst_util.draw(Output, 'Output.dot')
outputs = fst_util.accepted_strings(Lang, 3)
print('All legal words with <= 3 segments:')
print(outputs)
