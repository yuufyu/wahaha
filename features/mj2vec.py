"""
 mj2vec
"""
import json
import argparse
import numpy as np
from dataclasses import dataclass, asdict, field
import re
from collections import OrderedDict
import itertools
from pathlib import Path

from mjlegal.mjai_possible_action import MjaiPossibleActionGenerator
from mjlegal.mjai import MjaiLoader
from mjlegal.mjtypes import Tile, TilesUtil

def feature_count_to_offset(counts : OrderedDict, initial_offset = 0) :
    offsets = {}
    offset = initial_offset
    for key, count in counts.items() :
        offsets[key] = offset
        offset += count
    return offsets

SPARSE_FEATURE_COUNT = OrderedDict([
    ("style"            , 2),
    ("seat"             , 3),
    ("bakaze"           , 3),
    ("kyoku"            , 3),
    ("honba"            , 4),
    ("kyotaku"          , 3),
    ("dora_0"           , 37),
    ("dora_1"           , 37),
    ("dora_2"           , 37),
    ("dora_3"           , 37),
    ("dora_4"           , 37),
    ("rank"             , 6),
    ("hand"             , 136),
    ("tsumo_tile"       , 37),
    ("end"              , 0)
])
SPARSE_FEATURE_OFFSET = feature_count_to_offset(SPARSE_FEATURE_COUNT)
SPARSE_FEATURE_PADDING = SPARSE_FEATURE_OFFSET["end"]

PROGRESSION_FEATURE_COUNT = OrderedDict([
    ("dahai_tsumogiri"  , 37),
    ("dahai_tedasi"     , 37),
    ("reach"            , 1),
    ("pon"              , 37),
    ("daiminkan"        , 34),
    ("ankan"            , 34),
    ("kakan"            , 34),
    ("nukidora"         , 1),
    ("end"              , 0)
])
PROGRESSION_FEATURE_OFFSETS = feature_count_to_offset(PROGRESSION_FEATURE_COUNT, 1) # Offset for BOR
PROGRESSION_FEATURE_PLAYER_OFFSET = PROGRESSION_FEATURE_OFFSETS["end"]
PROGRESSION_FEATURE_PADDING = PROGRESSION_FEATURE_PLAYER_OFFSET * 3

POSSIBLE_FEATURE_COUNT = OrderedDict([
    ("dahai_tsumogiri"  , 37),
    ("dahai_tedasi"     , 37),
    ("reach"            , 1),
    ("pon"              , 37),
    ("daiminkan"        , 34),
    ("ankan"            , 34),
    ("kakan"            , 34),
    ("nukidora"         , 1),
    ("hora_tsumo"       , 1),
    ("hora_rong"        , 1),
    ("ryukyoku"         , 1),
    ("skip"             , 1),
    ("end"              , 0)
])
POSSIBLE_FEATURE_OFFSETS = feature_count_to_offset(POSSIBLE_FEATURE_COUNT, 0)
POSSIBLE_FEATURE_PADDING = POSSIBLE_FEATURE_OFFSETS["end"]

RANKS_TO_FEATURE_LOOKUP_TABLE = list(itertools.permutations(range(3)))

@dataclass
class PlayerElem :
    hand : list
    scores : list = None
    tsumo : int = -1
    ranks  : int = -1

    def set_scores(self, player_id, scores) :
        rel_scores = [scores[(i + player_id) % 3]  for i in range(3)]
        rel_ranks = tuple(scores2ranks(rel_scores))
        ranks_feature = RANKS_TO_FEATURE_LOOKUP_TABLE.index(rel_ranks)
        self.scores = rel_scores
        self.ranks  = ranks_feature

    def to_sparse_feature(self) :
        hand_offset = SPARSE_FEATURE_OFFSET["hand"]
        hand_features = [hand_offset + tile136 for tile136 in self.hand]
        ranks_feature = SPARSE_FEATURE_OFFSET["rank"] + self.ranks
        features = [ranks_feature] + hand_features
        if self.tsumo >= 0 :
            tsumo_feature = SPARSE_FEATURE_OFFSET["tsumo_tile"] + self.tsumo
            features.append(tsumo_feature)
        features.sort()
        return features

    def to_numeric_feature(self) :
        return self.scores

