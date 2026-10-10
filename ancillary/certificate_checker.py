#!/usr/bin/env python3
"""Exact, unsigned Section 2.4 closure; standard library + NumPy only.

Empty CSV field: singleton, positive integer (twice): pair, '.': hole.
Row order must be lexicographic edges of K_n (vertices 1,...,n).
Equal printed labels are NOT identifications at initialization.
"""
import argparse
import csv
import hashlib
import itertools
import json
import time
from pathlib import Path
import numpy as np


class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x
    def union(self, x, y):
        x, y = self.find(x), self.find(y)
        if x != y:
            self.parent[max(x, y)] = min(x, y)


def read_sheet(path, require_incidence=True):
    with open(path, newline='') as f:
        grid = list(csv.reader(f))
    m, n = len(grid), len(grid[0])
    if any(len(row) != n for row in grid):
        raise ValueError('Ragged CSV')
    N = m*n
    singles, holes, labels = [], [], {}
    for p, field in enumerate(itertools.chain.from_iterable(grid)):
        if field == '':
            singles.append(p)
        elif field == '.':
            holes.append(p)
        elif field.isdigit() and int(field) > 0:
            labels.setdefault(int(field), []).append(p)
        else:
            raise ValueError(f'Invalid cell token at {divmod(p,n)}: {field!r}')
    if sorted(labels) != list(range(1, len(labels)+1)):
        raise ValueError('Pair labels must be 1,...,E2')
    if any(len(v) != 2 for v in labels.values()):
        raise ValueError('Every pair label must occur exactly twice')
    pairs = np.array(list(labels.values()), dtype=np.int32).reshape(-1, 2)
    # Pair-of-columns count audits C4-freeness independently of row names.
    seen = set()
    for row in grid:
        cols = [j for j, v in enumerate(row) if v == '']
        for cp in itertools.combinations(cols, 2):
            if cp in seen:
                raise ValueError('Singleton graph contains a C4')
            seen.add(cp)
    limited = None
    if require_incidence:
        if m != n*(n-1)//2:
            raise ValueError('Not an incidence-family dimension')
        for i, edge in enumerate(itertools.combinations(range(n), 2)):
            if tuple(j for j, v in enumerate(grid[i]) if v == '') != edge:
                raise ValueError(f'Row {i+1} is not the incidence row {edge}')
        # r <= binom(r,2)+1 for each nonempty row proves z<=m+binom(n,2).
        limited = len(singles) == 2*m
    occupied = np.ones(N, dtype=bool)
    occupied[holes] = False
    partner = np.arange(N, dtype=np.int32)
    if len(pairs):
        partner[pairs[:,0]] = pairs[:,1]
        partner[pairs[:,1]] = pairs[:,0]
    edge_id = np.full(N, -1, dtype=np.int32)
    reps = []
    for p in singles:
        edge_id[p] = len(reps); reps.append(p)
    for p, q in pairs:
        edge_id[[p,q]] = len(reps); reps.append(int(p))
    return dict(grid=grid, m=m, n=n, N=N, singles=singles, holes=holes,
                pairs=pairs, occupied=occupied, partner=partner,
                edge_id=edge_id, reps=np.array(reps), limited=limited)


