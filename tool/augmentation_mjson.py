"""
preprocess
"""
import argparse
from pathlib import Path
import copy
import shutil
from .preprocess import load_mjai_records, fix_records

def convert_pai_sangen(pai, shift_count) :
    # 三元牌をシフト
    SANGENPAI = ["P", "F", "C"]
    if pai in SANGENPAI :
        idx = SANGENPAI.index(pai)
        pai = SANGENPAI[(idx + shift_count) % len(SANGENPAI)]
    return pai

def convert_pai_swap_ps(pai) :
    # ピンズとソーズを入れ替え
    if pai.find("p") > 0 :
        pai = pai.replace("p", "s")
    elif pai.find("s") > 0 :
        pai = pai.replace("s", "p")
    return pai

def convert_pai_manzu(pai) :
    # サンマのみ: 1mと9mを入れ替え
    MANZU_TABLE = {"1m" : "9m", "9m" : "1m"}
    if pai in MANZU_TABLE :
        pai = MANZU_TABLE[pai]
    return pai

def create_converter(swap_ps = False, swap_manzu = False, shift_sangen = 0) :
    # 関数を合成して牌変換関数を作成する
    res = lambda p : convert_pai_sangen(p, shift_sangen)
    if swap_ps :
        f = res
        res = lambda p : convert_pai_swap_ps(f(p))
    if swap_manzu :
        f_ = res
        res = lambda p : convert_pai_manzu(f_(p))
    return res

def augmentation_records(records, *args, **kwargs) :
    aug_records = copy.deepcopy(records)
    converter = create_converter(*args, **kwargs)

    for record in aug_records :
        if "tehais" in record :
            tehais = record["tehais"]
            record["tehais"] = [list(map(converter, tehai)) for tehai in tehais]
        if "pai" in record :
            record["pai"] = converter(record["pai"])
        if "dora_marker" in record :
            record["dora_marker"] = converter(record["dora_marker"]) 
        if "consumed" in record :
            record["consumed"] = list(map(converter, record["consumed"]))

        print(record)
    return aug_records

def main() :
    parser = argparse.ArgumentParser()
    parser.add_argument("mjson_filenames",metavar='mjson',nargs='+')
    # parser.add_argument("input_mjson_directory")
    parser.add_argument("--swap_ps", type = bool, default = False)
    parser.add_argument("--swap_manzu", type = bool, default = False)
    parser.add_argument("--shift_sangen", type = int, choices = [0, 1, 2], default = 0)
    args = parser.parse_args()
    filenames = args.mjson_filenames
    for filename in filenames :
        pattern = {'swap_ps' : args.swap_ps, 'swap_manzu' : args.swap_manzu, 'shift_sangen' : args.shift_sangen}

        records = load_mjai_records(filename)
        fix_records(records)
        aug_records = augmentation_records(records, **pattern)

   
#    for filename in Path(dir_path).glob("*.mjson") :
#        records = load_mjai_records(filename)
#        fix_records(records)
#        aug_records = augmentation_records(records, **pattern)

def test() : 
    TEST_PATTERN = [
        {"swap_ps" : False, "swap_manzu" : False, "shift_sangen" : 0},
        {"swap_ps" : False, "swap_manzu" : True, "shift_sangen" : 0},
        {"swap_ps" : True, "swap_manzu" : False, "shift_sangen" : 0},
        {"swap_ps" : True, "swap_manzu" : True, "shift_sangen" : 0},
        {"swap_ps" : False, "swap_manzu" : False, "shift_sangen" : 1},
        {"swap_ps" : False, "swap_manzu" : True, "shift_sangen" : 2},
    ]
    print_convert = lambda p : print(p , "=>", converter(p) )
    for pattern in TEST_PATTERN :
        converter = create_converter(**pattern)
        print(pattern)
        print_convert("1m")
        print_convert("9m")
        print_convert("1p")
        print_convert("1s")
        print_convert("5pr")
        print_convert("5sr")
        print_convert("E")
        print_convert("P")
        print_convert("F")
        print_convert("C")

if __name__ == '__main__':
    main()
