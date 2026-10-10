#!/usr/bin/env python3
"""Independent nested generators and deterministic seeded repair search.

These are newly constructed candidates, not recovered unpublished data.
The bipyramidal matching enumeration is explicitly given below. Labels
are inner cyclic indices 0,...,q-1 in the order the edges are appended.
"""
import argparse
import csv
import itertools
import json
import time
from pathlib import Path
import numpy as np
from certificate_checker import read_sheet,closure


def write_grid(path,grid):
    # Canonical pair renumbering by first occurrence, preserving supports.
    labelmap={}
    clean=[]
    for row in grid:
        out=[]
        for v in row:
            if v not in ('','.'):
                labelmap.setdefault(str(v),len(labelmap)+1)
                v=str(labelmap[str(v)])
            out.append(v)
        clean.append(out)
    with open(path,'w',newline='') as f:
        csv.writer(f,lineterminator='\n').writerows(clean)


def nested(q):
    assert q%2==1
    n=2*q
    edges=list(itertools.combinations(range(n),2)); rowid={e:i for i,e in enumerate(edges)}
    factors=[]
    # q matchings: an anchor cross-edge, reflection pairs in each copy.
    for a in range(q):
        f=[(a,a+q)]
        for t in range(1,(q+1)//2):
            f.append(tuple(sorted(((a+t)%q,(a-t)%q))))
            f.append(tuple(sorted(((a+t)%q+q,(a-t)%q+q))))
        factors.append(f)
    # q-1 matchings containing the nonzero cross shifts.
    for t in range(1,q): factors.append([(a,(a+t)%q+q) for a in range(q)])
    if q == 9:
        # K18 has the cyclic perfect factorization on Z17 union {infinity}.
        # The bipyramidal composite-q factors above would NOT be perfect.
        L=2*q-1
        factors=[]
        for a in range(L):
            factors.append([(a,L)]+[tuple(sorted(((a+x)%L,(a-x)%L)))
                                    for x in range(1,q)])
    assert sorted(e for f in factors for e in f)==edges
    grid=[['?' for _ in range(n)] for _ in edges]
    for i,(u,v) in enumerate(edges):grid[i][u]=grid[i][v]=''
    lab=0
    for factor in factors:
        for a,(u,v) in enumerate(factor):
            for x in range(1,(q+1)//2):
                i=rowid[factor[(a+x)%q]];k=rowid[factor[(a-x)%q]]
                for p,r in [((i,u),(k,v)),((i,v),(k,u))]:
                    assert grid[p[0]][p[1]]=='?' and grid[r[0]][r[1]]=='?'
                    lab+=1;grid[p[0]][p[1]]=grid[r[0]][r[1]]=str(lab)
    assert not any('?' in row for row in grid)
    return grid


def restrict(grid,keep):
    n=len(grid[0]);edge_rows=list(itertools.combinations(range(n),2))
    target=[[grid[i][j] for j in keep] for i,e in enumerate(edge_rows) if set(e)<=set(keep)]
    occurrences={}
    for p,v in enumerate(itertools.chain.from_iterable(target)):
        if v not in ('','.'):
            occurrences.setdefault(v,[]).append(p)
    inherited=[v for v in occurrences.values() if len(v)==2]
    orphan=[v[0] for v in occurrences.values() if len(v)==1]
    orphan.extend(p for p,v in enumerate(itertools.chain.from_iterable(target)) if v=='.')
    return target,inherited,orphan


def repair(parent,keep,path,seed=20261010,attempts=100,break_pairs=0,seconds=120,strategy='targeted'):
    rng=np.random.default_rng(seed)
    grid,inherited,free=restrict(parent,keep)
    n=len(keep);flat=list(itertools.chain.from_iterable(grid))
    outdir=Path(path).parent
    logfile=outdir.parent/'logs'/f'{Path(path).stem}_search.jsonl'
    start=time.perf_counter();best=None;best_score=None;targets=[]
    with open(logfile,'w') as log:
        log.write(json.dumps(dict(seed=seed,attempts=attempts,budget_seconds=seconds,
                                 target_n=n,keep_vertices_0based=keep,
                                 inherited=len(inherited),orphans=len(free),
                                 break_pairs=break_pairs,strategy=strategy))+'\n')
        for t in range(attempts):
            if t and time.perf_counter()-start>seconds:break
            work=flat.copy();pool=free.copy()
            if break_pairs:
                for k in rng.choice(len(inherited),break_pairs,replace=False):pool.extend(inherited[k])
            if best is None or t%20==0 or break_pairs:
                rng.shuffle(pool)
                pairing=pool.copy()
            else:
                pairing=best.copy()
                # Cross-switch endpoints among two to four pairs, preserving support.
                k=int(rng.integers(2, min(5,len(pairing)//2+1)))
                chosen=rng.choice(len(pairing)//2,k,replace=False)*2+rng.integers(0,2,k)
                if targets and strategy=='targeted':
                    chosen[0]=int(rng.choice(targets))
                    # Unique endpoints, with distinct pair blocks.
                    if len(set((chosen//2).tolist()))!=k:
                        continue
                vals=[pairing[x] for x in chosen]
                for i,x in enumerate(chosen):pairing[x]=vals[(i+1)%k]
            for k in range(0,len(pairing)-1,2):
                lab=f'new{k//2}';work[pairing[k]]=work[pairing[k+1]]=lab
            if len(pairing)%2:work[pairing[-1]]='.'
            candidate=[work[i*n:(i+1)*n] for i in range(len(grid))]
            write_grid(path,candidate)
            data=read_sheet(path)
            result,_,_=closure(data)
            score=(len(result['unresolved_pair_labels']),result['unresolved_pairs'])
            entry=dict(attempt=t,score=score,status=result['status'],
                       elapsed=time.perf_counter()-start,closure_seconds=result['seconds'])
            log.write(json.dumps(entry)+'\n');log.flush()
            if best_score is None or score<best_score or (strategy=='targeted' and score==best_score):
                improved=best_score is None or score<best_score
                best_score=score;best=pairing.copy();bestgrid=candidate
                badcells=set()
                for label in result['unresolved_pair_labels']:
                    badcells.update(map(int,data['pairs'][label-1]))
                if not badcells:
                    for a,b in result['unresolved_sample_edge_ids_0based']:
                        for edge in [a,b]:
                            badcells.update(np.flatnonzero(data['edge_id']==edge).tolist())
                targets=[i for i,p in enumerate(pairing) if p in badcells]
                if improved:print('IMPROVED',n,t,score,flush=True)
            if result['status']=='VERIFIED':
                print('VERIFIED',n,'attempt',t,flush=True);return result
    write_grid(path,bestgrid)
    result,_,_=closure(read_sheet(path))
    print('BUDGET ENDED',n,best_score,flush=True)
    return result


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--q',type=int)
    ap.add_argument('--parent')
    ap.add_argument('--n',type=int)
    ap.add_argument('--out',required=True)
    ap.add_argument('--attempts',type=int,default=100)
    ap.add_argument('--seconds',type=float,default=120)
    ap.add_argument('--seed',type=int,default=20261010)
    ap.add_argument('--break-pairs',type=int,default=0)
    ap.add_argument('--strategy',choices=['basic','targeted'],default='targeted')
    args=ap.parse_args()
    if args.q:
        parent=nested(args.q)
    else:
        parent=read_sheet(args.parent)['grid']
    if args.n is None:write_grid(args.out,parent)
    else:repair(parent,list(range(args.n)),args.out,args.seed,args.attempts,args.break_pairs,args.seconds,args.strategy)
