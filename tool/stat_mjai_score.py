""" 
 stat_mjai_score.py

"""

import json
import argparse
import os
import glob
import dataclasses

NUM_PLAYERS = 3

RESULT_HORA = 1
RESULT_RYUKYOKU = 2

@dataclasses.dataclass
class KyokuResult :
    result_type : int = 0
    
    bakaze      : str = None
    kyoku       : int = 0
    honba       : int = 0
    result_mjson : json = None

@dataclasses.dataclass
class GameResult :
    uuid : str = None
    results : list = None
    names   : list = None

@dataclasses.dataclass
class PlayerResult :
    count_kyoku : int   = 0
    count_game  : int   = 0 
    count_reach : int   = 0
    count_furo  : int   = 0
    count_furo_kyoku : int = 0
    count_hora  : int   = 0
    count_baojia: int   = 0 # 放銃
    count_draw  : int   = 0
    count_tenpai_draw : int = 0
    count_tsumo : int   = 0
    total_score : int   = 0
    total_hora_score : int  = 0
    total_baojia_score : int = 0
    count_ranks : list = None

    @property
    def rate_hora(self) :
        return self.div(self.count_hora, self.count_kyoku)

    @property
    def rate_tsumo(self) :
        return self.div(self.count_tsumo, self.count_hora)

    @property
    def rate_dealin(self) :
        return self.div(self.count_baojia, self.count_kyoku)

    @property
    def rate_reach(self) :
        return self.div(self.count_reach, self.count_kyoku)

    @property
    def rate_furo(self) :
        return self.div(self.count_furo_kyoku, self.count_kyoku)
    
    @property
    def rate_draw(self) :
        return self.div(self.count_draw, self.count_kyoku)

    @property
    def rate_tenpai_draw(self) :
        return self.div(self.count_tenpai_draw, self.count_draw)

    @property
    def average_win_score(self) :
        return self.div(self.total_hora_score, self.count_hora)

    @property
    def average_baojia_score(self) :
        return self.div(self.total_baojia_score, self.count_baojia)

    @property
    def average_rank(self) :
        sum_rank = sum([(i+1) * count_rank for i, count_rank in enumerate(self.count_ranks)])
        count_game = sum(self.count_ranks)
        return self.div(sum_rank, count_game)

    def div(self, a, b) :
        return a / b if b > 0 else 0.0

    def __post_init__(self) :
        self.count_ranks = [0] * NUM_PLAYERS

    def __add__(self, other) :
        result = PlayerResult(
            count_kyoku = self.count_kyoku + other.count_kyoku,
            count_game = self.count_game + other.count_game,
            count_reach = self.count_reach + other.count_reach,
            count_furo = self.count_furo + other.count_furo,
            count_furo_kyoku = self.count_furo_kyoku + other.count_furo_kyoku,
            count_hora = self.count_hora + other.count_hora,
            count_baojia = self.count_baojia + other.count_baojia,
            count_draw = self.count_draw + other.count_draw,
            count_tenpai_draw = self.count_tenpai_draw + other.count_tenpai_draw,
            count_tsumo = self.count_tsumo + other.count_tsumo,
            total_score = self.total_score + other.total_score,
            total_hora_score = self.total_hora_score + other.total_hora_score,
            total_baojia_score = self.total_baojia_score + other.total_baojia_score,
        )
        result.count_ranks = [rank1 + rank2 for rank1, rank2 in zip(self.count_ranks, other.count_ranks)]
        return result

def merge_game_result(result1, result2) :
    game_result = {}
    names = result1.keys() | result2.keys()
    for name in names :
        res1 = result1[name] if (name in result1) else PlayerResult()
        res2 = result2[name] if (name in result2) else PlayerResult()
        game_result[name] = res1 + res2
    return game_result

