#! /usr/bin/env python
# coding:utf-8

from __future__ import division
from collections import defaultdict
import re
from heapdict import heapdict


class Arc(object):
    def __init__(self, lhs, before, after, start, end, prob):
        self.lhs = lhs
        self.before = before
        self.after = after
        self.start = start
        self.end = end
        self.prob = prob

    def __cmp__(self, other):
        return all([
            self.lhs == other.lhs,
            self.before == other.before,
            self.after == other.after,
            self.start == other.start,
            self.end == other.end,
            self.prob == other.prob])

    def __hash__(self):
        return hash(
            (self.lhs, self.before, self.after,
             self.start, self.end, self.prob))

    def __add__(self, other):
        return DeductiveArc(self, other)

    def __unicode__(self):
        fmt = u"[{p}] ({s}, {e}) {lhs} -> {bf}・{af}"
        return fmt.format(
            s=self.start, e=self.end, lhs=self.lhs,
            bf=" ".join(self.before),
            af=" ".join(self.after),
            p=self.prob)

    def __str__(self):
        return self.__unicode__().encode('utf-8')


class DeductiveArc(object):
    def __init__(self, lhyp, rhyp):
        if not (lhyp.after and
                lhyp.after[0] == rhyp.lhs and
                lhyp.end == rhyp.start):
            raise Exception("Two hypothesis cannot be merged")
        self.lhyp = lhyp
        self.rhyp = rhyp
        self.conc = Arc(
            lhyp.lhs,
            lhyp.before + (rhyp.lhs,),
            lhyp.after[1:],
            lhyp.start,
            rhyp.end,
            lhyp.prob*rhyp.prob)

    def __getattr__(self, name):
        return getattr(self.conc, name)

    def __cmp__(self, other):
        return all([
            self.lhyp == other.lhyp,
            self.rhyp == other.rhyp,
            self.conc == other.conc])

    def __add__(self, other):
        return DeductiveArc(self.conc, other.conc)

    def __hash__(self):
        return hash(
            (self.lhyp, self.rhyp, self.conc))

    def __unicode__(self):
        fmt = u"{c}  from  {l}, {r}"
        return fmt.format(
            c=unicode(self.conc),
            l=unicode(self.lhyp),
            r=unicode(self.rhyp))

    def __str__(self):
        return self.__unicode__().encode('utf-8')

    def _pretty_print(self, ln, typ, size=5):
        default = "." + " " * (size - 1)
        comp = "." + "=" * (size - 1)
        incomp = "." + "-" * (size - 2) + ">"
        incomp_not_finished = "." + "-" * (size - 1)
        slf = "." + ">" + " " * (size - 2)
        if not typ in ["comp", "incomp", "self"]:
            raise Exception()
        if typ == "self":
            s = default * self.start + slf + default * (ln - self.end - 1)
        elif typ == "comp":
            s = default * self.start + comp * (self.end - self.start) \
                + default * (ln - self.end)
        elif typ == "incomp":
            s = default * self.start + incomp_not_finished \
                * (self.end - self.start - 1) + incomp + default * \
                (ln - self.end)
        return s + "."

    def pretty_print(self, sent, size=10, verbose=False):
        if self.start == self.end:
            s = self._pretty_print(len(sent), "self", size)
        elif self.after:
            s = self._pretty_print(len(sent), "incomp", size)
        else:
            s = self._pretty_print(len(sent), "comp", size)

        fmt = u"{}  {}".format(s, unicode(self))
        return fmt

    def is_last(self):
        return True if self.start == -1 and self.end == -1 else False


class PredArc(DeductiveArc):
    def __init__(self, conc):
        arc = Arc("root", tuple([]), tuple([]), -1, -1, 1),
        self.lhyp = arc
        self.rhyp = arc
        self.conc = conc

    def __unicode__(self):
        fmt = u"{c}"
        return fmt.format(c=unicode(self.conc))

    def __str__(self):
        return self.__unicode__().encode('utf-8')


