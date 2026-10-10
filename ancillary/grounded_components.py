#!/usr/bin/env python3
"""Section 2.5 quotient-graph audit, after legal pair identification.

This is diagnostic, NOT a replacement for the identification prefix.
"""
import argparse
import itertools
import json
from collections import Counter
from certificate_checker import read_sheet,closure,UnionFind


def audit(path,holes=True):
    d=read_sheet(path)
    result,_,_=closure(d,holes)
    assert result['all_pairs_identified']
    m,n=d['m'],d['n'];R=len(d['reps']);V=R*(R-1)//2
    uf=UnionFind(V);ground=set();hole_ground=set()
    edge=d['edge_id']
    def variable(p,q):
        a,b=int(edge[p]),int(edge[q])
        if min(a,b)<0 or a==b:return None
        a,b=sorted((a,b));return b*(b-1)//2+a
    for i in range(m):
        for j,l in itertools.combinations(range(n),2):
            v=variable(i*n+j,i*n+l)
            if v is not None:ground.add(v)
    for j in range(n):
        for i,k in itertools.combinations(range(m),2):
            v=variable(i*n+j,k*n+j)
            if v is not None:ground.add(v)
    for i,k in itertools.combinations(range(m),2):
        for j,l in itertools.combinations(range(n),2):
            p,q,r,s=i*n+j,k*n+l,i*n+l,k*n+j
            A,B=variable(p,q),variable(r,s)
            holed=min(edge[p],edge[q],edge[r],edge[s])<0
            if holed and not holes:continue
            if A is not None and B is not None:uf.union(A,B)
            elif A is not None:
                ground.add(A)
                if holed:hole_ground.add(A)
            elif B is not None:
                ground.add(B)
                if holed:hole_ground.add(B)
    size=Counter(uf.find(v) for v in range(V))
    rooted={uf.find(v) for v in ground}
    ungrounded=[s for r,s in size.items() if r not in rooted]
    return dict(variables=V,components=len(size),grounded_components=len(rooted),
                ungrounded_components=len(ungrounded),
                ungrounded_size_histogram=dict(Counter(ungrounded)),
                ungrounded_variables=sum(ungrounded),holes_enabled=holes,
                components_with_direct_hole_ground=len({uf.find(v) for v in hole_ground}))


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('sheet');ap.add_argument('--no-holes',action='store_true')
    args=ap.parse_args();print(json.dumps(audit(args.sheet,not args.no_holes),indent=2))