@dataclass
class ActionElem :
    type : str
    actor : int = 0
    value : int = 0

    @staticmethod
    def from_mjai(record) :
        action = None
        action_type = record["type"]
        assert action_type != "tsumo"
        # skipはmjaiにない
        if action_type == "ryukyoku" :
            # mjaiにactorが含まれていない。
            # possible actionの場合はactorが含まれる。
            actor_id = 0
            if "actor" in record :
                actor_id = record["actor"] 
            action = ActionElem(type = action_type, actor = actor_id, value = 0)
        elif action_type == "none" :
            action = ActionElem(type = "skip", value = 0)
        elif "actor" in record :
            actor_id = record["actor"]
            if action_type == "dahai" :
                pai = record["pai"]
                tsumogiri = record["tsumogiri"]
                tile37 = mjai_pai_to_tile37(pai)
                progression_type = "dahai_tsumogiri" if tsumogiri else "dahai_tedasi"
                action = ActionElem(type = progression_type, actor = actor_id, value = tile37)
            elif action_type == "reach" :
                action = ActionElem(type = action_type, actor = actor_id, value = 0)
            elif action_type == "pon" :
                pai = record["pai"]
                # target = record["target"]
                consumed = record["consumed"]
                pai_list = [pai] + consumed
                tile37_list = [mjai_pai_to_tile37(pai) for pai in pai_list]
                tile37 = min(tile37_list) # 赤ドラを含む場合は赤ドラ牌を選出する
                action = ActionElem(type = action_type, actor = actor_id, value = tile37)
            elif action_type == "daiminkan" :
                pai = record["pai"]
                # target = record["target"]
                # consumed = record["consumed"]
                tile34 = mjai_pai_to_tile34(pai)
                action = ActionElem(type = action_type, actor = actor_id, value = tile34)
            elif action_type == "kakan" :
                pai = record["pai"]
                tile34 = mjai_pai_to_tile34(pai)
                action = ActionElem(type = action_type, actor = actor_id, value = tile34)
            elif action_type == "ankan" :
                consumed = record["consumed"]
                pai = consumed[0]
                tile34 = mjai_pai_to_tile34(pai)
                action = ActionElem(type = action_type, actor = actor_id, value = tile34)
            elif action_type == "nukidora" :
                # pai = record["pai"]
                action = ActionElem(type = action_type, actor = actor_id, value = 0)
            elif action_type == "hora" :
                target = record["target"]
                elem_type = ("hora_tsumo" if target == actor_id else "hora_rong")
                action = ActionElem(type = elem_type, actor = actor_id, value = 0)
        return action

    @staticmethod
    def possible_action_feature(action_elem) :
        assert 0 <= action_elem.value and action_elem.value < POSSIBLE_FEATURE_COUNT[action_elem.type], f"invalid num (type={action_elem.type}, value={action_elem.value})"
        offset = POSSIBLE_FEATURE_OFFSETS[action_elem.type]
        feature_value =  (action_elem.value + offset)
        return feature_value

@dataclass
class GameElem :
    style   : int = -1
    kyotaku : int = -1
    kyoku   : int = -1
    honba   : int = -1
    bakaze  : int = -1
    dora_0 : int = -1
    dora_1 : int = -1
    dora_2 : int = -1
    dora_3 : int = -1
    dora_4 : int = -1

    def to_feature(self, player_id) :
        features = []
        game_elem_dict = asdict(self)
        game_elem_dict["seat"] = player_id
        for key, value in game_elem_dict.items() :
            if (key in ("dora_1", "dora_2", "dora_3", "dora_4")) and value == -1 :
                continue # skip

            if (key in ("honba", "kyotaku")) :
                value = min(SPARSE_FEATURE_COUNT[key] - 1, value)
            assert 0 <= value and value < SPARSE_FEATURE_COUNT[key], f"invalid num (key={key}, val={value})" 
            offset = SPARSE_FEATURE_OFFSET[key]
            features.append(offset + value)
        features.sort()
        return features
    def add_dora(self, tile37) :
        if -1 == self.dora_0 :
            self.dora_0 = tile37
        elif -1 == self.dora_1 :
            self.dora_1 = tile37
        elif -1 == self.dora_2 :
            self.dora_2 = tile37
        elif -1 == self.dora_3 :
            self.dora_3 = tile37
        elif -1 == self.dora_4 :
            self.dora_4 = tile37
        else :
            assert False, "Too many dora markers."

@dataclass
class Features :
    uuid        : str = "uuid"
    sparse      : list = None
    numeric     : list = None
    progression : list = None
    possible    : list = None
    actual      : int  = POSSIBLE_FEATURE_OFFSETS["skip"] # label

TILE37_SUIT_OFFSET_TABLE = {"m" : 0, "p" : 10, "s" : 20, "z" : 29 }
TILE37_LOOKUP_MJAI_PAI_NAME_TABLE = {'5mr': '0m', '5pr': '0p', '5sr': '0s', 'E': '1z', 'S': '2z', 'W': '3z', 'N': '4z', 'P': '5z', 'F': '6z', 'C': '7z'}

