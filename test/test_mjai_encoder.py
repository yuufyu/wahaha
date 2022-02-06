import unittest
from features.mjai_encoder import *
from mjlegal.mjtypes import Tile
from tool.preprocess import fix_records

def test_encode_record(records, player_id) :
    client = MjaiEncoderClient()
    for record in records :
        client.update(record) 
    return client.encode(player_id)
    
class TestSimpleEncoder(unittest.TestCase) :
    def test_next_record(self) :
        records = [ 
            {"type":"dora","dora_marker":"6s"},
            {"type":"tsumo","actor":1,"pai":"6p"},
            {"type":"dora","dora_marker":"1p"},
            {"type":"dahai","actor":1,"pai":"6p","tsumogiri":False},
            {"type":"tsumo","actor":2,"pai":"1s"},
            {"type":"pon","actor":0,"target":2,"pai":"S","consumed":["S","S"]}
        ]
        i = 2
        next_record = next((r for r in records[i + 1:] if r["type"] in ("pon", "daiminkan", "hora")), None)
        expect = {"type":"pon","actor":0,"target":2,"pai":"S","consumed":["S","S"]}
        self.assertEqual(next_record, expect)

    def test_mjai_encoder_client(self) :
        input_records = [ # tonpu
            {"type":"start_game","names":["x","x","x"],"uri":"http://tenhou.net/0/?log=2000080000gm-00b1-0000-6b000000&tw=0"},
            {"type":"start_kyoku","bakaze":"E","kyoku":1,"honba":0,"kyotaku":0,"oya":0,"dora_marker":"0m","tehais":[["1m","2p","4p","5p","4s","7s","E","E","S","N","P","P","F"],["4p","7p","9p","1s","3s","6s","8s","W","N","F","F","C","C"],["1p","2p","3p","6p","6p","8p","9p","1s","2s","3s","5s","9s","E"]]},
            {"type":"tsumo","actor":0,"pai":"2p"}
        ]
        input_player_id = 0
        expected =  [1, 6, 8, 11, 14, 17, 21, 72, 169, 218, 256, 267, 269, 270, 279, 282, 285, 285, 286, 288, 289, 289, 290, 304, 2, 3]
        
        feature = test_encode_record(input_records, input_player_id)
        # print("actual:",feature)
        self.assertEqual(expected, feature)

        input_records = [
            {"type":"start_game","names":["x","x","x"],"uri":"http://tenhou.net/0/?log=2000080000gm-00b2-0000-6b000000&tw=0"},
            {"type":"start_kyoku","bakaze":"E","kyoku":1,"honba":0,"kyotaku":0,"oya":0,"dora_marker":"0m","tehais":[["1m","2p","4p","5p","4s","7s","E","E","S","N","P","P","F"],["4p","7p","9p","1s","3s","6s","8s","W","N","F","F","C","C"],["1p","2p","3p","6p","6p","8p","9p","1s","2s","3s","5s","9s","E"]]},
            {"type":"tsumo","actor":0,"pai":"2p"}
        ]
        input_player_id = 0
        expected =  [1, 7, 8, 11, 14, 17, 21, 72, 169, 218, 256, 267, 269, 270, 279, 282, 285, 285, 286, 288, 289, 289, 290, 304, 2, 3]

        feature = test_encode_record(input_records, input_player_id)
        # print("actual:",feature)
        self.assertEqual(expected, feature)

    def dora_markers(self) :
        input_doras = [Tile.from_str(pai) for pai in ["0m", "1m", "1m", "C", "C"]]
        self.assertEqual(MjaiStateEncoder.dora_markers(input_doras), [21, 59, 96, 168, 205])
    
    def test_encode_delta_score(self) :
        self.assertEqual(encode_delta_score(99999) , 96)
        self.assertEqual(encode_delta_score(48001) , 96)
        self.assertEqual(encode_delta_score(48000) , 96)
        
        self.assertEqual(encode_delta_score(47999) , 95)

        self.assertEqual(encode_delta_score(-48000), 0)
        self.assertEqual(encode_delta_score(-48001), 0)
        self.assertEqual(encode_delta_score(-99999), 0)
        
        self.assertEqual(encode_delta_score(-47999), 1 )
        
        self.assertEqual(encode_delta_score(-1001) , 47 )
        self.assertEqual(encode_delta_score(-1000) , 47 )

        self.assertEqual(encode_delta_score(999)   , 48 )
        self.assertEqual(encode_delta_score(0)     , 48 )
        self.assertEqual(encode_delta_score(-999)  , 48 )

        self.assertEqual(encode_delta_score(1000)  , 49 )
        self.assertEqual(encode_delta_score(1001)  , 49 )

        self.assertEqual(MjaiStateEncoder.scores.width, 97 * 2)

    def test_score(self) :
        input_scores = [0, 999999, 999999]
        input_player_id = 0
        self.assertEqual(MjaiStateEncoder.scores(input_scores, input_player_id), [24, 121])

        input_player_id = 1
        self.assertEqual(MjaiStateEncoder.scores(input_scores, input_player_id), [24 + 48, 217])

        input_player_id = 2
        self.assertEqual(MjaiStateEncoder.scores(input_scores, input_player_id), [120, 121 + 48])

        input_scores = [0, -999999, -999999]
        input_player_id = 0
        self.assertEqual(MjaiStateEncoder.scores(input_scores, input_player_id), [120, 217])

    def test_tsumo(self) :
        self.assertEqual(MjaiStateEncoder.tsumo(Tile.from_str("0m")), [292])

    def test_record(self) :
        input_action = {"type":"dahai","actor":0,"pai":"0m","tsumogiri":False}
        input_player_id = 0
        self.assertEqual(MjaiStateEncoder.record(input_action, input_player_id), 329)
        input_action = {"type":"dahai","actor":0,"pai":"0m","tsumogiri":False}
        input_player_id = 2
        self.assertEqual(MjaiStateEncoder.record(input_action, input_player_id), 544)
        input_action = {"type":"dahai","actor":0,"pai":"0m","tsumogiri":False}
        input_player_id = 1
        self.assertEqual(MjaiStateEncoder.record(input_action, input_player_id), 759)

        input_action = {"type":"dahai","actor":0,"pai":"0m","tsumogiri":True}
        input_player_id = 0
        self.assertEqual(MjaiStateEncoder.record(input_action, input_player_id), 329 + 37)

        input_action = {"type":"reach","actor":0}
        input_player_id = 0
        self.assertEqual(MjaiStateEncoder.record(input_action, input_player_id), 403)

        input_action = {"type":"nukidora","actor":0,"pai":"N"}
        input_player_id = 0
        self.assertEqual(MjaiStateEncoder.record(input_action, input_player_id), 543)
        input_action = {"type":"nukidora","actor":0,"pai":"N"}
        input_player_id = 2
        self.assertEqual(MjaiStateEncoder.record(input_action, input_player_id), 758)
        input_action = {"type":"nukidora","actor":0,"pai":"N"}
        input_player_id = 1
        self.assertEqual(MjaiStateEncoder.record(input_action, input_player_id), 973)

    def test_constant(self) :
        self.assertEqual(TOKEN_VOCAB_COUNT, 974)
        self.assertEqual(MAX_TOKEN_LENGTH, 112)
        self.assertEqual(NUM_LABELS, 112)

        self.assertEqual(TRAIN_TOKEN_PAD, 0)
        self.assertEqual(TRAIN_TOKEN_CLS, 1)
        self.assertEqual(TRAIN_TOKEN_SEP, 2)
        self.assertEqual(TRAIN_TOKEN_EOS, 3)
        self.assertEqual(TRAIN_TOKEN_MASK, 4)
        self.assertEqual(TRAIN_TOKEN_UNK, 5)
     
