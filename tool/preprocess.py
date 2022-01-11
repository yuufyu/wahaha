"""
 preprocess.py
"""
import json
import argparse
import re
import itertools
from pathlib import Path

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
    width = -1
    def __init__(self, *args) :
        self.args = args
    
    def feature(self) :
        nums = self.values(*self.args) 
        if type(self).offset != 0 :
            nums = [num + type(self).offset for num in nums]
        assert type(self).offset <= min(nums + [type(self).offset]) and max(nums + [type(self).offset]) < type(self).width + type(self).offset, f"[{type(self).__name__}]Invalid return values ({type(self).width} + {type(self).offset} <= {nums} )"
        return nums 

    """
    特徴となる数値リストを返す
    """
    def values(self, *args) :
        return list(args)

class _ActionBase :
    # クラス変数に設定するoffset値として使用するため、クラス変数として定義
    offset = 0
    @staticmethod
    def action_elem(width) :
        offset = _ActionBase.offset
        _ActionBase.offset += width
        return Elem(width, offset)

class Action (_ActionBase) :
    def __init__(self) :
        self.action_classes = {member.typename : member for member in Action.__dict__.values() if hasattr(member, "typename")}

    def __call__(self, action) :
        elem_type = self.action_classes[action["type"]]
        return elem_type(action)

    class Dahai(_ActionBase.action_elem(37*2)) :
        typename = "dahai"
        def values(self, action) :
            assert self.typename == action["type"]
            pai = action["pai"]
            tsumogiri = action["tsumogiri"]
            tile37_list = Tile37(pai).feature()
            if tsumogiri :
                tile37_list[0] *= 2
            return tile37_list

    class Reach(_ActionBase.action_elem(1)) :
        typename = "reach"
        def values(self, action) :
            assert self.typename == action["type"]
            return [0]

    class Pon(_ActionBase.action_elem(37)) :
        typename = "pon"
        def values(self, action) :
            assert self.typename == action["type"]
            pai = action["pai"]
            consumed = action["consumed"]
            tile37_list = [Tile37(pai).feature()[0] for pai in [pai] + consumed]
            tile37 = min(tile37_list) # 赤ドラを含む場合は赤ドラ牌を選出する
            return [tile37]
    
    class Daiminkan(_ActionBase.action_elem(34)) :
        typename = "daiminkan"
        def values(self, action) :
            assert self.typename == action["type"]
            pai = action["pai"]
            tile34_list = Tile34(pai).feature()
            return tile34_list
    
    class Kakan(_ActionBase.action_elem(34)) :
        typename = "kakan"
        def values(self, action) :
            assert self.typename == action["type"]
            pai = action["pai"]
            tile34_list = Tile34(pai).feature()
            return tile34_list
    class Ankan(_ActionBase.action_elem(34)) :
        typename = "ankan"
        def values(self, action) :
            assert self.typename == action["type"]
            pai = action["pai"]
            tile34_list = Tile34(pai).feature()
            return tile34_list

    

"""
 Define Elements
"""
class GameStyle(Elem(2)) :
    pass

class PlayerId(Elem(3)) :
    pass

class Kyoku(Elem(3)) :
    def values(self, kyoku) :
        return [kyoku - 1]

class Tile34(Elem(34)) :
    def values(self, pai_str) :
        tile34 = TilesUtil.tiles_to_tiles34([Tile.from_str(pai_str)])
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

class Tile136(Elem(136)) :
    def values(self, tiles) :
        tiles136 = TilesUtil.tiles_to_tiles136(tiles)
        tiles136.sort()
        return tiles136

class Honba(Elem(4)) :
    def values(self, honba) :
        return [min(Honba.width - 1, honba)]

class Kyotaku(Elem(3)) :
    def values(self, kyotaku) :
        return [min(Kyotaku.width - 1, kyotaku)]

class Bakaze(Elem(3)) :
    def values(self, bakaze_str) :
        return ["ESW".index(bakaze_str)]

class DoraMarkers(Elem(37 * 5)) :
    def values(self, dora_markers) :
        return encode_elems([Tile37(tile.to_str()) for tile in dora_markers])

class Rank(Elem(6)) :
    def values(self, abs_scores, player_id) :
        rel_scores = sort_rel_scores(abs_scores, player_id)

        # Calculate ranking by Mahjong rule
        range_indices = range(len(rel_scores))
        sorted_indices = sorted(range_indices, key = rel_scores.__getitem__, reverse = True)
        ranks = [0] * len(sorted_indices)
        for i, indices in enumerate(sorted_indices) :
            ranks[indices] = i
        return ranks

