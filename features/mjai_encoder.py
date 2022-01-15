"""
 mjai_encoder.py
"""
import json
import re

from mjlegal.mjai_possible_action import MjaiPossibleActionGenerator
from mjlegal.mjai import MjaiLoader
from mjlegal.mjtypes import Tile, TilesUtil

class WidthFunc :
    """
    @width指定されたmethodをdecorateするCallable class。
    """
    def __init__(self, org_func, width) :
        self.func = org_func
        self.width = width
        self.offset = 0
    
    def num_offset(self, num) :
        assert 0 <= num
        assert num < self.width
        return num + self.offset

    def __call__(self, *args, **kwargs) :
        result = self.func(*args, **kwargs)
        if isinstance(result, list) :
            result = [self.num_offset(n) for n in result]
        else :
            result = self.num_offset(result)
        return result

def offset_class(cls) :
    """
    offsetを加算するclass decorator。
    @widthでdecorateされたmethodにoffsetを設定する。
    offsetはclass内の定義された順序で計算する。
    """
    current_offset = 0
    for width_func in cls.__dict__.values() :
        if isinstance(width_func, WidthFunc) :
            width_func.offset = current_offset
            current_offset += width_func.width
    return cls

def width(width) :
    """
    offsetを加算するmethod decorator。
    引数に指定した値を使ってoffsetが計算される。
    decoratorが付与されるmethodの戻り値は[0,...,width)の範囲であること。
    """
    def func_width(org_func) :
        width_func = WidthFunc(org_func, width)
        return width_func
    return func_width

def encode_tile34(pai) :
    tile34 = TilesUtil.tiles_to_tiles34([Tile.from_str(pai)])
    return tile34.index(1)
        
TILE37_SUIT_OFFSET_TABLE = {"m" : 0, "p" : 10, "s" : 20, "z" : 29 }
TILE37_LOOKUP_MJAI_PAI_NAME_TABLE = {'5mr': '0m', '5pr': '0p', '5sr': '0s', 'E': '1z', 'S': '2z', 'W': '3z', 'N': '4z', 'P': '5z', 'F': '6z', 'C': '7z'}
def encode_tile37(pai_str) :
    tile_str = TILE37_LOOKUP_MJAI_PAI_NAME_TABLE[pai_str] if pai_str in TILE37_LOOKUP_MJAI_PAI_NAME_TABLE else pai_str
    num = int(tile_str[0])
    suit = tile_str[1]
    assert not("z" == suit and (num < 1 or 7 < num) )
    offset = TILE37_SUIT_OFFSET_TABLE[suit]
    tile37 = offset + num
    return tile37

def sort_rel_scores(abs_scores, player_id) :
    # scoreの並び順をplayer_id視点における順序に変更
    return [abs_scores[(i + player_id) % 3]  for i in range(3)]

@offset_class
class Action :
    """
     Encode mjai action
    """
    @width(37 * 2)
    def dahai(action) :
        pai = action["pai"]
        tsumogiri = action["tsumogiri"]
        tile37 = encode_tile37(pai)
        # 手出し[0,...,36], ツモ切り[37,...,73]
        if tsumogiri :
            tile37 += 37
        return tile37

    @width(1)
    def reach(action) :
        return 0

    @width(37)
    def pon(action) :
        pai = action["pai"]
        consumed = action["consumed"]
        tile37_list = [encode_tile37(pai) for pai in [pai] + consumed]
        tile37 = min(tile37_list) # 赤ドラ牌を選出する
        return tile37

    @width(34)
    def daiminkan(action) :
        pai = action["pai"]
        tile34 = encode_tile34(pai)
        return tile34

    @width(34)
    def kakan(action) :
        pai = action["pai"]
        tile34 = encode_tile34(pai)
        return tile34

    @width(34)
    def ankan(action) :
        consumed = action["consumed"]
        tile34 = encode_tile34(consumed[0])
        return tile34

    @width(1)
    def nukidora(action) :
        return 0

    @width(2)
    def hora(action) :
        # [0,1] 0: ロン, 1: ツモ
        return int(action["target"] != action["actor"])

    @width(1)
    def ryukyoku(action) :
        return 0
    
    @width(1)
    def none(action) :
        return 0

    @classmethod
    def encode(cls, action) :
        action_type = action["type"]
        action_func = getattr(cls, action_type)
        return action_func(action)

    PLAYER_ACTION_WIDTH = hora.offset

# [-48,...,48]
DELTA_SCORE_MAX = 48
def encode_delta_score(delta_score) :
    delta = int(delta_score / 1000)
    if delta > 0:
        k = min(DELTA_SCORE_MAX, delta) + DELTA_SCORE_MAX
    else :
        k = max(-1 * DELTA_SCORE_MAX, delta) + DELTA_SCORE_MAX
    return k