class TestPreprocess(unittest.TestCase) :
    def test_fix_record_kan1(self) :
        # 牌譜の途中でdaiminkan
        input_records_1 = [
            {"type":"tsumo","actor":0,"pai":"7s"},
            {"type":"dahai","actor":0,"pai":"7s","tsumogiri":True},
            {"type":"daiminkan","actor":2,"target":0,"pai":"7s","consumed":["7s","7s","7s"]},
            {"type":"tsumo","actor":2,"pai":"9m"},
            {"type":"dora","dora_marker":"9m"},
            {"type":"dahai","actor":2,"pai":"E","tsumogiri":False},
            {"type":"ryukyoku","reason":"fanpai","tehais":[["1p","2p","3p","2s","3s","4s","4s","5s","6s","6s"],["?","?","?","?","?","?","?","?","?","?","?","?","?"],["?","?","?","?","?","?","?","?","?","?"]],"tenpais":[True,False,False],"deltas":[3000,-1500,-1500],"scores":[44900,17100,27000]},
            {"type":"end_kyoku"}
            ]
        expected_records_1 = [
            {"type":"tsumo","actor":0,"pai":"7s"},
            {"type":"dahai","actor":0,"pai":"7s","tsumogiri":True},
            {"type":"daiminkan","actor":2,"target":0,"pai":"7s","consumed":["7s","7s","7s"]},
            {"type":"tsumo","actor":2,"pai":"9m"},
            {"type":"dahai","actor":2,"pai":"E","tsumogiri":False},
            {"type":"dora","dora_marker":"9m"},
            {"type":"ryukyoku","reason":"fanpai","tehais":[["1p","2p","3p","2s","3s","4s","4s","5s","6s","6s"],["?","?","?","?","?","?","?","?","?","?","?","?","?"],["?","?","?","?","?","?","?","?","?","?"]],"tenpais":[True,False,False],"deltas":[3000,-1500,-1500],"scores":[44900,17100,27000]},
            {"type":"end_kyoku"}
            ]

        fix_records(input_records_1)
        self.assertEqual(input_records_1, expected_records_1)

    def test_fix_record_kan2(self) :
        input_records = [
            # recordサイズ境界
            {"type":"daiminkan","actor":2,"target":0,"pai":"7s","consumed":["7s","7s","7s"]},
            {"type":"tsumo","actor":2,"pai":"9m"},
            {"type":"dora","dora_marker":"9m"},
            {"type":"dahai","actor":2,"pai":"E","tsumogiri":False},
            ]
        expected_records = [
            {"type":"daiminkan","actor":2,"target":0,"pai":"7s","consumed":["7s","7s","7s"]},
            {"type":"tsumo","actor":2,"pai":"9m"},
            {"type":"dahai","actor":2,"pai":"E","tsumogiri":False},
            {"type":"dora","dora_marker":"9m"},
            ]

        fix_records(input_records)
        self.assertEqual(input_records, expected_records)

    def test_fix_record_kan3(self) :
        input_records = [
            # recordサイズ境界
            {"type":"dahai","actor":0,"pai":"7s","tsumogiri":True},
            {"type":"daiminkan","actor":2,"target":0,"pai":"7s","consumed":["7s","7s","7s"]},
            {"type":"tsumo","actor":2,"pai":"9m"},
            {"type":"dora","dora_marker":"9m"},
            ]
        expected_records = [
            {"type":"dahai","actor":0,"pai":"7s","tsumogiri":True},
            {"type":"daiminkan","actor":2,"target":0,"pai":"7s","consumed":["7s","7s","7s"]},
            {"type":"tsumo","actor":2,"pai":"9m"},
            {"type":"dora","dora_marker":"9m"},
            ]

        fix_records(input_records)
        self.assertEqual(input_records, expected_records)

    def test_fix_record_kan4(self) :
        input_records = [
            # recordサイズ境界
            {"type":"kakan","actor":2,"target":0,"pai":"7s","consumed":["7s","7s","7s"]},
            {"type":"tsumo","actor":2,"pai":"9m"},
            {"type":"dora","dora_marker":"9m"},
            {"type":"dahai","actor":2,"pai":"E","tsumogiri":False},
            ]
        expected_records = [
            {"type":"kakan","actor":2,"target":0,"pai":"7s","consumed":["7s","7s","7s"]},
            {"type":"tsumo","actor":2,"pai":"9m"},
            {"type":"dahai","actor":2,"pai":"E","tsumogiri":False},
            {"type":"dora","dora_marker":"9m"},
            ]

        fix_records(input_records)
        self.assertEqual(input_records, expected_records)

    def test_fix_record_pon1(self) :
        input_records = [
            {"type":"pon","actor":2,"target":0,"pai":"8p","consumed":["8p","8p"]},
            {"type":"dahai","actor":2,"pai":"4s","tsumogiri":True},
            {"type":"tsumo","actor":0,"pai":"9s"}
            ]
        expected_records = [
            {"type":"pon","actor":2,"target":0,"pai":"8p","consumed":["8p","8p"]},
            {"type":"dahai","actor":2,"pai":"4s","tsumogiri":False},
            {"type":"tsumo","actor":0,"pai":"9s"}
            ]
        fix_records(input_records)
        self.assertEqual(input_records, expected_records)
