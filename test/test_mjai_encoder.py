import unittest
from features.mjai_encoder import *
# from mjlegal.mjtypes import Tile, TilesUtil

class TestMjai(unittest.TestCase) :
    def test_Elem_offset(self) :
        # self.assertEqual(GameStateElem.offset, 3)
        self.assertEqual(BeginRecordElem.offset, 403)
        self.assertEqual(RecordElem.offset, 404)
        self.assertEqual(PossibleActionElem.offset, 1049)

        self.assertEqual(TOKEN_VOCAB_COUNT, 1268)
        self.assertEqual(MAX_TOKEN_LENGTH, 145)

    def test_DeltaScores(self) :
        self.assertEqual(DeltaScores([35000, 36000, 34000], 0).feature(),[212, 221])
        self.assertEqual(DeltaScores([35000, 39000, 25000], 0).feature(),[213, 225])
    
    def test_Bakaze(self) :
        self.assertEqual(Bakaze("E").feature(), [8])
        
    def test_DoraMarkers(self) :
        tiles = ["1m", "2m", "C", "C"]
        self.assertEqual(DoraMarkers(TilesUtil.tiles_str_array_to_tiles(tiles)).feature(), [22, 60, 131, 168])
    
    def test_Rank(self) :
        self.assertEqual(Rank().get_rel_rank([1000,2000,3000], 0), [2,1,0])
        self.assertEqual(Rank().get_rel_rank([1000,2000,3000], 1), [1,0,2])
        self.assertEqual(Rank().get_rel_rank([1000,2000,3000], 2), [0,2,1])

        self.assertEqual(Rank([1000,2000,3000], 0).feature(), [211])
        self.assertEqual(Rank([1000,2000,3000], 1).feature(), [208])
        self.assertEqual(Rank([1000,2000,3000], 2).feature(), [207])

    def test_Action(self) :
        mjai = {"type" : "dahai", "pai" : "0m", "tsumogiri" : False}
        self.assertEqual(Action(mjai).feature(), [0])

        mjai = {'type': 'pon', 'actor': 0, 'target': 1, 'pai': '0m', 'consumed': ['5m', '5m']}
        self.assertEqual(Action(mjai).feature(), [75])

        mjai = {'type': 'pon', 'actor': 0, 'target': 1, 'pai': '5m', 'consumed': ['5m', '5m']}
        self.assertEqual(Action(mjai).feature(), [80])

        mjai = {'type': 'dahai', 'actor': 2, 'pai': '5p', 'tsumogiri': True}
        self.assertEqual(Action(mjai).feature(), [52])

        mjai = {'type': 'dahai', 'actor': 2, 'pai': 'E', 'tsumogiri': False}
        self.assertEqual(Action(mjai).feature(), [30])