def mjai_pai_to_tile37(mjai_str) :
    tile_str = TILE37_LOOKUP_MJAI_PAI_NAME_TABLE[mjai_str] if mjai_str in TILE37_LOOKUP_MJAI_PAI_NAME_TABLE else mjai_str
    assert len(tile_str) == 2

    num = int(tile_str[0])
    suit = tile_str[1]
    assert not("z" == suit and (num < 1 or 7 < num) )

    offset = TILE37_SUIT_OFFSET_TABLE[suit]
    tile37 = offset + num
    return tile37

def mjai_pai_to_tile34(pai) :
    tile34 = TilesUtil.tiles_to_tiles34([Tile.from_str(pai)])
    return tile34.index(1)

# Calculate ranking by Mahjong rule
def scores2ranks(scores) :
    range_indices = range(len(scores))
    sorted_indices = sorted(range_indices, key = scores.__getitem__, reverse = True)
    ranks = [0] * len(sorted_indices)
    for i, indices in enumerate(sorted_indices) :
        ranks[indices] = i
    return ranks

def load_mjai_records(filename) :
    records = []
    log_input_file = open(filename, 'r', encoding="utf-8")
    for line in log_input_file :
        mjai_ev = json.loads(line)
        records.append(mjai_ev)
    log_input_file.close()
    return records

class Progression2Vec :
    def __init__(self) :
        pass
        
    def to_rel_seat(self, actor, player_id) :
        return ((actor - player_id + 3) % 3)

    def to_feature(self, player_id) :
        progression = [0] # Begging of the Round
        for actionElem in self.action_list :
            assert 0 <= actionElem.value and actionElem.value < PROGRESSION_FEATURE_COUNT[actionElem.type], f"invalid num (type={actionElem.type}, value={actionElem.value})"
            offset = PROGRESSION_FEATURE_OFFSETS[actionElem.type]
            rel_actor_id = self.to_rel_seat(actionElem.actor, player_id)
            feature_value =  (actionElem.value + offset) + (PROGRESSION_FEATURE_PLAYER_OFFSET) * rel_actor_id
            progression.append(feature_value)
        return progression

    def action(self, record) :
        action_type = record["type"]
        if action_type == "start_kyoku" :
            self.action_list = []
        elif "actor" in record :
            if action_type in ["dahai", "reach", "pon", "daiminkan", "ankan", "kakan", "nukidora"] :
                actionElem = ActionElem.from_mjai(record)
                self.action_list.append(actionElem)

class Players2Vec :
    def __init__(self) :
        self.mjlegal_client = MjaiLoader()
        self.possible_generator = MjaiPossibleActionGenerator()
        self.progression2vec = None

    def action(self, record) :
        self.mjlegal_client.action(record)
        # TODO possible_action()もここで計算した方が高速

        action_type = record["type"]
        if action_type == "start_kyoku" :
            self.progression2vec = Progression2Vec()
    
        if self.progression2vec is not None :
            self.progression2vec.action(record)

    def progression_actions(self) :
        return self.progression2vec.action_list

    def progression_feature(self, player_id) :
        return self.progression2vec.to_feature(player_id)

    def get_player_elem(self, player_id) :
        game_state = self.mjlegal_client.game
        player_state = game_state.player_states[player_id]
        tiles = player_state.tiles
        tiles136 = TilesUtil.tiles_to_tiles136(tiles)
        tsumo_tile = player_state.tsumo_tile
        
        player_elem = PlayerElem(hand = tiles136)
        if tsumo_tile :
            player_elem.tsumo = mjai_pai_to_tile37(tsumo_tile.to_mjai_str())
        scores = game_state.scores
        player_elem.set_scores(player_id, scores)

        return player_elem

    def get_possible_action(self, player_id) :
        game_state = self.mjlegal_client.game
        game_state.player_id = player_id

        possible_actions = self.possible_generator.possible_mjai_action(game_state)

        # 重複削除
        possible_mjai_json_actions = [json.dumps(action) for action in possible_actions]
        possible_mjai_actions = [json.loads(action_str) for action_str in set(possible_mjai_json_actions)]

        # player_idのactionのみ抽出
        possible_player_actions = []
        for mjai_action in possible_mjai_actions :
            action_type = mjai_action["type"]
            if action_type in ("dahai", "reach", "pon", "daiminkan", "ankan", "kakan", "nukidora", "hora", "ryukyoku") :
                if mjai_action["actor"] == player_id :
                    possible_player_actions.append(mjai_action)
            elif action_type == "none" :
                possible_player_actions.append(mjai_action)

        return possible_player_actions

    def get_possible_action_elem(self, player_id) :
        possible_player_actions = self.get_possible_action(player_id)
        action_elems = [ActionElem.from_mjai(action) for action in possible_player_actions]
        return action_elems

    def to_possible_feature(self, player_id) :
        possible_action_elems = self.get_possible_action_elem(player_id)
        features = [ActionElem.possible_action_feature(action_elem) for action_elem in possible_action_elems]
        assert len(features) == len(set(features))
        features.sort()
        return features

    def dump(self) :
        for i in range(3) :
            player_elem = self.get_player_elem(i)
            possible_action = self.get_possible_action_elem(i)
            print(f"possible{i} : {possible_action}")
            print(f"player{i} : {player_elem}")

