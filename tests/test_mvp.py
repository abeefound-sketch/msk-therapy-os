import sqlite3
import unittest
from msk_therapy_os.__main__ import add_visit, init, seed_demo


class DemoTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.execute('PRAGMA foreign_keys=ON')
        init(self.db)
        seed_demo(self.db)

    def tearDown(self):
        self.db.close()

    def kwargs(self):
        return dict(case='DEMO-NECK-001', when='2026-10-19', pain=5, rom=40,
                    region='neck', flag='none', note='Fictional data')

    def test_demo_visit_saved(self):
        self.assertEqual(add_visit(self.db, **self.kwargs()), 'DOCUMENT_ONLY')
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM visits').fetchone()[0], 1)

    def test_red_flags_hard_stop_even_without_pain(self):
        for flag in ['progressive_weakness', 'bowel_bladder_change', 'saddle_numbness',
                     'fever_with_spinal_pain', 'major_trauma']:
            args = self.kwargs()
            args.update(flag=flag, pain=0)
            self.assertEqual(add_visit(self.db, **args), 'STOP_AND_REFER')

    def test_reject_real_identifier(self):
        args = self.kwargs()
        args['case'] = 'PERSON-001'
        with self.assertRaises(ValueError):
            add_visit(self.db, **args)

    def test_reject_invalid_pain(self):
        args = self.kwargs()
        args['pain'] = 11
        with self.assertRaises(ValueError):
            add_visit(self.db, **args)

    def test_reject_invalid_rom(self):
        args = self.kwargs()
        args['rom'] = 500
        with self.assertRaises(ValueError):
            add_visit(self.db, **args)

    def test_reject_invalid_date(self):
        args = self.kwargs()
        args['when'] = 'wrong-date'
        with self.assertRaises(ValueError):
            add_visit(self.db, **args)

    def test_reject_unknown_case(self):
        args = self.kwargs()
        args['case'] = 'DEMO-MISSING-404'
        with self.assertRaises(ValueError):
            add_visit(self.db, **args)

    def test_reject_unknown_flag(self):
        args = self.kwargs()
        args['flag'] = 'green'
        with self.assertRaises(ValueError):
            add_visit(self.db, **args)


if __name__ == '__main__':
    unittest.main()