def closure(data, holes_enabled=True, trace_path=None):
    start = time.perf_counter()
    m,n,N = data['m'],data['n'],data['N']
    pairs, occ = data['pairs'],data['occupied']
    rows = np.arange(N)//n; cols = np.arange(N)%n
    genuine = (rows[:,None] != rows) & (cols[:,None] != cols)
    active = occ[:,None] & occ
    delta = np.zeros((N,N), dtype=bool)
    if len(pairs):
        delta[pairs[:,0],pairs[:,1]] = True
        delta[pairs[:,1],pairs[:,0]] = True
    same_line = (rows[:,None] == rows) | (cols[:,None] == cols)
    ortho = same_line & active & ~delta
    np.fill_diagonal(ortho, False)
    equal = np.eye(N, dtype=bool) & active
    uf = UnionFind(N)
    merged = np.zeros(len(pairs), dtype=bool)
    counts = dict(line=0, complementary=0, zero_companion=0, transfer=0)
    orth_counts=dict(line=int(ortho.sum())//2,complementary=0,
                     zero_companion=0,saturation=0,transfer=0)
    trace = []

    def merge(mask, reason):
        fresh = mask & ~merged
        indices = np.flatnonzero(fresh)
        for k in indices:
            p,q = map(int,pairs[k])
            if ortho[p,q]:
                raise ValueError('Identification/orthogonality conflict')
            uf.union(p,q)
            equal[p,q] = equal[q,p] = True
        merged[fresh] = True
        counts[reason] += len(indices)
        return indices

    if len(pairs):
        merge(same_line[pairs[:,0],pairs[:,1]], 'line')
        companion_delta = delta.reshape(m,n,m,n).transpose(0,3,2,1).reshape(N,N)
        merge(companion_delta[pairs[:,0],pairs[:,1]] &
              genuine[pairs[:,0],pairs[:,1]], 'complementary')
    # All orthogonality remains in a separate store; no signed odd-cycle rule.
    initial_equal = equal.copy()
    initial_ortho = ortho.copy()
    if holes_enabled:
        orth_before_zero=int(ortho.sum())
        zero = np.zeros((N,N), dtype=bool)
        zero[data['holes'],:] = True; zero[:,data['holes']] = True
        zero = zero.reshape(m,n,m,n).transpose(0,3,2,1).reshape(N,N)
        zero &= genuine & active
        ortho |= zero & ~delta
        if len(pairs):
            merge(zero[pairs[:,0],pairs[:,1]], 'zero_companion')
        orth_counts['zero_companion']=(int(ortho.sum())-orth_before_zero)//2
    zero_equal = equal.copy()
    zero_ortho = ortho.copy()
    iterations = 0
    while True:
        iterations += 1
        before = int(ortho.sum()) + int(merged.sum())
        # Saturation under the current Union-Find classes (size <=2).
        roots = np.array([uf.find(p) for p in range(N)],dtype=np.int32)
        cp = np.arange(N,dtype=np.int32)
        for k in np.flatnonzero(merged):
            p,q = pairs[k]; cp[p],cp[q] = q,p
        ortho |= ortho[cp,:]
        ortho |= ortho[:,cp]
        orth_after_saturation=int(ortho.sum())
        orth_counts['saturation']+=(orth_after_saturation-(before-int(merged.sum())))//2
        if np.any(ortho & equal):
            raise ValueError('Saturation produced a conflict')
        known = ortho | equal
        companion = known.reshape(m,n,m,n).transpose(0,3,2,1).reshape(N,N)
        transfer = companion & genuine & active
        ortho |= transfer & ~delta
        orth_counts['transfer']+=(int(ortho.sum())-orth_after_saturation)//2
        new_merge = (merge(transfer[pairs[:,0],pairs[:,1]], 'transfer')
                     if len(pairs) else np.empty(0,dtype=int))
        after = int(ortho.sum()) + int(merged.sum())
        if trace_path:
            # A finite synchronous proof: store each round's orthogonality
            # store and all inferred identifications. Verifier checks each
            # new fact against previous-round premises, never its own conclusion.
            trace.append((np.packbits(ortho,axis=None),new_merge.copy()))
        if after == before:
            break
    # Independent terminal audit from the computed stores, not target counts.
    reps = data['reps']; R=len(reps)
    roots = [uf.find(int(p)) for p in reps]
    distinct = len(set(roots)) == R
    quotient_ortho = ortho[np.ix_(reps,reps)]
    certified = int(np.triu(quotient_ortho,1).sum())
    target = R*(R-1)//2
    unresolved = [(int(a),int(b)) for a,b in
                  zip(*np.where(np.triu(~quotient_ortho,1)))][:100]
    ok = bool(merged.all() and distinct and certified == target)
    result = dict(m=m,n=n,E1=len(data['singles']),E2=len(pairs),H=len(data['holes']),
                  R=R,Z=n*(n-1)*(n+2)//4,limited=data['limited'],
                  status='VERIFIED' if ok else 'UNVERIFIED',
                  all_pairs_identified=bool(merged.all()),
                  selected_classes_distinct=distinct,
                  occupied_equivalence_classes=len(set(uf.find(int(p)) for p in np.flatnonzero(occ))),
                  identifications=int(merged.sum()),orthogonality_pairs=certified,
                  unresolved_pairs=target-certified,
                  unresolved_sample_edge_ids_0based=unresolved,
                  unresolved_pair_labels=(np.flatnonzero(~merged)+1).tolist(),
                  identification_rules=counts,iterations=iterations,
                  orthogonality_cell_facts_by_rule=orth_counts,
                  orthogonality_cell_facts=int(ortho.sum())//2,
                  hole_rectangles=len(data['holes'])*(m-1)*(n-1),
                  holes_enabled=holes_enabled,conflict=False,
                  seconds=time.perf_counter()-start)
    if trace_path:
        payload = dict(shape=np.array([m,n]),
                       holes_enabled=np.array(holes_enabled),
                       initial_equal=np.packbits(initial_equal),
                       initial_ortho=np.packbits(initial_ortho),
                       zero_equal=np.packbits(zero_equal),
                       zero_ortho=np.packbits(zero_ortho))
        for i,(bits,merges) in enumerate(trace):
            payload[f'orth_{i}']=bits
            payload[f'merges_{i}']=merges
        temporary=Path(trace_path).with_suffix('.tmp.npz')
        np.savez_compressed(temporary, **payload)
        temporary.replace(trace_path)
    return result, ortho, equal


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('sheet',type=Path)
    ap.add_argument('--no-holes',action='store_true')
    ap.add_argument('--json',type=Path)
    ap.add_argument('--certificate',type=Path)
    args=ap.parse_args()
    d=read_sheet(args.sheet)
    result,_,_=closure(d, not args.no_holes,args.certificate)
    result['file']=args.sheet.name
    result['sha256']=hashlib.sha256(args.sheet.read_bytes()).hexdigest()
    output=json.dumps(result,indent=2)
    if args.json:
        args.json.write_text(output+'\n')
    print(output)
    return 0 if result['status']=='VERIFIED' else 1


if __name__=='__main__':
    raise SystemExit(main())
