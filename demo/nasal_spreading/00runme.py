# -*- coding: utf-8 -*-

import argparse, re, sys
import itertools
sys.path.append('../../../fst_util')
sys.path.append('../..')
from statgram.harmony import Node, HGStat, OTStat
from fst_util import fst_config, fst_util
FST, Transition = fst_util.FST, fst_util.Transition


# # # # # # # # # #
# Sigma
Sigma_seg = ['T', 'S', 'N', 'G', 'V'] # segments
Sigma_head = ['1', '0'] # head vs. dependent in span
Sigma_brack = ['(', '+', ')', '|', '-'] # span specs
Sigma = itertools.product(
    Sigma_seg, Sigma_head, Sigma_brack)
fst_config.Sigma = {''.join(x) for x in Sigma}
print(f'|Sigma| = {len(fst_config.Sigma)}')
#print(fst_config.Sigma)

def pretty_print(form):
    # x( -> (x+
    form = re.sub('(\S+)[(]', '(\\1+', form)
    # x) -> x+)
    form = re.sub('(\S+)[)]', '\\1+)', form)
    # x| -> (x+)
    form = re.sub('(\S+)[|]', '(\\1+)', form)
    # x1 -> .x
    form = re.sub('(.)[1]', '.\\1', form) # \u0332
    # x0 -> x
    form = re.sub('(.)[0]', '\\1', form)
    # x+ -> nasalized(x)
    form = re.sub('([TSGV])[+]', '\\1\u0303', form)
    # x- -> x
    form = re.sub('[-+]', '', form)
    form = re.sub('V', 'a', form)
    form = re.sub('G', 'w', form)
    form = form.lower()
    #form = re.sub(' ', '', form)
    return form

# # # # # # # # # #
# Gen
# Headed +nasal spans
M_tier = FST(
    Q = {0, 1, 2, 3, 4, 5},
    T = set(),
    q0 = 0,
    qf = {5}
)
T = M_tier.T
T.add(Transition(src=0, olabel=fst_config.begin_delim, dest=1)) # (0, >, 1)
T.add(Transition(src=1, olabel=fst_config.end_delim, dest=5)) # (1, <, 5)
for x in fst_config.Sigma:
    # Non-nasal; single-membered span
    if re.search('(0[-])|(1[|])', x): 
        T.add(Transition(src=1, olabel=x, dest=1)) 
    # Left-headed span
    if re.search('1[(]', x):
        T.add(Transition(src=1, olabel=x, dest=2))
    if re.search('0[+]', x):
        T.add(Transition(src=2, olabel=x, dest=2))
    if re.search('0[)]', x):
        T.add(Transition(src=2, olabel=x, dest=1))
    # Right-headed span
    if re.search('0[(]', x):
        T.add(Transition(src=1, olabel=x, dest=3))
    if re.search('0[+]', x):
        T.add(Transition(src=3, olabel=x, dest=3))
    if re.search('1[)]', x):
        T.add(Transition(src=3, olabel=x, dest=1))
    # Interior-headed span
    if re.search('1[+]', x):
        T.add(Transition(src=3, olabel=x, dest=4))
    if re.search('0[+]', x):
        T.add(Transition(src=4, olabel=x, dest=4))
    if re.search('0[)]', x):
        T.add(Transition(src=4, olabel=x, dest=1))
print(f'M_tier: {len(M_tier.Q)} states, {len(M_tier.T)} transitions')
fst_util.draw(M_tier, 'Tier_nasal.dot')
# dot -Tpdf Tier_nasal.dot > Tier_nasal.pdf

# Left-context machine with one-segment history
M_left = fst_util.left_context_acceptor(fst_config.Sigma, 1)
print(f'M_left: {len(M_left.Q)} states, {len(M_tier.T)} transitions')
fst_util.draw(M_left, 'Left_context.dot')
# dot -Tpdf Left_context.dot > Left_context.pdf

# Intersection of M_tier and M_left
Gen = fst_util.intersect(M_tier, M_left)
Gen = fst_util.map_states(Gen, lambda q: (q[0], q[1][0]))
print(f'Gen: {len(Gen.Q)} states, {len(Gen.T)} transitions')
fst_util.draw(Gen, 'Gen_nasal.dot')
# dot -Tpdf Gen_nasal.dot > Gen_nasal.pdf 


# # # # # # # # # #
# Constraints
def NasN(t):
    label = t.olabel
    if re.search('[N]', label):
        #if re.search('[-]', label): # N must be [+nasal]
        if not re.search('1', label): # N must be head of +nasal span
            return ('NasN', -1)
        else:
            return ('NasN', +1)
    return ('NasN', 0)

def NoNasObs(t):
    label = t.olabel
    if re.search('[TS]', label):
        if re.search('[-]', label): # obstruent must be [-nasal]
            return ('NoNasObs', +1)
        else:
            return ('NoNasObs', -1)
    return ('NoNasObs', 0)

def NoNasVoc(t):
    label = t.olabel
    if re.search('[GV]', label):
        if re.search('[-]', label): # vocoid must be [-nasal]
            return ('NoNasVoc', +1)
        else:
            return ('NoNasVoc', -1)
    return ('NoNasVoc', 0)

def SpreadR(t):
    left_context, label = \
        t.src[1], t.olabel
    if re.search('[)|]', left_context): # I shoulda been a dependent
        return ('SpreadR', -1)
    if re.search('[(+]', left_context) \
        and re.search('0[+)]', label):
            return ('SpreadR', +1)
    return ('SpreadR', 0)

def SyllStruc(t):
    left_context, label = \
        t.src[1], t.olabel
    if re.search('[TSNG]', left_context):
        if re.search('[TSNG]', label): # no clusters
            return ('SyllStruc', -1)
    if re.search('[V]', left_context):
        if re.search('[V]', label): # no hiatus
            return ('SyllStruc', -1)
    return ('SyllStruc', 0)


# # # # # # # # # #
# Eval
Con = [NasN, NoNasObs, NoNasVoc, SpreadR, SyllStruc]
weights = { 'NasN': 3.0,
            'NoNasObs': 3.0,
            'NoNasVoc': 1.0,
            'SpreadR': 2.0,
            'SyllStruc': 10.0 }
markup = {} # map transitions to mark sets
for t in Gen.T:
    if t.olabel == fst_config.end_delim:
        continue
    marks = set()
    for constraint in Con:
        mark = constraint(t)
        if mark[1] != 0:
            marks.add(mark)
    markup[t] = Node(t, marks)

_, nodes_ill = HGStat(markup.values(), weights)
#_, nodes_ill = OTStat(markup.values(), weights)
for node in nodes_ill: # xxx copy Gen first
    Gen.T.remove(node.t)
Lang = fst_util.trim(Gen)
print(f'Lang: {len(Lang.Q)} states, {len(Lang.T)} transitions')
fst_util.draw(Lang, 'Lang_nasal.dot')
# dot -Tpdf Lang_nasal.dot > Lang_nasal.pdf

# # # # # # # # # #
# Words
Output = fst_util.intersect(Lang, fst_util.trellis(4))
fst_util.draw(Output, 'Output_nasal.dot')
outputs = fst_util.accepted_strings(Lang, 4)
outputs = { pretty_print(x) for x in outputs }
print('All legal words with <= 4 segments:')
print(outputs)
