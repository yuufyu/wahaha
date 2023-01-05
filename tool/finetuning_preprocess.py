"""
 preprocess.py
"""
import argparse
from features.mjai_encoder import MjaiEncoderClient, RecordAction
from .preprocess import load_mjai_records, fix_records

"""
 fine-tuning ネタ

 - 順位予想
 - 和了形予想
 - 合法手生成
"""
def process_records(records) :
    mj_client = MjaiEncoderClient()
    train_data = []
    for i in range(len(records) - 1) :
        record = records[i]
        mj_client.update(record)

        """
        手番(意思決定ポイント)
        - 自家のツモ番後
        - 他家の打牌後
        - 他家の抜きドラ後
        - 他家の暗槓後(槍槓)
        """
        # for player_id in range(3) :
            # if record["type"] == "tsumo" and record["actor"] == player_id :
            #     # 自家のツモ番後
            #     next_record = next_record = next((r for r in records[i + 1:] if r["type"] in ("dahai", "reach", "hora", "ankan", "kakan", "nukidora", "ryukyoku")), None)
            #     actual = Action.encode(next_record)

            #     # 意思決定ポイントを追加
            #     train_data.append((mj_client.encode(player_id), actual))

            # elif record["type"] == "dahai" and record["actor"] != player_id :
            #     # 次アクションを選択
            #     next_record = next((r for r in records[i + 1:] if r["type"] in ("pon", "daiminkan", "hora")), None)
            #     # playerが選択しないactionは学習しない
            #     if next_record is not None and "actor" in next_record :
            #         # 他家の打牌後
            #         if next_record["type"] in ("tsumo") :# Skip選択
            #             actual = Action.encode({"type" : "none"}) 
            #         elif player_id != next_record["actor"] : # Skip選択
            #             actual = Action.encode({"type" : "none"})
            #         else :
            #             actual = Action.encode(next_record)
                    
            #         # 意思決定ポイントを追加
            #         train_data.append((mj_client.encode(player_id), actual))

            # elif record["type"] in ("ankan", "kakan", "nukidora") and record["actor"] != player_id :
            #     next_record = records[i + 1]
            #     if next_record["type"] == "hora" and next_record["actor"] == player_id :
            #         actual = Action.encode(next_record)
            #     else : # Skip選択
            #         actual = Action.encode({"type" : "none"})

            #     # 意思決定ポイントを追加
            #     train_data.append((mj_client.encode(player_id), actual))

    return train_data

def main() :
    parser = argparse.ArgumentParser()
    parser.add_argument("mjson_filename")
    args = parser.parse_args()
    
    filename = args.mjson_filename

    records = load_mjai_records(filename)
    fix_records(records)
    train_list = process_records(records)
    
    """
     [空白区切りデータ], [ラベル]
    """
    for train_data in train_list :
        line = " ".join([str(n) for n in train_data[0]]) + "," + str(train_data[1])
        print(line)

if __name__ == '__main__':
    main()