def get_result_from_mjson(log_file) :
    result = {}
    game_result = None
    kyoku_result = None
    for line in log_file :
        action = json.loads(line)
        action_type = action["type"]
        if action_type == "start_game" :
            names = action["names"]
            for name in names :
                result[name] = PlayerResult()
            game_result = GameResult(uuid = "", names = names, results = [])
        elif action_type == "start_kyoku" :
            kyoku_result = KyokuResult(result_type=0, bakaze = action["bakaze"], kyoku = action["kyoku"], honba = action["honba"], result_mjson=action)
        elif action_type == "reach" :
            actor = action["actor"]
            result[names[actor]].count_reach += 1
        elif action_type in ("pon", "chi", "daiminkan") :
            actor = action["actor"]
            result[names[actor]].count_furo += 1
        elif action_type == "hora" :
            actor = action["actor"]
            target = action["target"]
            delta_scores = action["deltas"]
            result[names[actor]].count_hora += 1
            result[names[actor]].total_hora_score += delta_scores[actor]
            if actor != target :
                result[names[target]].count_baojia += 1
                result[names[target]].total_baojia_score += delta_scores[target]
            else :
                result[names[actor]].count_tsumo += 1

            kyoku_result.result_type = RESULT_HORA
            kyoku_result.result_mjson = action

        elif action_type == "end_kyoku" :
            for name in names :
                result[name].count_kyoku += 1
                if result[name].count_furo > 0 :
                    result[name].count_furo_kyoku += 1
                    result[name].count_furo = 0 # reset count
            game_result.results.append(kyoku_result)
        elif action_type == "ryukyoku" :
            tenpais = action["tenpais"]
            for i, name in enumerate(names) :
                result[name].count_draw += 1
                if tenpais[i] :
                    result[name].count_tenpai_draw += 1
            
            kyoku_result.result_type = RESULT_RYUKYOKU
            kyoku_result.result_mjson = action
            
        elif action_type == "end_game" :
            scores = action["scores"]

            # Calculate ranking by Mahjong rule
            range_indices = range(len(scores))
            sorted_indices = sorted(range_indices, key = scores.__getitem__, reverse = True)
            ranks = [0] * len(sorted_indices)
            for i, indices in enumerate(sorted_indices) :
                ranks[indices] = i

            for name, rank in zip(names, ranks) :
                result[name].count_game += 1
                result[name].count_ranks[rank] += 1
    return result, game_result

def print_player_result(name, player_result : PlayerResult) :
    count_ranks = player_result.count_ranks
    format_ranks = '\n'.join([ "  {}位       | {}".format(i + 1, count_rank ) for i, count_rank in enumerate(count_ranks)])

    format_str = """\
name        : {name}
---------------------------------------
対戦数        : {count_game}回
和了率      : {rate_hora:.2f}%
自摸率      : {rate_tsumo:.2f}%
平均得点    : {average_win_score:.2f}
平均放銃    : {average_baojia_score:.2f}
放銃率      : {rate_dealin:.2f}%
立直率      : {rate_reach:.2f}%
副露率      : {rate_furo:.2f}%
  順位      | 回数 
{format_ranks}
平均順位    : {average_rank:.2f}
流局率      : {rate_draw:.2f}%
流局時聴牌率: {rate_draw_tenpai:.2f}%
    """
    score_message = format_str.format(
        name = name,
        count_game = player_result.count_game,
        rate_hora   = player_result.rate_hora * 100,
        rate_tsumo  = player_result.rate_tsumo * 100,
        average_win_score = player_result.average_win_score,
        average_baojia_score = player_result.average_baojia_score,
        rate_dealin  = player_result.rate_dealin * 100,
        rate_reach  = player_result.rate_reach * 100,
        rate_furo   = player_result.rate_furo * 100,
        format_ranks = format_ranks,
        average_rank = player_result.average_rank,
        rate_draw   = player_result.rate_draw * 100,
        rate_draw_tenpai = player_result.rate_tenpai_draw * 100,
    )
    print(score_message)

def main(args) :
    log_dir = args.log_directory
    log_file_prefix = os.path.join(log_dir, '*.mjson')
    log_file_list = glob.glob(log_file_prefix)

    results = {}
    for log_file_name in log_file_list :
        log_file = open(log_file_name, 'r', encoding="utf-8")
        player_result, game_result = get_result_from_mjson(log_file)
        if all(res.count_game > 0 for name, res in player_result.items()) :
            results = merge_game_result(player_result, results)

        if args.print_result :
            print(f"file : {log_file_name}")
            for kyoku_result in game_result.results :
                action = kyoku_result.result_mjson
                print("-------------------------------------")
                print(f"{kyoku_result.bakaze}, {kyoku_result.kyoku}, {kyoku_result.honba}")
                if kyoku_result.result_type == RESULT_HORA :
                    res = f"""\
result : {'ツモ' if action["actor"] == action["target"] else 'ロン'}
scores : {action['scores']}
yaku   : {action['yakus']} \
"""
                elif kyoku_result.result_type == RESULT_RYUKYOKU :
                    res = f"result : 流局 "
                print(res)
                
        log_file.close()
    
    for name, res in results.items() :
        print_player_result(name, res)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = "Statistics mjai records.")
    parser.add_argument('log_directory', help = "mjai log directory")
    parser.add_argument('--print_result', action="store_true")
    args = parser.parse_args()
    main(args)
