import unittest
from tool.preprocess import *
from mjlegal.mjtypes import Tile, TilesUtil

class TestMjai(unittest.TestCase) :
    def test_DeltaScores(self) :
        self.assertEqual(DeltaScores([35000, 39000, 25000], 0).feature(),[0, 1, 4] )
    
    def test_Bakaze(self) :
        self.assertEqual(Bakaze("E").feature(), [0])
    
    def test_elems_to_nums(self) :
        self.assertEqual(elems_to_nums([Kyoku(1), Tile34("9m")]),[0,8])
    
    def test_elems_to_cumsum(self) :
        self.assertEqual(encode_elems([Kyoku(1), Tile34("1m")]),[0,3])
    
    def test_DoraMarkers(self) :
        tiles = ["1m", "2m", "C", "C"]
        self.assertEqual(DoraMarkers(TilesUtil.tiles_str_array_to_tiles(tiles)).feature(), encode_elems([Tile37(tile) for tile in tiles]))
    
    def test_Rank(self) :
        self.assertEqual(Rank([1000,2000,3000], 0).feature(), [2,1,0])
        self.assertEqual(Rank([1000,2000,3000], 1).feature(), [1,0,2])
        self.assertEqual(Rank([1000,2000,3000], 2).feature(), [0,2,1])