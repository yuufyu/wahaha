"""
 augmentation
"""
import argparse
import json
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

def create_convert_func(swap_ps = False, swap_manzu = False, shift_sangen = 0) :
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
    convert_func = create_convert_func(*args, **kwargs)
    
    def convert_pais(pais) :
        if isinstance(pais, list) :
            res = list(map(convert_pais, pais))
        else :
            res = convert_func(pais)
        return res
        
    for record in aug_records :
        for key, value in record.items() :
            if key in ("pai", "consumed", "tehais", "dora_marker", "uradora_markers", "hora_tehais") :
                record[key] = convert_pais(value)

    return aug_records

def main() :
    parser = argparse.ArgumentParser()
    parser.add_argument("mjson_filename",metavar='mjson')
    parser.add_argument("--swap_ps", action = "store_true")
    parser.add_argument("--swap_manzu", action = "store_true")
    parser.add_argument("--shift_sangen", type = int, choices = [0, 1, 2], default = 0)

    args = parser.parse_args()
    filename = args.mjson_filename
    pattern = {'swap_ps' : args.swap_ps, 'swap_manzu' : args.swap_manzu, 'shift_sangen' : args.shift_sangen}

    records = load_mjai_records(filename)
    fix_records(records)
    aug_records = augmentation_records(records, **pattern)
    
    mjson_str = "\n".join([json.dumps(record) for record in aug_records])
    
    print(mjson_str)
   
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
        converter = create_convert_func(**pattern)
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
