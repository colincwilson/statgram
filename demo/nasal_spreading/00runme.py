# -*- coding: utf-8 -*-

import collections, itertools, re, sys
from pathlib import Path

sys.path.append(str(Path.home() / 'Code/Python/fst_util'))
from fst_util import config as fst_config
from fst_util.fst import *

sys.path.append(str(Path.home() / 'Code/Python/statgram'))
from statgram.harmony import Mark, MarkedNode, Eval, HGStat, OTStat, Stat


StrArc = collections.namedtuple('StrArc', \
    ['src', 'ilabel', 'olabel', 'dest'])
spread_direction = {0: 'LR->', 1: '<-RL'}[0]
fstat = {0: HGStat, 1: OTStat}[0]

# # # # # # # # # #
# Alphabet
sigma_seg = ['T', 'S', 'N', 'G', 'V']  # Segments
sigma_head = ['1', '0']  # Head vs. dependent within span
sigma_brack = ['(', '+', ')', '|', '-']  # Span specs
sigma = itertools.product(sigma_seg, sigma_head, sigma_brack)
sigma = [''.join(x) for x in sigma]
fst_config.init({'sigma': sigma})
print(f'|Sigma| = {len(sigma)}')
print(fst_config.sigma)


def pretty_print_spans(form):
    # x( -> (x+
    form = re.sub('(\S+)[(]', '(\\1+', form)
    # x) -> x+)
    form = re.sub('(\S+)[)]', '\\1+)', form)
    # x| -> (x+)
    form = re.sub('(\S+)[|]', '(\\1+)', form)
    # x1 -> .x
    form = re.sub('(.)[1]', '.\\1', form)  # \u0332
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
M_span = Fst(fst_config.symtable)
for q in range(6):
    M_span.add_state(q)
M_span.set_start(0)
M_span.set_final(5)
M_span.add_arc(src=0, ilabel=fst_config.bos, dest=1)  # (0, >, 1)
M_span.add_arc(src=1, ilabel=fst_config.eos, dest=5)  # (1, <, 5)
for x in fst_config.sigma:
    # Non-nasal; single-membered span
    if re.search('(0[-])|(1[|])', x):
        M_span.add_arc(src=1, ilabel=x, dest=1)
    # Left-headed span
    if re.search('1[(]', x):
        M_span.add_arc(src=1, ilabel=x, dest=2)
    if re.search('0[+]', x):
        M_span.add_arc(src=2, ilabel=x, dest=2)
    if re.search('0[)]', x):
        M_span.add_arc(src=2, ilabel=x, dest=1)
    # Right-headed span
    if re.search('0[(]', x):
        M_span.add_arc(src=1, ilabel=x, dest=3)
    if re.search('0[+]', x):
        M_span.add_arc(src=3, ilabel=x, dest=3)
    if re.search('1[)]', x):
        M_span.add_arc(src=3, ilabel=x, dest=1)
    # Interior-headed span
    if re.search('1[+]', x):
        M_span.add_arc(src=3, ilabel=x, dest=4)
    if re.search('0[+]', x):
        M_span.add_arc(src=4, ilabel=x, dest=4)
    if re.search('0[)]', x):
        M_span.add_arc(src=4, ilabel=x, dest=1)
print(f'M_span: {M_span.num_states()} states, ' \
      f'{M_span.num_arcs()} arcs')
M_span.draw('Span_nasal.dot')
# dot -Tpdf Span_nasal.dot > Span_nasal.pdf

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

# Intersection of M_tier and M_left or M_right
if spread_direction == 'LR->':
    Gen = compose(M_span, M_left)
else:
    Gen = compose(M_span, M_right)
print(f'Gen: {Gen.num_states()} states, ' \
      f'{Gen.num_arcs()} arcs')
Gen.draw('Gen_nasal.dot')

# dot -Tpdf Gen_nasal.dot > Gen_nasal.pdf

# # # # # # # # # #
# Con
# Preceding symbol (last symbol of left-hand context)
get_prec = lambda t: t.src[1][-1]
# Following symbol (first symbol of right-hand context)
get_succ = lambda t: t.dest[1][0]


def NasN(t):
    # Nasals must be [+nasal] and span heads
    v = 0
    x = t.olabel
    if re.search('[N]', x):
        #if re.search('[-]', label): # N must be [+nasal]
        if re.search('1', x):  # N must be head of +nasal span
            v = +1
        else:
            v = -1
    return Mark('NasN', v, subnode='nasal')


def NoNasObs(t):
    # Obstruents must be [-nasal]
    v = 0
    x = t.olabel
    if re.search('[TS]', x):
        if re.search('[-]', x):
            v = +1
        else:
            v = -1
    return Mark('NoNasObs', v, subnode='nasal')


def NoNasVoc(t):
    # Vocoids must be [-nasal]
    v = 0
    x = t.olabel
    if re.search('[GV]', x):
        if re.search('[-]', x):
            v = +1
        else:
            v = -1
    return Mark('NoNasVoc', v, subnode='nasal')


def SpreadNasR(t):
    # Segments immediately following span members must be dependents
    v = 0
    prec, x = get_prec(t), t.olabel
    if re.search('[)|]', prec):  # Preceded by span edge
        v = -1
    elif re.search('[(+]', prec) \
        and re.search('0[+)]', x): # Dependent
        v = +1
    return Mark('SpreadNasR', v, subnode='nasal')


def SpreadNasL(t):
    # Segments immediately preceded by span members must be dependents
    v = 0
    x, succ = x, get_succ(t)
    if re.search('[(|]', succ):  # Followed by span edge
        v = -1
    elif re.search('[)+]', succ) \
        and re.search('0[+(]', x): # Dependent
        v = +1
    return Mark('SpreadNasL', v, subnode='nasal')


def SyllStrucR(t):
    v = 0
    prec, x = get_prec(t), t.olabel
    if re.search('[TSNG]', prec) \
        and re.search('[TSNG]', x): # No clusters
        v = -1
    elif re.search('[V]', prec) \
        and re.search('[V]', x): # No hiatus
        v = -1
    return Mark('SyllStrucR', v)


def SyllStrucL(t):
    v = 0
    x, succ = t.olabel, get_succ(t)
    if re.search('[TSNG]', succ) \
        and re.search('[TSNG]', x): # No clusters
        v = -1
    elif re.search('[V]', succ) \
        and re.search('[V]', x): # No hiatus
        v = -1
    return Mark('SyllStrucL', v)


# # # # # # # # # #
# Eval
Con = [NasN, NoNasObs, NoNasVoc]
weights = {'NasN': 3.0, 'NoNasObs': 3.0, 'NoNasVoc': 1.0}
if spread_direction == 'LR->':
    Con += [SpreadNasR, SyllStrucR]
    weights['SpreadNasR'] = 2.0
    weights['SyllStrucR'] = 10.0
else:
    Con += [SpreadNasL, SyllStrucL]
    weights['SpreadNasL'] = 2.0
    weights['SyllStrucL'] = 10.0

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
# dot -Tpdf Lang_nasal.dot > Lang_nasal.pdf

# # # # # # # # # #
# Outputs
#Output = fst_util.intersect(Lang, fst_util.trellis(4))
#fst_util.draw(Output, 'Output_nasal.dot')
outputs = accepted_strings(Lang, max_len=4)
outputs = {pretty_print_spans(x) for x in outputs}
print('All legal words with <= 4 segments:')
print(outputs)
