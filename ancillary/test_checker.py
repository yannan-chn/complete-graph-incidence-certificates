#!/usr/bin/env python3
"""Tests of rule soundness, negative outcomes, random cross-checks and proof tampering."""
import csv
import itertools
import tempfile
import unittest
from pathlib import Path
import numpy as np
from certificate_checker import read_sheet,closure
from reference_checker import reference_closure
from verify_certificate import verify


def custom(grid):
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'test.csv'
        with p.open('w',newline='') as f:csv.writer(f).writerows(grid)
        return read_sheet(p,require_incidence=False)


class Tests(unittest.TestCase):
    def test_hole_opposite_selected_pair_identifies(self):
        d=custom([['.','1'],['1','']])
        r,O,E=closure(d)
        self.assertTrue(E[1,2]);self.assertFalse(O[1,2])
        self.assertEqual(r['identification_rules']['zero_companion'],1)
        _,O2,E2=closure(d,False)
        self.assertFalse(E2[1,2])

    def test_hole_opposite_unselected_pair_orthogonal(self):
        d=custom([['.',''],['','.']])
        _,O,E=closure(d)
        self.assertTrue(O[1,2]);self.assertFalse(E[1,2])

    def test_complementary_pair(self):
        d=custom([['1','2'],['2','1']])
        r,O,E=closure(d)
        self.assertEqual(r['identification_rules']['complementary'],2)
        self.assertEqual(r['status'],'VERIFIED')

    def test_labels_not_initial_equivalence(self):
        # A diagonal pair with no grounded companion must remain unresolved.
        d=custom([['1','.'],['.','1']])
        r,_,E=closure(d,False)
        self.assertFalse(E[0,3]);self.assertEqual(r['status'],'UNVERIFIED')

    def test_line_pair(self):
        r,_,E=closure(custom([['1','1']]))
        self.assertTrue(E[0,1]);self.assertEqual(r['identification_rules']['line'],1)

    def test_invalid_labels_and_C4(self):
        for g in [[['1','']], [['','',''],['','','.']], [['x']]]:
            with self.assertRaises(ValueError):custom(g)

    def test_random_reference(self):
        rng=np.random.default_rng(90210)
        for t in range(80):
            cells=list(rng.permutation(9));g=['.']*9
            # no singleton here: avoids accidentally C4 singleton skeletons.
            k=int(rng.integers(1,5))
            for j in range(k):g[cells[2*j]]=g[cells[2*j+1]]=str(j+1)
            d=custom([g[0:3],g[3:6],g[6:9]])
            for holes in (False,True):
                _,O,E=closure(d,holes)
                Or,Er=reference_closure(d,holes)
                self.assertTrue(np.array_equal(O,Or),(t,holes))
                self.assertTrue(np.array_equal(E,Er),(t,holes))

    def test_three_printed_grids_reference(self):
        for name in ['217','288','369']:
            d=read_sheet(Path(__file__).parent/(name+'.csv'))
            _,O,E=closure(d);Or,Er=reference_closure(d)
            self.assertTrue(np.array_equal(O,Or))
            self.assertTrue(np.array_equal(E,Er))

    def test_certificate_tampering_rejected(self):
        sheet=Path(__file__).parent/'217.csv'
        with tempfile.TemporaryDirectory() as td:
            proof=Path(td)/'proof.npz'
            closure(read_sheet(sheet),trace_path=proof)
            self.assertEqual(verify(sheet,proof)['status'],'CERTIFICATE_VERIFIED')
            with np.load(proof) as z:bad={k:z[k] for k in z.files}
            bad['orth_0']=bad['orth_0'].copy();bad['orth_0'][0]^=1
            np.savez_compressed(proof,**bad)
            with self.assertRaises(ValueError):verify(sheet,proof)


if __name__=='__main__':unittest.main(verbosity=2)
