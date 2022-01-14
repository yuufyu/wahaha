import unittest
# from features.simple_encoder import *
# from mjlegal.mjtypes import Tile, TilesUtil

class TestSimpleEncoder(unittest.TestCase) :
    def test_Elem_offset(self) :
        
        def delta_score(player_score, other_score) :
            DELTA_SCORE_MAX = 48
            delta = int((other_score - player_score) / 1000)
            if delta > 0:
                k = min(DELTA_SCORE_MAX, delta) + DELTA_SCORE_MAX
            else :
                k = max(-1 * DELTA_SCORE_MAX, delta) + DELTA_SCORE_MAX

            print(f"{k} : {player_score} {other_score}")
            return k
        
        delta_score(0,99999)
        delta_score(0,-99999)
        delta_score(0,48000)
        delta_score(0,-48000)
        delta_score(0,0)
        delta_score(0,1000)
        delta_score(0,-1000)
        # self.assertEqual(GameStateElem.offset, 3)
        # self.assertEqual(BeginRecordElem.offset, 403)
        # self.assertEqual(RecordElem.offset, 404)
        # self.assertEqual(PossibleActionElem.offset, 1049)

        # self.assertEqual(TOKEN_VOCAB_COUNT, 1268)
        # self.assertEqual(MAX_TOKEN_LENGTH, 145)