@offset_class
class MjaiStateEncoder :
    @width(1)
    def token_pad() :
        """ Special Token [PAD] """
        pass

    @width(1)
    def token_cls() :
        """ Special Token [CLS] """
        return 0

    @width(1)
    def token_sep() :
        """ Special Token [SEP] """
        return 0

    @width(2)
    def game_type(num) :
        # 0: 東風, 1: 東南
        return num

    @width(3)
    def player_id(num) :
        return num

    @width(3)
    def bakaze(bakaze_str) :
        return "ESW".index(bakaze_str)
    
    @width(3)
    def kyoku(num) :
        return num - 1
    
    @width(4)
    def honba(num) :
        # [0,...,4)内に切り捨てる
        return min(4 - 1, num)

    @width(3)
    def kyotaku(num) :
        return min(3 - 1, num)

    @width(37)
    def dora_0(dora_marker) :
        return encode_tile37(dora_marker)
    @width(37)
    def dora_1(dora_marker) :
        return encode_tile37(dora_marker)
    @width(37)
    def dora_2(dora_marker) :
        return encode_tile37(dora_marker)
    @width(37)
    def dora_3(dora_marker) :
        return encode_tile37(dora_marker)
    @width(37)
    def dora_4(dora_marker) :
        return encode_tile37(dora_marker)

    @classmethod
    def dora_markers(cls, dora_markers_) :
        return [getattr(cls, "dora_" + str(idx))(pai.to_str()) for idx, pai in enumerate(dora_markers_)]

    @width( (DELTA_SCORE_MAX * 2 + 1) * 2 )
    def scores(scores_, player_id) :
        rel_scores = sort_rel_scores(scores_, player_id)
        deltas = [encode_delta_score(rel_scores[0] - score) for score in rel_scores[1:]]
        return [deltas[0], deltas[1] + (DELTA_SCORE_MAX * 2 + 1)]

    @width(136)
    def tehai(tiles) :
        # ツモ牌も含む
        tiles136 = TilesUtil.tiles_to_tiles136(tiles)
        tiles136.sort()
        return tiles136

    @width(37)
    def tsumo(tsumo_tile) :
        res = []
        if tsumo_tile :
            tile37 = encode_tile37(tsumo_tile.to_str())
            res.append(tile37)
        return res

    @width(1)
    def begin_record() :
        return 0

    @width(215)
    def record_player_0(action) :
        return Action.encode(action)
    @width(215)
    def record_player_1(action) :
        return Action.encode(action)
    @width(215)
    def record_player_2(action) :
        return Action.encode(action)

    @classmethod
    def record(cls, action, player_id) :
        rel_player_id = (action["actor"] - player_id + 3) % 3
        record_player_action = getattr(cls, "record_player_" + str(rel_player_id))
        return record_player_action(action)
        
    @classmethod
    def encode(cls, mjai_state, player_id) :
        game_state = mjai_state.client.game
        player_state = game_state.player_states[player_id]
        game_feature = [
            cls.game_type(mjai_state.game_type),
            cls.player_id(player_id),
            cls.bakaze(game_state.bakaze),
            cls.kyoku(game_state.kyoku),
            cls.honba(game_state.honba),
            cls.kyotaku(game_state.kyotaku)
            ] + (cls.dora_markers(game_state.dora_markers) 
            + cls.scores(game_state.scores, player_id)
            + cls.tehai(player_state.tiles)
            + cls.tsumo(player_state.tsumo_tile) 
            + [cls.begin_record()])

        record_feature = [cls.record(r, player_id) for r in mjai_state.records if r["type"] in ("dahai", "reach", "pon", "daiminkan", "kakan", "ankan", "nukidora", "hora", "ryukyoku", "none")]

        return [cls.token_cls()] + game_feature + record_feature + [cls.token_sep()]

    @width(0)
    def EOF() :
        pass

"""
Mahjong game state
"""
class MjaiState :
    def __init__(self) :
        self.client = MjaiLoader()
        self.records = []

    def update(self, record) :
        record_type = record["type"]
        """
        [NOTE] mjaiで副露後の打牌がtsumogiri = Trueになった場合、tsumogiri = Falseに直す.
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
                if m is not None and "00b1" == m.group(1) :
                    self.game_type = 0
        elif record_type == "start_kyoku" :
            self.records = []
            # self.start_kyoku_record = record
            self.client.game.honba = record["honba"]
            self.client.game.kyotaku = record["kyotaku"]
        
        self.client.action(record)
        self.records.append(record)

class MjaiEncoderClient :
    def __init__(self) :
        self.state = MjaiState()
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
        features = MjaiStateEncoder.encode(self.state, player_id)
        assert len(features) <= MAX_TOKEN_LENGTH - 2 , f"Token count is bigger. {MAX_TOKEN_LENGTH}-2 < {len(features)}"
        return features

"""
Constant
"""
TOKEN_VOCAB_COUNT = MjaiStateEncoder.EOF.offset
MAX_TOKEN_LENGTH = 112 # 2(special) + 29(sparse) + 81(progression)

#EOF