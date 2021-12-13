import unittest
from features.mj2vec import *

class TestMjai(unittest.TestCase) :
    def test_mjai_tile(self) :
        self.assertEqual(mjai_pai_to_tile37("1m"), 1)
        self.assertEqual(mjai_pai_to_tile37("5m"), 5)
        self.assertEqual(mjai_pai_to_tile37("5mr"), 0)
        self.assertEqual(mjai_pai_to_tile34("1m"), 0)
        self.assertEqual(mjai_pai_to_tile34("5m"), 4)
        self.assertEqual(mjai_pai_to_tile34("5mr"), 4)