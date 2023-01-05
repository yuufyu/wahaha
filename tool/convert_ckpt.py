from argparse import ArgumentParser
from pathlib import Path

import torch

def argparse():
    parser = ArgumentParser(description='Convert pl checkpoint to transformers format')
    parser.add_argument('ckpt_path', type=str)
    parser.add_argument('-o', '--output', type=str, default = "pytorch_model.bin")
    args, _ = parser.parse_known_args()
    return args

def main(args):
    ckpt_path = Path(args.ckpt_path)
    # ckpt_dir = ckpt_path.parent
    state_dict_path = args.output

    ckpt = torch.load(ckpt_path, map_location=torch.device('cpu'))
    print(ckpt.keys())
    state_dict = ckpt['state_dict']
    print(state_dict.keys())
    # state_dict = {'.'.join(k.split('.')[2:]): v for k, v in state_dict.items()}
    state_dict = {'.'.join(k.split('.')[1:]): v for k, v in state_dict.items()}
    # print("---")
    print(state_dict.keys())

    # 同一ディレクトリにpytorch_model.binとconfig.jsonが必要
    # state_dict_path = ckpt_dir / f'pytorch_model.bin'
    torch.save(state_dict, state_dict_path)
    # config.to_json_file(ckpt_dir / 'config.json')


if __name__ == '__main__':
    args = argparse()
    main(args)
