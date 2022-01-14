"""
 preprocess.py
"""
import json
import argparse
from features.simple_encoder import MjaiEncoderClient, Action

def load_mjai_records(filename) :
    records = []
    log_input_file = open(filename, 'r', encoding="utf-8")
    for line in log_input_file :
        mjai_ev = json.loads(line)
        records.append(mjai_ev)
    log_input_file.close()
    return records

def process_records(records) :
    mj_client = MjaiEncoderClient()
    train_data = []
    for i in range(len(records) - 1) :
        record = records[i]
        mj_client.update(record)
        
        for player_id in range(3) :
            # MjaiPossibleActionGeneratorは複数playerのactionを返すことができないため、player数分呼び出す必要がある
            possible_actions = mj_client.possible_player_action(player_id)

            # playerに選択肢が発生したとき
            if len(possible_actions) > 1 :
                next_record = records[i + 1]

                # playerが選択しないactionは学習しない(dora etc..)
                if not("actor" in next_record) :
                    continue
                
                if next_record["type"] in ("tsumo", "reach_accepted") :# Skip選択
                    actual = Action.encode({"type" : "none"}) 
                elif player_id != next_record["actor"] : # Skip選択
                    actual = Action.encode({"type" : "none"})
                else :
                    """
                    [NOTE] 副露した後の打牌がtsumogiri = Trueになることがあるため、tsumogiri = Falseに直す。
                    MjStateで同じ処理を行っているが、MjState単独での使用を想定して両方とも残す。
                    """
                    if next_record["type"] == "dahai" and record["type"] in ("pon", "daiminkan") :
                        next_record["tsumogiri"] = False

                    actual = Action.encode(next_record)

                # feature
                feature = mj_client.encode(player_id)

                train_data.append((feature, actual))

    return train_data

def main() :
    parser = argparse.ArgumentParser()
    parser.add_argument("mjson_filename")
    args = parser.parse_args()
    
    filename = args.mjson_filename

    records = load_mjai_records(filename)
    train_list = process_records(records)
    
    """
     [空白区切りデータ], [ラベル]
    """
    for train_data in train_list :
        line = " ".join([str(n) for n in train_data[0]]) + "," + str(train_data[1])
        print(line)

if __name__ == '__main__':
    main()