class Sparse2Vec :
    def __init__(self) :
        self.game_style = -1
        self.players = None
        self.game_elem = None

    def action(self, record) :
        action_type = record["type"]
        if action_type == "start_game" :
            self.setup_game_style(record)
        elif action_type == "start_kyoku" :
            self.game_elem = GameElem()
            self.game_elem.style = self.game_style
            self.setup_kyoku(record)
            self.setup_kyotaku(record)
            self.setup_honba(record)
            self.setup_bakaze(record)
            self.setup_dora_markers(record)
        elif action_type == "dora" :
            self.add_dora_markers(record)
    
    def setup_game_style(self, start_game_record) :
        assert "start_game" == start_game_record["type"], "record type must be start_game."
        game_type = 1 # 東風(0), 半荘(1)
        if "uri" in start_game_record :
            uri = start_game_record["uri"]
            self.uri = uri
            m = re.search("log=\d{10}gm-([0-9a-f]{4})-",uri)
            if "00b1" == m.group(1) :
                game_type = 0
        self.game_style = game_type 

    def setup_kyotaku(self, record) :
        assert "start_kyoku" == record["type"], "invalid record type"
        kyotaku = record["kyotaku"]
        self.game_elem.kyotaku = kyotaku

    def setup_kyoku(self, record) :
        assert "start_kyoku" == record["type"], "invalid record type"
        kyoku = record["kyoku"]
        self.game_elem.kyoku = kyoku - 1

    def setup_honba(self, record) :
        assert "start_kyoku" == record["type"], "invalid record type"
        honba = record["honba"]
        self.game_elem.honba = honba

    def setup_bakaze(self, record) :
        assert "start_kyoku" == record["type"], "invalid record type"
        bakaze_str = record["bakaze"]
        bakaze = "ESW".index(bakaze_str)
        self.game_elem.bakaze = bakaze

    def setup_dora_markers(self, record) :
        assert "start_kyoku" == record["type"], "invalid record type"
        dora_marker = record["dora_marker"]
        self.game_elem.dora_0  = mjai_pai_to_tile37(dora_marker)

    def add_dora_markers(self, record) :
        dora_marker = record["dora_marker"]
        self.game_elem.add_dora(mjai_pai_to_tile37(dora_marker))

    def dump(self) :
        return self.game_elem

    def to_feature(self, player_id) :
        return self.game_elem.to_feature(player_id)

