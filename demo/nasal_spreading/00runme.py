# -*- coding: utf-8 -*-

import re, sys
import itertools
sys.path.append('../../../fst_util')
sys.path.append('../..')
from statgram.harmony import Mark, MarkedNode, Eval, \
    HGStat, OTStat, Stat
from fst_util import fst_config, fst_util
FST, Transition = fst_util.FST, fst_util.Transition

Spread_direction = {0:'LR->', 1:'<-RL'}[0]
fstat = {0:HGStat, 1:OTStat}[0]


# # # # # # # # # #
# Alphabet
Sigma_seg = ['T', 'S', 'N', 'G', 'V'] # segments
Sigma_head = ['1', '0'] # head vs. dependent in span
Sigma_brack = ['(', '+', ')', '|', '-'] # span specs
Sigma = itertools.product(
    Sigma_seg, Sigma_head, Sigma_brack)
fst_config.Sigma = {''.join(x) for x in Sigma}
print(f'|Sigma| = {len(fst_config.Sigma)}')
#print(fst_config.Sigma)

def pretty_print_spans(form):
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
M_span = FST(
    Q = {0, 1, 2, 3, 4, 5},
    T = set(),
    q0 = 0,
    qf = {5}
)
T = M_span.T
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
print(f'M_span: {len(M_span.Q)} states, {len(M_span.T)} transitions')
fst_util.draw(M_span, 'Span_nasal.dot')
# dot -Tpdf Span_nasal.dot > Span_nasal.pdf

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


# Intersection of M_tier and M_left or M_right
if Spread_direction == 'LR->':
    Gen = fst_util.intersect(M_span, M_left)
else:
    Gen = fst_util.intersect(M_span, M_right)
Gen = fst_util.map_states(Gen, lambda q: (q[0], q[1][0]))
print(f'Gen: {len(Gen.Q)} states, {len(Gen.T)} transitions')
fst_util.draw(Gen, 'Gen_nasal.dot')
# dot -Tpdf Gen_nasal.dot > Gen_nasal.pdf 


# # # # # # # # # #
# Con
def NasN(t):
    label = t.olabel
    if re.search('[N]', label):
        #if re.search('[-]', label): # N must be [+nasal]
        if re.search('1', label): # N must be head of +nasal span
            v = +1
        else:
            v = -1
    else:
        v = 0
    return Mark('NasN', v, subnode='nasal')

def NoNasObs(t):
    label = t.olabel
    if re.search('[TS]', label):
        if re.search('[-]', label): # obstruent must be [-nasal]
            v = +1
        else:
            v = -1
    else:
        v = 0
    return Mark('NoNasObs', v, subnode='nasal')

def NoNasVoc(t):
    label = t.olabel
    if re.search('[GV]', label):
        if re.search('[-]', label): # vocoid must be [-nasal]
            v = +1
        else:
            v = -1
    else:
        v = 0
    return Mark('NoNasVoc', v, subnode='nasal')

def SpreadNasR(t):
    left_context, label = \
        t.src[1], t.olabel
    if re.search('[)|]', left_context): # I shoulda been a dependent
        v = -1
    elif re.search('[(+]', left_context) \
        and re.search('0[+)]', label):
            v = +1
    else:
        v = 0
    return Mark('SpreadNasR', v, subnode='nasal')

def SpreadNasL(t):
    right_context, label = \
        t.dest[1], t.olabel
    if re.search('[(|]', right_context): # I shoulda been a dependent
        v = -1
    elif re.search('[)+]', right_context) \
        and re.search('0[+(]', label):
            v = +1
    else:
        v = 0
    return Mark('SpreadNasL', v, subnode='nasal')

def SyllStrucR(t):
    left_context, label = \
        t.src[1], t.olabel
    if re.search('[TSNG]', left_context) \
        and re.search('[TSNG]', label): # no clusters
            v = -1
    elif re.search('[V]', left_context) \
        and re.search('[V]', label): # no hiatus
            v = -1
    else:
        v = 0
    return Mark('SyllStrucR', v)

def SyllStrucL(t):
    right_context, label = \
        t.dest[1], t.olabel
    if re.search('[TSNG]', right_context) \
        and re.search('[TSNG]', label): # no clusters
            v = -1
    elif re.search('[V]', right_context) \
        and re.search('[V]', label): # no hiatus
            v = -1
    else:
        v = 0
    return Mark('SyllStrucL', v)


# # # # # # # # # #
# Eval
Con = [NasN, NoNasObs, NoNasVoc]
weights = { 'NasN': 3.0,
            'NoNasObs': 3.0,
            'NoNasVoc': 1.0 }
if Spread_direction == 'LR->':
    Con += [SpreadNasR, SyllStrucR]
    weights['SpreadNasR'] = 2.0
    weights['SyllStrucR'] = 10.0
else:
    Con += [SpreadNasL, SyllStrucL]
    weights['SpreadNasL'] = 2.0
    weights['SyllStrucL'] = 10.0

# Assign marks to transitions and prune
fignore = lambda t : (t.olabel in [fst_config.begin_delim,
                                   fst_config.end_delim])
markup = Eval(Gen.T, Con, fignore)
_, nodes_ill = Stat(markup, weights, fstat)
for node in nodes_ill: # xxx copy Gen first
    Gen.T.remove(node.n)
Lang = fst_util.connect(Gen)
print(f'Lang: {len(Lang.Q)} states, {len(Lang.T)} transitions')
fst_util.draw(Lang, 'Lang_nasal.dot')
# dot -Tpdf Lang_nasal.dot > Lang_nasal.pdf


# # # # # # # # # #
# Outputs
Output = fst_util.intersect(Lang, fst_util.trellis(4))
fst_util.draw(Output, 'Output_nasal.dot')
outputs = fst_util.accepted_strings(Lang, 4)
outputs = { pretty_print_spans(x) for x in outputs }
print('All legal words with <= 4 segments:')
print(outputs)
