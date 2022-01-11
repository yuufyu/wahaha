"""
 mjai_encoder.py
"""
import json
import re
import itertools

from mjlegal.mjai_possible_action import MjaiPossibleActionGenerator
from mjlegal.mjai import MjaiLoader
from mjlegal.mjtypes import Tile, TilesUtil

"""
分類数を保持したクラスを返す
"""
def Elem(width, offset = 0):
    return type(f"Elem_{width}", (BaseElem, ), {'width' : width, 'offset' : offset})

class BaseElem :
    """
    BaseElem
    各要素を保持する基底クラス
    """
    def __init__(self, *args) :
        self.args = args
    
    def feature(self) :
        nums = self.values(*self.args) 
        if type(self).offset != 0 :
            nums = [num + type(self).offset for num in nums]
        assert len(nums) == 0 or ( type(self).offset <= min(nums) and max(nums) < type(self).width + type(self).offset ), f"[{type(self).__name__}]Invalid return values ({type(self).width} + {type(self).offset} <= {nums} )"
        return nums 

    """
    特徴となる数値リストを返す
    """
    def values(self, *args) :
        return list(args)

"""
offset値をElemクラス定義に保持させる。
offsetの並びはクラス定義順となることに注意。
"""
class _OffsetElemBase :
    def __init__(self) :
        self.offset = 0
    def __call__(self, width) :
        offset = self.offset
        self.offset += width
        return Elem(width, offset)
    
"""
 Define Elements
"""
class Tile34(Elem(34)) :
    def values(self, pai) :
        tile34 = TilesUtil.tiles_to_tiles34([Tile.from_str(pai)])
        return [tile34.index(1)]
        
class Tile37(Elem(37)) :
    TILE37_SUIT_OFFSET_TABLE = {"m" : 0, "p" : 10, "s" : 20, "z" : 29 }
    TILE37_LOOKUP_MJAI_PAI_NAME_TABLE = {'5mr': '0m', '5pr': '0p', '5sr': '0s', 'E': '1z', 'S': '2z', 'W': '3z', 'N': '4z', 'P': '5z', 'F': '6z', 'C': '7z'}
    def values(self, pai_str) :
        tile_str = Tile37.TILE37_LOOKUP_MJAI_PAI_NAME_TABLE[pai_str] if pai_str in Tile37.TILE37_LOOKUP_MJAI_PAI_NAME_TABLE else pai_str
        num = int(tile_str[0])
        suit = tile_str[1]
        assert not("z" == suit and (num < 1 or 7 < num) )
        offset = Tile37.TILE37_SUIT_OFFSET_TABLE[suit]
        tile37 = offset + num
        return [tile37]

def sort_rel_scores(abs_scores, player_id) :
    # scoreの並び順をplayer_id視点における順序に変更
    return [abs_scores[(i + player_id) % 3]  for i in range(3)]

ActionElemBase = _OffsetElemBase()
class ActionBase (BaseElem):
    def __init__(self, action) :
        self.action_classes = {member.typename : member for member in ActionBase.__dict__.values() if hasattr(member, "typename")}
        super().__init__(action)
        
    def values(self, action) :
        action_type = action["type"]
        elems = []
        if action_type in self.action_classes :
            elem_type = self.action_classes[action_type]
            elems.append(elem_type(action))
        return elems_to_nums(elems)

    class Dahai(ActionElemBase(37*2)) :
        typename = "dahai"
        def values(self, action) :
            assert self.typename == action["type"]
            pai = action["pai"]
            tsumogiri = action["tsumogiri"]
            tile37_list = Tile37(pai).feature()
            if tsumogiri :
                tile37_list[0] += 37
            return tile37_list

    class Reach(ActionElemBase(1)) :
        typename = "reach"
        def values(self, action) :
            assert self.typename == action["type"]
            return [0]

    class Pon(ActionElemBase(37)) :
        typename = "pon"
        def values(self, action) :
            assert self.typename == action["type"]
            pai = action["pai"]
            consumed = action["consumed"]
            tile37_list = [Tile37(pai).feature()[0] for pai in [pai] + consumed]
            tile37 = min(tile37_list) # 赤ドラを含む場合は赤ドラ牌を選出する
            return [tile37]

    class Daiminkan(ActionElemBase(34)) :
        typename = "daiminkan"
        def values(self, action) :
            assert self.typename == action["type"]
            pai = action["pai"]
            tile34_list = Tile34(pai).feature()
            return tile34_list

    class Kakan(ActionElemBase(34)) :
        typename = "kakan"
        def values(self, action) :
            assert self.typename == action["type"]
            pai = action["pai"]
            tile34_list = Tile34(pai).feature()
            return tile34_list

    class Ankan(ActionElemBase(34)) :
        typename = "ankan"
        def values(self, action) :
            assert self.typename == action["type"]
            consumed = action["consumed"]
            tile34_list = Tile34(consumed[0]).feature()
            return tile34_list

    class Nukidora(ActionElemBase(1)) :
        typename = "nukidora"
        def values(self, action) :
            assert self.typename == action["type"]
            return [0]

    class Hora(ActionElemBase(2)) :
        typename = "hora"
        def values(self, action) :
            assert self.typename == action["type"]
            num = int(action["target"] != action["actor"])
            return [num]

    class Ryukyoku(ActionElemBase(1)) :
        typename = "ryukyoku"
        def values(self, action) :
            assert self.typename == action["type"]
            return [0]

    class Skip(ActionElemBase(1)) :
        typename = "none"
        def values(self, action) :
            assert self.typename == action["type"]
            return [0]
    
    PLAYER_ACTION_WIDTH = Hora.offset

