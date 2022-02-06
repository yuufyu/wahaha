import argparse
import numpy as np
from sklearn.metrics import precision_score

def join_num(num_list) :
    return ",".join([str(n) for n in num_list])

def npz2txt(filename) :
    npz_arr = np.load(filename, allow_pickle=True)
    input_ids = npz_arr["arr_0"]
    labels = npz_arr["arr_1"]
    preds = npz_arr["arr_2"]
    print("input:", input_ids.shape, input_ids)
    print("label:", labels.shape, labels)
    print("pred :", preds.shape, preds)

    pre_score = precision_score(labels, preds, average = None)
    print(pre_score)


def main() :
    parser = argparse.ArgumentParser()
    parser.add_argument("npz_filename")
    args = parser.parse_args()
    
    filename = args.npz_filename
    npz2txt(filename)

if __name__ == '__main__':
    main()