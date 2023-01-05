"""
preprocess
"""
import argparse
from pathlib import Path
import shutil
from .preprocess import load_mjai_records, fix_records
# from features.mjai_encoder import MjaiEncoderClient, Action

def stat_records(records) :
    # 立直しないで連続ツモ切りした回数
    result_kyoku = []
    game_stat = []
    for i, record in enumerate(records) :
        if record["type"] == "start_game" :
            player_count = len(record["names"])
        elif record["type"] == "start_kyoku" :
            tsumogiri_counts = [0] * player_count
            max_tsumogiri_counts = [0] * player_count
            reach_stat = [False] * player_count
        elif record["type"] == "reach" :
            actor = record["actor"]
            reach_stat[actor] = True
        elif record["type"] == "dahai" :
            actor = record["actor"]
            tsumogiri = record["tsumogiri"]
            if tsumogiri and reach_stat[actor] == False :
                tsumogiri_counts[actor] += 1
            else :
                max_tsumogiri_counts[actor] = max(max_tsumogiri_counts[actor], tsumogiri_counts[actor])
                tsumogiri_counts[actor] = 0 #reset
        elif record["type"] == "end_kyoku" :
            game_stat.append(max_tsumogiri_counts)

    # print(result_kyoku)
    # print(game_stat)
    return game_stat


def main() :
    parser = argparse.ArgumentParser()
    # parser.add_argument("mjson_filenames",metavar='mjson',nargs='+')
    parser.add_argument("mjson_directory")
    args = parser.parse_args()
    dir_path = args.mjson_directory

    max_tsumogiri_stat = [0] * 28

    for filename in Path(dir_path).glob("*.mjson") :
        records = load_mjai_records(filename)
        fix_records(records)
        stat = stat_records(records)

        max_tsumogiri_game_count = 0
        for kyoku_stat in stat :
            max_tsumogiri_kyoku_count = max(kyoku_stat)
            max_tsumogiri_stat[max_tsumogiri_kyoku_count] += 1

            max_tsumogiri_game_count = max(max_tsumogiri_game_count, max_tsumogiri_kyoku_count)

        if max_tsumogiri_game_count > 10 :
            print(filename)
            print("max tsumogiri(w/o reach):", max_tsumogiri_game_count)
            print(stat)
if __name__ == '__main__':
    main()