DELTA_SCORE_BINS = [2000, 4000, 6000, 8000, 10000, 12000, 14000, 16000]
class DeltaScores(Elem(len(DELTA_SCORE_BINS) + 1)) :
    def values(self, abs_scores, player_id) :
        rel_scores = sort_rel_scores(abs_scores, player_id)

        # delta_scoreに変換
        delta_scores = [rel_scores[0] - score for score in rel_scores]
        return [next((idx for idx, bin in enumerate(DELTA_SCORE_BINS) if abs(delta) <= bin), len(DELTA_SCORE_BINS)) for delta in delta_scores ]

class TsumoTile(Tile37) :
    def values(self, tsumo_tile) :
        tile37 = []
        if tsumo_tile :
            tile37 = super().values(tsumo_tile.to_str())
        return tile37

class NanElem(Elem(0)) :
    def values(self, _) :
        return []

def sort_rel_scores(abs_scores, player_id) :
    # scoreの並び順をplayer_id視点における順序に変更
    return [abs_scores[(i + player_id) % 3]  for i in range(3)]

"""
 elem to feature
"""
def elems_to_nums(elems) :
    return list(itertools.chain.from_iterable(elem.feature() for elem in elems))

def encode_elems(elems) :
    result = []
    offset = 0
    for elem in elems : 
        nums = elem.feature()
        result.extend([num + offset for num in nums])
        offset += elem.width
    return result

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

class MjFeatureClient :
    def __init__(self) :
        self.state = MjState()
        self.possible_generator = MjaiPossibleActionGenerator()

    def update(self, record) :
        self.state.update(record)

    def possible_action(self, player_id) :
        game_state = self.state.client.game
        game_state.player_id = player_id

        possible_actions = self.possible_generator.possible_mjai_action(game_state)

        # 重複削除
        possible_mjai_json_actions = [json.dumps(action) for action in possible_actions]
        possible_mjai_actions = [json.loads(action_str) for action_str in set(possible_mjai_json_actions)]

        # player_idのactionのみ抽出
        possible_player_actions = []
        for mjai_action in possible_mjai_actions :
            if "actor" in mjai_action and mjai_action["actor"] == player_id :
                possible_player_actions.append(mjai_action)
            elif mjai_action["type"] == "none" :
                possible_player_actions.append(mjai_action)

        return possible_player_actions

    def encode(self, player_id) :
        return self.encode_game_state(player_id)

    def encode_game_state(self, player_id) :
        game_state = self.state.client.game
        player_state = game_state.player_states[player_id]
        elems = [
            GameStyle(self.state.game_type),
            PlayerId(player_id),
            Bakaze(self.state.start_kyoku_record["bakaze"]),
            Kyoku(self.state.start_kyoku_record["kyoku"]),
            Honba(self.state.start_kyoku_record["honba"]),
            Kyotaku(self.state.start_kyoku_record["kyotaku"]),
            DoraMarkers(game_state.dora_markers),
            Rank(game_state.scores, player_id),
            DeltaScores(game_state.scores, player_id),
            Tile136(player_state.tiles),
            TsumoTile(player_state.tsumo_tile)
        ]
        return encode_elems(elems)

    def encode_record(self, player_id) :
        pass
    def encode_possible_action(self, player_id) :
        pass

"""
 preprocess
"""
def join_num(num_list) :
    return ",".join([str(n) for n in num_list])

def load_mjai_records(filename) :
    records = []
    log_input_file = open(filename, 'r', encoding="utf-8")
    for line in log_input_file :
        mjai_ev = json.loads(line)
        records.append(mjai_ev)
    log_input_file.close()
    return records

def process_records(records) :
    mj_client = MjFeatureClient()
    train_data = []
    for i in range(len(records) - 1) :
        record = records[i]
        mj_client.update(record)
        
        for player_id in range(3) :
            possible_actions = mj_client.possible_action(player_id)

            # 選択肢が発生
            if len(possible_actions) > 1 :
                next_record = records[i + 1]

                # playerが選択しないactionは学習しない
                if not("actor" in next_record) :
                    continue
                
                if next_record["type"] in ("tsumo", "reach_accepted") :# Skip選択
                    pass #actual_label = SKIP 
                elif player_id != next_record["actor"] : # Skip選択
                    pass #actual_label = SKIP
                else :
                    pass #actual_label = Action(actual_action)

                # feature
                feature = mj_client.encode(player_id)
                print(feature)
                # assert actual_label in possible_feature, f"invalid actual feature {actual_label}"
                
                # train_data.append((feature, actual_label))

    return train_data

def main() :
    parser = argparse.ArgumentParser()
    parser.add_argument("mjson_filename")
    parser.add_argument("save_dir_name", default = ".")
    args = parser.parse_args()
    
    filename = args.mjson_filename

    records = load_mjai_records(filename)

    process_records(records)

if __name__ == '__main__':
    main()
