import argparse
import pathlib
import numpy as np

from features.mj2vec import SPARSE_FEATURE_PADDING, PROGRESSION_FEATURE_PADDING, POSSIBLE_FEATURE_PADDING

def join_num(num_list) :
    return ",".join([str(n) for n in num_list])

def npz2txt(filename) :
    uuid = pathlib.Path(filename).stem
    npz_arr = np.load(filename, allow_pickle=True)
    sparse_list = npz_arr['sparse']
    numeric_list = npz_arr['numeric']
    progression_list = npz_arr['progression']
    possible_list = npz_arr['possible']
    actual_list = npz_arr['actual']
    list_length = sparse_list.shape[0]
    for i in range(list_length) :
        sparse = sparse_list[i]
        numeric = numeric_list[i]
        progression = progression_list[i]
        possible = possible_list[i]
        actual = actual_list[i]
        actual_index = possible.index(actual)
        line = uuid + "\t" + join_num(sparse)  + "\t" \
                + join_num(numeric) + "\t" \
                + join_num(progression) + "\t" \
                + join_num(possible) + "\t" \
                + str(actual_index) + "\t" \
                + "0,1,2,3" # dummy result
        print(line)

def npz2txt_bert(filename) :
    uuid = pathlib.Path(filename).stem
    npz_arr = np.load(filename, allow_pickle=True)
    sparse_list = npz_arr['sparse']
    # numeric_list = npz_arr['numeric'] # unused
    progression_list = npz_arr['progression']
    possible_list = npz_arr['possible']
    actual_list = npz_arr['actual']
    list_length = sparse_list.shape[0]

    for i in range(list_length) :
        sparse = sparse_list[i]
        # numeric = numeric_list[i] # unused
        progression = [num + SPARSE_FEATURE_PADDING for num in progression_list[i]]
        possible =    [num + SPARSE_FEATURE_PADDING + PROGRESSION_FEATURE_PADDING for num in possible_list[i]]
        actual = actual_list[i]

        assert all([0 <= num and num < SPARSE_FEATURE_PADDING for num in sparse]), f"{uuid} : sparse is invalid ({sparse})"
        assert all([SPARSE_FEATURE_PADDING <= num and num < SPARSE_FEATURE_PADDING + PROGRESSION_FEATURE_PADDING for num in progression]), f"{uuid} : progression is invalid ({progression})"
        assert all([SPARSE_FEATURE_PADDING + PROGRESSION_FEATURE_PADDING <= num and num < SPARSE_FEATURE_PADDING + PROGRESSION_FEATURE_PADDING + POSSIBLE_FEATURE_PADDING for num in possible]), f"{uuid} : possible is invalid ({possible})"

        # Output text format : 
        # [uuid]\t[train_num]\t[label]\n
        line = uuid + "\t" + join_num(sparse + progression + possible) + "\t" + str(actual)
        print(line)

def main() :
    parser = argparse.ArgumentParser()
    parser.add_argument("npz_filename")
    parser.add_argument("--output-type", default="kanachan", choices=("kanachan", "bert"))
    args = parser.parse_args()
    
    filename = args.npz_filename
    if args.output_type == "kanachan" :
        npz2txt(filename)
    elif args.output_type == "bert" :
        npz2txt_bert(filename)

if __name__ == '__main__':
    main()