#!/usr/bin/env python3
"""Re-extract the three fully printed grids from the supplied PDF (Poppler)."""
import argparse
import csv
import re
import subprocess
from pathlib import Path


def extract(pdf,out):
    text=subprocess.check_output(['pdftotext','-layout',str(pdf),'-'],text=True)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    for n,filename,a,b in [(7,'217.csv','D','E'),(8,'288.csv','C','D'),(9,'369.csv','B','C')]:
        block=re.split(r'[\n\f]'+a+r'\s+The explicit',text)[1]
        block=re.split(r'[\n\f]'+b+r'\s+The explicit',block)[0]
        rows=[]
        for line in block.splitlines():
            t=line.split()
            if len(t)==n+1 and re.fullmatch('[1-9][1-9]',t[0]) and all(
                    x in ['•','◦'] or x.isdigit() for x in t[1:]):
                rows.append(['' if x=='•' else '.' if x=='◦' else x for x in t[1:]])
        if len(rows)!=n*(n-1)//2:raise ValueError(f'Could not extract all rows at n={n}')
        with (out/filename).open('w',newline='') as f:
            csv.writer(f,lineterminator='\n').writerows(rows)
        print(filename,len(rows),'rows')


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('pdf');ap.add_argument('out');args=ap.parse_args()
    extract(args.pdf,args.out)