class Action(Elem(219), ActionBase) :
    pass

"""
 annotation
"""
OffsetElem = _OffsetElemBase()

class SpecialTokens(OffsetElem(3)) :
    def values(self, _) :
        return []

class GameStyle(OffsetElem(2)) :
    pass

class PlayerId(OffsetElem(3)) :
    pass

class Bakaze(OffsetElem(3)) :
    def values(self, bakaze_str) :
        return ["ESW".index(bakaze_str)]

class Kyoku(OffsetElem(3)) :
    def values(self, kyoku) :
        return [kyoku - 1]

class Honba(OffsetElem(4)) :
    def values(self, honba) :
        return [min(Honba.width - 1, honba)]

class Kyotaku(OffsetElem(3)) :
    def values(self, kyotaku) :
        return [min(Kyotaku.width - 1, kyotaku)]

class DoraMarkers(OffsetElem(37 * 5)) :
    def values(self, dora_markers) :
        assert len(dora_markers) <= 5
        res = []
        offset = 0
        for tile in dora_markers :
            tile37 = Tile37(tile.to_str()).feature()[0]
            tile37 += offset
            offset += 37
            res.append(tile37)
        return res

class Rank(OffsetElem(6)) :
    RANKS_TO_FEATURE_LOOKUP_TABLE = list(itertools.permutations(range(3)))
    def get_rel_rank(self, abs_scores, player_id) :
        rel_scores = sort_rel_scores(abs_scores, player_id)

        # Calculate ranking by Mahjong rule
        range_indices = range(len(rel_scores))
        sorted_indices = sorted(range_indices, key = rel_scores.__getitem__, reverse = True)
        ranks = [0] * len(sorted_indices)
        for i, indices in enumerate(sorted_indices) :
            ranks[indices] = i
        return ranks

    def values(self, abs_scores, player_id) :
        ranks = self.get_rel_rank(abs_scores, player_id)
        ranks_feature = type(self).RANKS_TO_FEATURE_LOOKUP_TABLE.index(tuple(ranks))
        return [ranks_feature]

DELTA_SCORE_BINS = [2000, 4000, 6000, 8000, 10000, 12000, 14000, 16000]
class DeltaScores(OffsetElem((len(DELTA_SCORE_BINS) + 1) * 2)) :
    def values(self, abs_scores, player_id) :
        rel_scores = sort_rel_scores(abs_scores, player_id)

        # delta_scoreに変換
        delta_scores = [rel_scores[0] - score for score in rel_scores]
        score_classes =  [next((idx for idx, bin in enumerate(DELTA_SCORE_BINS) if abs(delta) <= bin), len(DELTA_SCORE_BINS)) for delta in delta_scores ]
        return [score_classes[1], score_classes[2] + len(DELTA_SCORE_BINS) + 1]

class Tehai(OffsetElem(136)) :
    def values(self, tiles) :
        # ツモ牌も含む
        tiles136 = TilesUtil.tiles_to_tiles136(tiles)
        tiles136.sort()
        return tiles136

class TsumoTile(OffsetElem(37)) :
    def values(self, tsumo_tile) :
        tile37 = []
        if tsumo_tile :
            tile37 = Tile37(tsumo_tile.to_str()).feature()
        return tile37

class BeginRecordElem(OffsetElem(1)) :
    def values(self) :
        return [0]

RecordElemBase = _OffsetElemBase()
class RecordPlayerElem_0(RecordElemBase(215), ActionBase) :
    pass
