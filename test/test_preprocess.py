import unittest
from tool.preprocess import *
from mjlegal.mjtypes import Tile, TilesUtil

class TestMjai(unittest.TestCase) :
    def test_DeltaScores(self) :
        self.assertEqual(DeltaScores([35000, 39000, 25000], 0).feature(),[210,213] )
    
    def test_Bakaze(self) :
        self.assertEqual(Bakaze("E").feature(), [15])
        
    def test_DoraMarkers(self) :
        tiles = ["1m", "2m", "C", "C"]
        self.assertEqual(DoraMarkers(TilesUtil.tiles_str_array_to_tiles(tiles)).feature(), [19, 57, 128, 165])
    
    def test_Rank(self) :
        self.assertEqual(Rank().get_rel_rank([1000,2000,3000], 0), [2,1,0])
        self.assertEqual(Rank().get_rel_rank([1000,2000,3000], 1), [1,0,2])
        self.assertEqual(Rank().get_rel_rank([1000,2000,3000], 2), [0,2,1])

        self.assertEqual(Rank([1000,2000,3000], 0).feature(), [208])
        self.assertEqual(Rank([1000,2000,3000], 1).feature(), [205])
        self.assertEqual(Rank([1000,2000,3000], 2).feature(), [204])

    def test_Action(self) :
        mjai = {"type" : "dahai", "pai" : "0m", "tsumogiri" : False}
        self.assertEqual(Action(mjai).feature(), [0])

        mjai = {'type': 'pon', 'actor': 0, 'target': 1, 'pai': '0m', 'consumed': ['5m', '5m']}
        self.assertEqual(Action(mjai).feature(), [75])

        mjai = {'type': 'pon', 'actor': 0, 'target': 1, 'pai': '5m', 'consumed': ['5m', '5m']}
        self.assertEqual(Action(mjai).feature(), [80])
