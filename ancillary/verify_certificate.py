#!/usr/bin/env python3
"""Verify finite synchronous proofs without invoking closure().

This deliberately checks rectangle premises by enumerating row/column pairs,
rather than by the tensor transposition used in certificate_checker.py.
"""
import argparse
import itertools
import json
import numpy as np
from certificate_checker import read_sheet


def require(condition,message='Invalid certificate'):
    if not condition:
        raise ValueError(message)


def verify(sheet, proof):
    d=read_sheet(sheet); N,n,m=d['N'],d['n'],d['m']
    z=np.load(proof,allow_pickle=False)
    require(list(z['shape'])==[m,n],'Wrong grid dimension')
    enabled=bool(z['holes_enabled'])
    def unpack(name):
        return np.unpackbits(z[name],count=N*N).reshape(N,N).astype(bool)
    occ=d['occupied']; active=occ[:,None]&occ
    pairs=d['pairs']; delta=np.zeros((N,N),dtype=bool)
    delta[pairs[:,0],pairs[:,1]]=True; delta[pairs[:,1],pairs[:,0]]=True
    E=np.eye(N,dtype=bool)&active; O=np.zeros((N,N),dtype=bool)
    rows=np.arange(N)//n; cols=np.arange(N)%n
    line=((rows[:,None]==rows)|(cols[:,None]==cols))&active
    O=line&~delta; np.fill_diagonal(O,False)
    E|=line&delta
    # Different algorithmic indexing for each rectangle's diagonals.
    rr=np.array(list(itertools.combinations(range(m),2)),dtype=np.int32)
    cc=np.array(list(itertools.combinations(range(n),2)),dtype=np.int32)
    p=(rr[:,0,None]*n+cc[:,0]).ravel()
    q=(rr[:,1,None]*n+cc[:,1]).ravel()
    r=(rr[:,0,None]*n+cc[:,1]).ravel()
    s=(rr[:,1,None]*n+cc[:,0]).ravel()
    both=delta[p,q]&delta[r,s]
    for a,b in [(p[both],q[both]),(r[both],s[both])]: E[a,b]=E[b,a]=True
    require(np.array_equal(E,unpack('initial_equal')),'Invalid initial equality')
    require(np.array_equal(O,unpack('initial_ortho')),'Invalid initial orthogonality')
    if enabled:
        for a,b,c,e in [(p,q,r,s),(r,s,p,q)]:
            grounded=(~occ[c]|~occ[e])&occ[a]&occ[b]
            a,b=a[grounded],b[grounded]
            one=delta[a,b]
            E[a[one],b[one]]=E[b[one],a[one]]=True
            O[a[~one],b[~one]]=O[b[~one],a[~one]]=True
    require(np.array_equal(E,unpack('zero_equal')),'Invalid zero-companion equality')
    require(np.array_equal(O,unpack('zero_ortho')),'Invalid zero-companion orthogonality')
    rounds=0
    while f'orth_{rounds}' in z:
        cp=np.arange(N)
        identified=E[pairs[:,0],pairs[:,1]]
        for a,b in pairs[identified]:cp[a],cp[b]=b,a
        # Exact relational saturation over both representatives at once.
        saturated=O|O[cp,:]|O[:,cp]|O[np.ix_(cp,cp)]
        known=saturated|E
        expected=saturated.copy(); allowed_merges=set()
        for a,b,c,e in [(p,q,r,s),(r,s,p,q)]:
            ground=known[c,e]
            if enabled:ground|=~occ[c]|~occ[e]
            take=ground&occ[a]&occ[b]
            a,b=a[take],b[take]; one=delta[a,b]
            expected[a[~one],b[~one]]=expected[b[~one],a[~one]]=True
            allowed_merges.update(zip(a[one].tolist(),b[one].tolist()))
        # The fast checker handles holes only in the zero initialization.
        # Here repeated hole conclusions are valid but already present.
        claimed=unpack(f'orth_{rounds}')
        require(np.array_equal(claimed,expected),f'Invalid orthogonality round {rounds}')
        claimed_merges=z[f'merges_{rounds}']
        actual=[]
        for k,(a,b) in enumerate(pairs):
            if not E[a,b] and ((int(a),int(b)) in allowed_merges or
                               (int(b),int(a)) in allowed_merges): actual.append(k)
        require(list(claimed_merges)==actual,f'Invalid merge round {rounds}')
        for k in actual:
            a,b=pairs[k];E[a,b]=E[b,a]=True
        O=claimed
        require(not np.any(O&E),'Equality/orthogonality conflict')
        rounds+=1
    # Check terminal conditions directly from stores. A partial trace is
    # rejected unless all requested classes are pairwise orthogonal.
    require(np.all(E[pairs[:,0],pairs[:,1]]),'Unidentified selected pair')
    reps=d['reps'];Q=O[np.ix_(reps,reps)]
    require(np.all(Q|np.eye(len(reps),dtype=bool)),'Uncertified orthogonality')
    require(not np.any(E[np.ix_(reps,reps)]&~np.eye(len(reps),dtype=bool)),
            'Distinct selected edges identified')
    # Independently audit fixed-point closure, as well as an accepting proof.
    cp=d['partner']
    saturated=O|O[cp,:]|O[:,cp]|O[np.ix_(cp,cp)]
    require(np.array_equal(O,saturated),'Missing saturation conclusion at fixed point')
    known=O|E
    for a,b,c,e in [(p,q,r,s),(r,s,p,q)]:
        premises=known[c,e]
        if enabled:premises|=~occ[c]|~occ[e]
        take=premises&occ[a]&occ[b]
        require(np.all(known[a[take],b[take]]),
                'Missing rectangle conclusion at fixed point')
    return dict(status='CERTIFICATE_VERIFIED',rounds=rounds,
                selected_classes=len(reps),orthogonality_pairs=len(reps)*(len(reps)-1)//2,
                fixed_point_closed=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('sheet');ap.add_argument('proof');args=ap.parse_args()
    print(json.dumps(verify(args.sheet,args.proof),indent=2))