class RecordPlayerElem_1(RecordElemBase(215), ActionBase) :
    pass
class RecordPlayerElem_2(RecordElemBase(215), ActionBase) :
    pass
        
class RecordElem(OffsetElem(215 * 3)) :
    RECORD_PLAYER_ELEM_CLASSES = [RecordPlayerElem_0, RecordPlayerElem_1, RecordPlayerElem_2]
    
    def values(self, records, player_id) :
        #player_id : 現在の主観player_id
        elems = []
        for record in records :
            if "actor" in record :
                # 相対player_id
                rel_player_id = (record["actor"] - player_id + 3) % 3 

                # 相対player_idに応じて異なるActionBaseを作成
                elem_type = type(self).RECORD_PLAYER_ELEM_CLASSES[rel_player_id]
                elem = elem_type(record)
                elems.append(elem)
        return elems_to_nums(elems)

class PossibleActionElem(OffsetElem(219)) :
    def values(self, possible_actions) :
        elems = [Action(action) for action in possible_actions]
        nums = elems_to_nums(elems)
        assert len(nums) == len(possible_actions), "possible action is duplicate"
        return nums

class EOF(OffsetElem(0)) :
    pass

class AnnotateElem(Elem(EOF.offset)) :
    """
    全体をencodeするElem
    """
    def values(self, game_type, start_kyoku, player_id, game_state, records, possible_actions) :
        player_state = game_state.player_states[player_id]
        elems = [
            GameStyle(game_type),
            PlayerId(player_id),
            Bakaze(start_kyoku["bakaze"]),
            Kyoku(start_kyoku["kyoku"]),
            Honba(start_kyoku["honba"]),
            Kyotaku(start_kyoku["kyotaku"]),
            DoraMarkers(game_state.dora_markers),
            Rank(game_state.scores, player_id),
            DeltaScores(game_state.scores, player_id),
            Tehai(player_state.tiles),
            TsumoTile(player_state.tsumo_tile),
            BeginRecordElem(),
            RecordElem(records, player_id),
            PossibleActionElem(possible_actions)
        ]
        return elems_to_nums(elems)

"""
 elem to feature
"""
def elems_to_nums(elems) :
    return list(itertools.chain.from_iterable(elem.feature() for elem in elems))

"""
Mahjong game state
"""
class MjState :
    def __init__(self) :
        self.client = MjaiLoader()
        self.records = []

    def update(self, record) :
        record_type = record["type"]
        """
        [NOTE] 副露した後の打牌がtsumogiri = Trueになることがあるため、tsumogiri = Falseに直す。
        """
        if record_type == "dahai" and self.records[-1]["type"] in ("pon", "daiminkan") :
            record["tsumogiri"] = False

        # process record
        if record_type == "start_game" :
            self.game_type = 1 # 東風(0), 半荘(1)
            if "uri" in record :
                uri = record["uri"]
                self.uri = uri
                m = re.search("log=\d{10}gm-([0-9a-f]{4})-",uri)
                if "00b1" == m.group(1) :
                    self.game_type = 0
        elif record_type == "start_kyoku" :
            self.records = []
            self.start_kyoku_record = record
        
        self.client.action(record)
        self.records.append(record)

class MjaiEncoderClient :
    def __init__(self) :
        self.state = MjState()
        self.possible_generator = MjaiPossibleActionGenerator()

    def update(self, record) :
        self.state.update(record)

    def possible_player_action(self, player_id) :
        game_state = self.state.client.game
        game_state.player_id = player_id
        possible_mjai_actions = self.possible_generator.possible_mjai_action(game_state)

        # 重複削除
        possible_mjai_json_actions = [json.dumps(action) for action in possible_mjai_actions]
        possible_mjai_actions = [json.loads(action_str) for action_str in set(possible_mjai_json_actions)]

        return possible_mjai_actions

    def encode(self, player_id) :
        game_state = self.state.client.game
        elem = AnnotateElem(self.state.game_type,
            self.state.start_kyoku_record,
            player_id,
            game_state,
            self.state.records,
            self.possible_player_action(player_id))
        features = elem.feature()
        assert len(features) <= MAX_TOKEN_LENGTH - 2 , f"Token count is bigger. {MAX_TOKEN_LENGTH}-2 < {len(features)}"
        return features

"""
Constant
"""
TOKEN_VOCAB_COUNT = EOF.offset
MAX_TOKEN_LENGTH = 145 # 2(special) + 30(sparse) + 81(progression) + 32(possible)

#EOF
