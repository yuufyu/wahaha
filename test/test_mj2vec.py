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

    # def test_mjai2vec_1(self) :
    #     filename = "test/test_data/2020010100gm-00b9-0000-7a6863a8.mjson"
    #     output_dir = "test/result"
    #     mj2vec = Mj2Vec()
    #     records = load_mjai_records(filename)
    #     mj2vec.process_records(records)
    #     mj2vec.save_to_text(output_dir)
    