class ChartParser(object):
    def __init__(self, grammar):
        self._grammar = grammar

    def terminals(self, grammar):
        """Collect word_names which has a "N -> 'word_name'" shape from
        grammar."""
        re_obj = re.compile(ur"^'\S+'$")
        ret = set()
        for item in grammar:
            if len(item) == 3:
                if re_obj.search(item[1]):
                    ret.add(item)
        return ret

    def search(self, sent, verbose=False):

        adjenda = heapdict()
        # grammar dicts
        gr_right = defaultdict(list)
        for item in self._grammar:
            gr_right[item[1]].append(item)

        # initial arcs
        init_arcs = defaultdict(set)
        for lh, word, pr in self.terminals(self._grammar):
            init_arcs[word].add((lh, word, pr))

        # initialize
        pool = set([])
        for i, w in enumerate(sent):
            for lh, word, pr in init_arcs[w]:
                hyp1 = Arc(lh, tuple([]), tuple([word]), i, i, pr)
                hyp2 = Arc(word, tuple([]), tuple([]), i, i+1, 1)
                prob = hyp1.prob * hyp2.prob
                new_arc = hyp1 + hyp2
                adjenda[new_arc] = prob
                pool.add(new_arc)

        # initialize chart
        chart = defaultdict(set)
        chart_init = defaultdict(lambda: defaultdict(set))
        chart_after = defaultdict(lambda: defaultdict(set))

        # main loop
        while adjenda.items():
            arc, _ = adjenda.popitem()
            print arc.pretty_print(sent, size=10,
                                   verbose=verbose).encode('utf-8')
            # add to chart
            # Use set to remove deplicated items
            chart[(arc.start, arc.end)].add(arc)
            chart_init[arc.lhs][(arc.start, arc.end)].add(arc)

            if arc.after:
                chart_after[arc.after[0]][(arc.start, arc.end)].add(arc)

            # active edge
            if arc.after:
                y = arc.after[0]
                for (s, e), arcs in [((s, e), arcs) for
                                     (s, e), arcs in chart_init[y].items()
                                     if s == arc.end]:
                    for hyp in [hyp for hyp in arcs if not hyp.after]:
                        con = arc + hyp
                        if con not in pool:
                            adjenda[con] = arc.prob * hyp.prob
                            pool.add(con)
            else:
                for (s, e), arcs in [((s, e), arcs) for
                                     (s, e), arcs in
                                     chart_after[arc.lhs].items()
                                     if e == arc.start]:
                    for hyp in [hyp for hyp in arcs if hyp.after]:
                        con = hyp + arc
                        if con not in pool:
                            adjenda[con] = hyp.prob * arc.prob
                            pool.add(con)

            # recommend new arc
                if arc.lhs in gr_right:
                    for gr in gr_right[arc.lhs]:
                        predarc = PredArc(Arc(
                            gr[0],
                            tuple([]),
                            tuple(gr[1:][:-1]),
                            arc.start,
                            arc.start,
                            gr[-1]))
                        if predarc not in pool:
                            adjenda[predarc] = predarc.prob
                            pool.add(predarc)
        return chart

    def _find(self, arc, chart):
        return [item for item in chart[(arc.start, arc.end)]
                if item.conc == arc]

    def answer(self, chart, sent):
        return [arc for arc in chart[(0, len(sent))]]

    def print_answer(self, arc, sent):
        print u" ".join(sent).encode('utf-8')
        if arc.is_last():
            return
        print self._ans_format(arc, sent)
        self.print_answer(arc.hyp1, sent)
        self.print_answer(arc.hyp2, sent)

    def _ans_format(self, arc, sent):
        s = arc.start
        e = arc.end
        s_f = u" " * sum(map(len, sent[:s])) + u" "
        e_f = u" " + u" " * sum(map(len, sent[e:]))
        f_f = u"=" * sum(map(len, sent[s:e]))
        return s_f + f_f + e_f


def test_terminals():
    grammar = {("S", "NP", "VP", 0.5),
               ("S", "NP", "VP", "NP", 0.1),
               ("VP", "V", "NP", 0.5),
               ("NP", "N", 0.1),
               ("NP", "'kenkovtan'", 0.3),
               ("NP", "'Rikka'", 0.3),
               ("V", "'loves'", 0.4)}
    parser = ChartParser(grammar)
    assert parser.terminals(grammar) == {
        ('NP', "'kenkovtan'", 0.3),
        ('NP', "'Rikka'", 0.3),
        ('V', "'loves'", 0.4)}


def main():
    grammar = {("S", "NP", "VP", 2),
               ("S", "NP", "V", "NP", 5),
               ("VP", "V", "NP", 10),
               ("NP", u"'I'", 3),
               ("NP", u"'Rikka'", 3),
               ("V", u"'love'", 2)}
    parser = ChartParser(grammar)
    sent = ["".join(["'", w, "'"]) for w in u"I love Rikka".split()]
    res = parser.search(sent)
    print res
    grammar2 = {("NP", "NP", "NP", 2),
                ("NP", u"'I'", 3),
                ("NP", u"'Rikka'", 3)}
    parser2 = ChartParser(grammar2)
    sent2 = ["".join(["'", w, "'"]) for w in u"I Rikka".split()]
    res2 = parser2.search(sent2)
    print res2
    grammar2 = {("N", "N", "N", 2),
                ("N", u"'I'", 3),
                ("N", u"'am'", 3),
                ("N", u"'a'", 3),
                ("N", u"'teacher'", 3)}
    parser2 = ChartParser(grammar2)
    sent2 = ["".join(["'", w, "'"]) for w in u"I I I I I".split()]
    res2 = parser2.search(sent2)
    print res2


if __name__ == '__main__':
    test_terminals()
    main()