class Mj2Vec :
    def __init__(self) :
        self.sparse2vec = Sparse2Vec()
        self.players2vec = Players2Vec()
        self.features = []

    def process_records(self, records) :
        for i in range(len(records) - 1) :
            record = records[i] 
            next_record = records[i + 1]
            self.action(record, next_record)

    def action(self, record, next_record) :
        print(f"{record} -> {next_record}")

        # actual action to previous feature
        next_player_id = -1
        record_type = record["type"]
        next_record_type = next_record["type"]
        if "ryukyoku" == next_record_type :
            if next_record["reason"] == "kyushukyuhai" :
                assert(record_type == "tsumo")
                next_player_id = record["actor"]
            else :
                pass # 他の流局
        elif "dahai" == next_record_type :
            if "pon" == record_type:
                """
                [Fix]ponした後の打牌がtsumogiri = Trueになってしまうレコードを常にFalseに修正
                """
                next_record["tsumogiri"] = False
                
        if "actor" in next_record :
            next_player_id = next_record["actor"]

        # current feature
        self.sparse2vec.action(record)
        self.players2vec.action(record)
        
        """
        [FIXME]
        mjaiが出力するmjsonのaction順序は異なっている
        正しくはdaiminkan, kakan時は打牌した後にドラがめくれる
        即めくりする暗槓では本現象が発生しない
        
        暫定的にnextがdoraの場合は無視することにする
        現在のactionがdoraの場合はtsumoと同じ扱いにする
        
        - 加槓
            mjaiの動作 : (daiminkan|kakan) -> tsumo -> dahai -> dora
            mjson     : (daiminkan|kakan) -> tsumo -> dora -> dahai

        @ref https://gimite.net/pukiwiki/index.php?Mjai%20%E9%BA%BB%E9%9B%80AI%E5%AF%BE%E6%88%A6%E3%82%B5%E3%83%BC%E3%83%90
        """
        if record_type in ("dahai", "tsumo", "reach", "pon", "daiminkan", "ankan", "kakan", "nukidora", "hora", "ryukyoku", "dora") \
            and next_record_type != "dora" : 
            for player_id in range(3) :
                possible_actions = self.players2vec.get_possible_action_elem(player_id)
                if len(possible_actions) > 1 : # 選択肢が発生したとき、状態を保存する。
                    player_elem = self.players2vec.get_player_elem(player_id)

                    # sparse feature
                    sparse_feature = self.sparse2vec.to_feature(player_id) \
                                    + player_elem.to_sparse_feature()
                    print(f"sparse[{player_id}] : {sparse_feature}")

                    # numeric feature
                    numeric_feature = player_elem.scores
                    print(f"numeric : {numeric_feature}")

                    # progression feature
                    progression_feature = self.players2vec.progression_feature(player_id)
                    print(f"progression : {progression_feature}")

                    # possible_action feature
                    possible_feature = self.players2vec.to_possible_feature(player_id)
                    print(f"possible : {possible_feature}")

                    # actual
                    if next_record_type in ("tsumo", "reach_accepted") :
                        # 選択肢が発生している、かつ、next_actionがtsumo/reach_acceptedの場合はskipしていたことになる
                        actual_elem = ActionElem(type = "skip", value = 0)
                    elif next_player_id != player_id :
                        # 選択肢が発生している、かつ、次のplayerが自分でない場合はskipしていたことになる
                        actual_elem = ActionElem(type = "skip", value = 0)
                    else :
                        actual_elem = ActionElem.from_mjai(next_record)
                        assert actual_elem is not None, f"next record is invalid({next_record})"

                    # @debug
                    possible_elems = self.players2vec.get_possible_action_elem(player_id) # @debug
                    print(f"possible_elems:{possible_elems}") # @debug
                    print(f"actual_elem:{actual_elem}") # @debug

                    actual_label = ActionElem.possible_action_feature(actual_elem)
                    print(f"actual : {actual_label}")

                    assert actual_label in possible_feature, f"invalid actual feature {actual_label}"

                    feature = Features(uuid = self.sparse2vec.uri,
                            sparse = sparse_feature,
                            numeric = numeric_feature,
                            progression = progression_feature,
                            possible = possible_feature,
                            actual = actual_label)
                    self.features.append(feature)
    def savenpz(self, dir_name) :
        output_dir = Path(dir_name)
        
        sparse_list = []
        numeric_list = []
        progression_list = []
        possible_list = []
        actual_list = []
        for feature in self.features :
            sparse_list.append(feature.sparse)
            numeric_list.append(feature.numeric)
            progression_list.append(feature.progression)
            possible_list.append(feature.possible)
            actual_list.append(feature.actual)

        m = re.search("\d{10}gm-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{8}", feature.uuid)
        filename = m.group(0) + ".npz"
        
        np.savez_compressed(output_dir / filename, 
                sparse = np.array(sparse_list),
                numeric = np.array(numeric_list),
                progression = np.array(progression_list),
                possible = np.array(possible_list),
                actual = np.array(actual_list)
        )
    def save_to_text(self, dir_name) :
        output_dir = Path(dir_name)
        content = ""
        for feature in self.features :
            m = re.search("\d{10}gm-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{8}", feature.uuid)
            filename = m.group(0) + ".txt"
            output_path = output_dir / filename
            content += join_num(feature.sparse)  + "\t" \
                + join_num(feature.numeric) + "\t" \
                + join_num(feature.progression) + "\t" \
                + join_num(feature.possible) + "\t" \
                + str(feature.actual) + "\n"
        with open(output_path, mode = 'w', encoding = 'utf-8') as file :
            file.write(content)

def join_num(num_list) :
    return ",".join([str(n) for n in num_list])

def main() :
    parser = argparse.ArgumentParser()
    parser.add_argument("mjson_filename")
    parser.add_argument("save_dir_name", default = ".")
    args = parser.parse_args()
    
    filename = args.mjson_filename

    mj2vec = Mj2Vec()
    records = load_mjai_records(filename)
    mj2vec.process_records(records)
    mj2vec.savenpz(args.save_dir_name)

if __name__ == '__main__':
    main()
