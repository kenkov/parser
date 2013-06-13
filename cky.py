#! /usr/bin/env python
# coding:utf-8

from __future__ import division
from collections import defaultdict


def _terminal_grammar(grammar):
    return [(syms, prob) for syms, prob in grammar.items() if len(syms) == 2]


def _non_terminal_grammar(grammar):
    for syms, prob in grammar.items():
        if len(syms) == 3:
            yield (syms, prob)


def cyk(sent, grammar):

    # chart[("N", 1, 2)] = 1.2
    chart = defaultdict(float)
    # chart_ind[(i, j)] = {("N", 1, 2), ...}
    chart_ind = defaultdict(set)

    # if there is "A -> B C 0.5", then
    # grammar_hash is
    # grammar_hash[("B", "C")] = {("A", "B", "C"), ...}
    grammar_hash = defaultdict(set)
    # grammar[("A", "B", "C")] = 0.5
    gram = {}

    # initialize
    tg = _terminal_grammar(grammar)
    for i in range(len(sent)):
        for sym, word, prob in [(sym, word, prob) for (sym, word), prob in tg
                                if word == sent[i]]:
            chart[(sym, i, i)] = prob
            chart_ind[(i, i)].add((sym, i, i))
    for (sym, lsym, rsym), prob in _non_terminal_grammar(grammar):
        grammar_hash[(lsym, rsym)].add((sym, lsym, rsym))
        gram[(sym, lsym, rsym)] = prob

    n = len(sent)
    # topological order
    for j in range(1, n):
        for i in range(n-j):
            v_index = (i, i + j)
            # calculate BS(v) for the hypergraph
            print v_index
            for k in range(i, i + j):
                lindex = (i, k)
                rindex = (k + 1, i + j)
                print "  {} {}".format(lindex, rindex)
                for lsym, rsym in grammar_hash:
                    for sym, _, _ in grammar_hash[(lsym, rsym)]:
                        if lsym in {s for s, _, _ in chart_ind[lindex]} and \
                                rsym in {s for s, _, _ in chart_ind[rindex]}:
                            print "    {} -> {} {}".format(sym, lsym, rsym)
                            # calculate probability
                            prob = chart[(lsym, lindex[0], lindex[1])] * \
                                chart[(rsym, rindex[0], rindex[1])] * \
                                gram[(sym, lsym, rsym)]
                            # update chart
                            if prob >= chart[(sym, i, i + j)]:
                                chart[(sym, i, i + j)] = prob
                                chart_ind[v_index].add((sym, i, i + j))
                                print "    update: {}, {}, {}".format(
                                    sym, (i, i+j), prob)
    return chart


def test1():
    grammar = {("S", "NP", "VP"): 0.4,
               ("VP", "V", "NP"): 0.3,
               ("NP", u"I"): 0.5,
               ("NP", u"Rikka"): 0.5,
               ("NNP", u"Rikka"): 0.5,
               ("V", u"love"): 0.7}
    #sent = ["".join(["'", w, "'"]) for w in u"I love Rikka".split()]
    sent = "I love Rikka".split()
    print cyk(sent, grammar)


def test2():
    grammar = {("S", "N", "V"): 0.4,
               ("S", "S", "PP"): 0.3,
               ("S", "V", "N"): 0.3,
               ("V", "V", "N"): 0.3,
               ("PP", "P", "N"): 0.3,
               ("N", "N", "PP"): 0.3,
               ("N", "I"): 0.3,
               ("N", "Maria"): 0.3,
               ("N", "pizza"): 0.3,
               ("V", "eat"): 0.3,
               ("P", "with"): 0.3,
               }

    #sent = ["".join(["'", w, "'"]) for w in u"I love Rikka".split()]
    sent = "I eat pizza with Maria".split()
    print cyk(sent, grammar)


if __name__ == '__main__':
    test2()
