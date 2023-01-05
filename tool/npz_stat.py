import argparse
import numpy as np
from sklearn.metrics import precision_score,confusion_matrix

def join_num(num_list) :
    return ",".join([str(n) for n in num_list])

def npz_stat(filename) :
    npz_arr = np.load(filename, allow_pickle=True)
    input_ids = npz_arr["arr_0"]
    labels = npz_arr["arr_1"]
    preds = npz_arr["arr_2"]
    # print("input:", input_ids.shape, input_ids)
    print("label:", labels.shape, labels)
    # print("pred :", preds.shape, preds)

    hist = np.bincount(labels)
    hist_pred = np.bincount(preds)
    pre_score = precision_score(labels, preds, labels = range(0,112), average = None)
    for i, (count, count_pred, score) in enumerate(zip(hist, hist_pred, pre_score)) :
        print(f"{i}\t{count}\t{count_pred}\t{score}")

    conf = confusion_matrix(labels, preds, labels = range(0,112))
    print(conf)

    # s = precision_score(labels, preds, labels = range(0,112), average = "micro")
    # print(s)
    


def main() :
    parser = argparse.ArgumentParser()
    parser.add_argument("npz_filename")
    args = parser.parse_args()
    
    filename = args.npz_filename
    npz_stat(filename)

if __name__ == '__main__':
    main()