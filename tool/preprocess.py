"""
 preprocess.py
"""
import json
import argparse
from features.mjai_encoder import MjaiEncoderClient, Action

def load_mjai_records(filename) :
    records = []
    log_input_file = open(filename, 'r', encoding="utf-8")
    for line in log_input_file :
        mjai_ev = json.loads(line)
        records.append(mjai_ev)
    log_input_file.close()
    return records

def fix_records(records) :
    """
    mjai牌譜をルールベースで修正する
    本関数は引数で与えられた配列を破壊的に変更する
    """
    for idx, record in enumerate(records) :
        """
        mjaiが出力するmjsonのaction順序は異なっている
        正しくはdaiminkan, kakan時は打牌した後にドラがめくれる
        即めくりする暗槓では本現象が発生しない
        
        暫定的にnextがdoraの場合は無視することにする
        現在のactionがdoraの場合はtsumoと同じ扱いにする
        
        - 例(加カン)
            (x) mjson     : [daiminkan,kakan] -> tsumo -> dora -> dahai
            (o) mjai      : [daiminkan,kakan] -> tsumo -> dahai -> dora

        @ref https://gimite.net/pukiwiki/index.php?Mjai%20%E9%BA%BB%E9%9B%80AI%E5%AF%BE%E6%88%A6%E3%82%B5%E3%83%BC%E3%83%90
        """
        if record["type"] in ("daiminkan", "kakan") and idx < len(records) - 3 :
            tsumo, dora, dahai = records[idx + 1 : idx + 4]
            if tsumo["type"] == "tsumo" and dora["type"] == "dora" and dahai["type"] == "dahai" :
                records[idx + 2 : idx + 4] = records[idx + 3 : idx + 1 : -1] # swap
        
        """
        mjaiで副露後の打牌がtsumogiri = Trueになった場合、tsumogiri = Falseに直す.
        """
        if record["type"] == "pon" :
            next_record = records[idx + 1]
            if next_record["type"] == "dahai" :
                next_record["tsumogiri"] = False
    return records

def process_records(records) :
    mj_client = MjaiEncoderClient()
    train_data = []
    for i in range(len(records) - 1) :
        record = records[i]
        mj_client.update(record)

        """
        手番(動作決定点)
        - 自家のツモ番後
        - 他家の打牌後
        - 他家の抜きドラ後
        - 他家の暗槓後(槍槓)
        """
        for player_id in range(3) :
            if record["type"] == "tsumo" and record["actor"] == player_id :
                # 自家のツモ番後
                next_record = next_record = next((r for r in records[i + 1:] if r["type"] in ("dahai", "reach", "hora", "ankan", "kakan", "nukidora", "ryukyoku")), None)
                actual = Action.encode(next_record)

                # 意思決定ポイントを追加
                train_data.append((mj_client.encode(player_id), actual))

            elif record["type"] == "dahai" and record["actor"] != player_id :
                # 次アクションを選択
                next_record = next((r for r in records[i + 1:] if r["type"] in ("pon", "daiminkan", "hora")), None)
                # playerが選択しないactionは学習しない
                if next_record is not None and "actor" in next_record :
                    # 他家の打牌後
                    if next_record["type"] in ("tsumo") :# Skip選択
                        actual = Action.encode({"type" : "none"}) 
                    elif player_id != next_record["actor"] : # Skip選択
                        actual = Action.encode({"type" : "none"})
                    else :
                        actual = Action.encode(next_record)
                    
                    # 意思決定ポイントを追加
                    train_data.append((mj_client.encode(player_id), actual))

            elif record["type"] in ("ankan", "kakan", "nukidora") and record["actor"] != player_id :
                next_record = records[i + 1]
                if next_record["type"] == "hora" and next_record["actor"] == player_id :
                    actual = Action.encode(next_record)
                else : # Skip選択
                    actual = Action.encode({"type" : "none"})

                # 意思決定ポイントを追加
                train_data.append((mj_client.encode(player_id), actual))

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
