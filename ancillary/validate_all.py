#!/usr/bin/env python3
"""Re-run every exact closure and verify each saved finite proof."""
import hashlib
import json
from pathlib import Path
from certificate_checker import read_sheet,closure
from verify_certificate import verify


def main():
    base=Path(__file__).resolve().parent.parent
    provenance=json.loads((base/'ancillary'/'provenance.json').read_text())
    for item in provenance['instances']:
        stem=item['file'].removesuffix('.csv');sheet=base/'ancillary'/item['file']
        expected=json.loads((base/'logs'/(stem+'.json')).read_text())
        digest=hashlib.sha256(sheet.read_bytes()).hexdigest()
        if digest!=expected['sha256']:raise ValueError('CSV digest mismatch: '+stem)
        actual,_,_=closure(read_sheet(sheet))
        for key in ['status','E1','E2','H','R','occupied_equivalence_classes',
                    'identifications','orthogonality_pairs','unresolved_pairs','identification_rules']:
            if actual[key]!=expected[key]:raise ValueError(f'{stem}: mismatch at {key}')
        proof=verify(sheet,base/'logs'/(stem+'_certificate.npz'))
        (base/'logs'/(stem+'_certificate_verification.json')).write_text(
            json.dumps(proof,indent=2)+'\n')
        print(stem,actual['status'],proof['status'],digest,flush=True)
    print('ALL TEN VERIFIED')


if __name__=='__main__':main()
