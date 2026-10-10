#!/usr/bin/env python3
"""Rebuild seven searched grids in dependency order into a fresh directory.

No time budget is used for replay: the recorded attempt cap makes the
deterministic search independent of machine speed. The original run did
have a wall-clock budget, recorded in its logs.
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
from reconstruct import nested,repair,write_grid


def regenerate(out):
    out=Path(out)
    if out.exists():raise ValueError('Choose a new directory to preserve existing evidence')
    a=out/'ancillary';a.mkdir(parents=True);(out/'logs').mkdir()
    source=Path(__file__).parent
    for stem in ['217','288','369']:
        shutil.copy2(source/(stem+'.csv'),a/(stem+'.csv'))
    tasks=[(13,7,None,300,'basic'),(12,None,'7813',500,'basic'),
           (16,9,None,600,'targeted'),(17,9,None,600,'targeted'),
           (18,11,None,600,'targeted'),(20,11,None,600,'targeted'),
           (21,11,None,600,'targeted')]
    rows=[]
    for n,q,parent,attempts,strategy in tasks:
        stem=f'{n*(n-1)//2}{n}'
        if q is not None:grid=nested(q)
        else:
            from certificate_checker import read_sheet
            grid=read_sheet(a/(parent+'.csv'))['grid']
        result=repair(grid,list(range(n)),a/(stem+'.csv'),20261010,
                      attempts,0,float('inf'),strategy)
        expected=hashlib.sha256((source/(stem+'.csv')).read_bytes()).hexdigest()
        actual=hashlib.sha256((a/(stem+'.csv')).read_bytes()).hexdigest()
        if actual!=expected or result['status']!='VERIFIED':
            raise ValueError(f'{stem}: reconstruction does not reproduce the saved grid')
        rows.append(dict(file=stem+'.csv',status=result['status'],sha256=actual,
                         original_bytes_reproduced=True))
    (out/'logs'/'reproduction.json').write_text(json.dumps(rows,indent=2)+'\n')
    print('ALL SEVEN SEARCHED GRIDS REPRODUCED BYTE FOR BYTE')


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output');args=ap.parse_args();regenerate(args.output)
