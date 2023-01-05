from argparse import ArgumentParser
import torch

def argparse():
    parser = ArgumentParser(description='View pl checkpoint ')
    parser.add_argument('ckpt_path', type=str)
    args, _ = parser.parse_known_args()
    return args

def main(args):
    ckpt_path = args.ckpt_path

    ckpt = torch.load(ckpt_path, map_location=torch.device('cpu'))
    print("epoch:",ckpt["epoch"], "global_step:", ckpt["global_step"])
    print(ckpt.keys())
    state_dict = ckpt['state_dict']
    print(state_dict.keys())
    #state_dict = {'.'.join(k.split('.')[2:]): v for k, v in state_dict.items()}
    # print("---")
    # print(state_dict.keys())

if __name__ == '__main__':
    args = argparse()
    main(args)