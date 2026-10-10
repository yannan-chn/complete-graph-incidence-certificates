#!/usr/bin/env python3
"""Slow independent set-based implementation for small instances and tests."""
import itertools
import numpy as np
from certificate_checker import read_sheet


def reference_closure(d, holes_enabled=True):
    n,m,N=d['n'],d['m'],d['N']
    occupied=set(np.flatnonzero(d['occupied']).tolist())
    selected={frozenset(map(int,p)) for p in d['pairs']}
    eq={p:{p} for p in occupied}
    orth=set()
    def value(p,q):
        if p not in occupied or q not in occupied:
            return 0 if holes_enabled else None
        if q in eq[p]: return 1
        if frozenset((p,q)) in orth: return 0
        return None
    def infer(p,q):
        if p not in occupied or q not in occupied: return
        if frozenset((p,q)) in selected:
            group=eq[p]|eq[q]
            for x in group: eq[x]=group
        else:
            orth.add(frozenset((p,q)))
    for p,q in itertools.combinations(occupied,2):
        if p//n==q//n or p%n==q%n: infer(p,q)
    rects=[]
    for i,k in itertools.combinations(range(m),2):
        for j,l in itertools.combinations(range(n),2):
            p,q,r,s=i*n+j,k*n+l,i*n+l,k*n+j
            rects.append((p,q,r,s))
            if frozenset((p,q)) in selected and frozenset((r,s)) in selected:
                infer(p,q); infer(r,s)
    while True:
        before=len(orth)+sum(len(x) for x in eq.values())
        for pair in list(orth):
            p,q=tuple(pair)
            for a in eq[p]:
                for b in eq[q]:
                    if a==b: raise AssertionError('Conflict')
                    orth.add(frozenset((a,b)))
        for p,q,r,s in rects:
            if value(r,s)==int(frozenset((r,s)) in selected): infer(p,q)
            if value(p,q)==int(frozenset((p,q)) in selected): infer(r,s)
        if before==len(orth)+sum(len(x) for x in eq.values()): break
    O=np.zeros((N,N),dtype=bool); E=np.zeros((N,N),dtype=bool)
    for p,g in eq.items():
        for q in g: E[p,q]=True
    for pair in orth:
        p,q=tuple(pair); O[p,q]=O[q,p]=True
    return O,E


if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('sheet'); args=ap.parse_args()
    from certificate_checker import closure
    d=read_sheet(args.sheet)
    O,E=reference_closure(d)
    result,Of,Ef=closure(d)
    assert np.array_equal(O,Of) and np.array_equal(E,Ef)
    print(args.sheet, 'REFERENCE AGREES',result['status'])
