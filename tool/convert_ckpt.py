from argparse import ArgumentParser
from pathlib import Path

import torch.nn as nn
import torch
from transformers import BertConfig, BertForMaskedLM, BertModel, BertForSequenceClassification


# from src.model.bert import config
TRAIN_POSSIBLE_LABEL_COUNT = 219 # label count

TRAIN_TOKEN_CLS     = 0
TRAIN_TOKEN_SEP     = 1
TRAIN_TOKEN_PADDING = 2 + 382 + 648 + 219 # 2(CLS,SEP)+382(sparse)+648(progression)+219(possible)
TRAIN_TOKEN_MASK    = TRAIN_TOKEN_PADDING + 1

TRAIN_TOKEN_VOCAB_COUNT = TRAIN_TOKEN_PADDING + 2 # 2(PADDING, MASK)
TRAIN_MAX_TOKEN_LENGTH = 2 + 139 + 1 # 26(sparse)+81(progression)+32(possible)
TRAIN_ID_LIST = list(range(2, TRAIN_TOKEN_PADDING))

TRAIN_HIDDEN_SIZE = 768
TRAIN_MLM_CONFIG = {
    'vocab_size': TRAIN_TOKEN_VOCAB_COUNT,  # MASK_TOKEN_ID, MASK, CLS, SEP
    'hidden_size': TRAIN_HIDDEN_SIZE,
    'num_hidden_layers': 12,
    'num_attention_heads': 12,
    'intermediate_size': 3072,  # hidden_size * 4が目安
    'hidden_act': 'gelu',
    'hidden_dropout_prob': 0.1,
    'attention_probs_dropout_prob': 0.1,
    'max_position_embeddings': 512,  # 95(=81(マス目)+7(先手持駒)+7(後手持駒))でいいかも
    'type_vocab_size': 1,  # 対の文章を入れない。つまりtoken_type_embeddingsは完全に無駄になっている。
    'initializer_range': 0.02,
}
TRAIN_CLASSIFICATION_CONFIG = {
    'vocab_size': TRAIN_TOKEN_VOCAB_COUNT,  # MASK_TOKEN_ID, MASK, CLS, SEP
    'hidden_size': TRAIN_HIDDEN_SIZE,
    'num_hidden_layers': 12,
    'num_attention_heads': 12,
    'intermediate_size': 3072,  # hidden_size * 4が目安
    'hidden_act': 'gelu',
    'hidden_dropout_prob': 0.1,
    'attention_probs_dropout_prob': 0.1,
    'max_position_embeddings': 512,  # 95(=81(マス目)+7(先手持駒)+7(後手持駒))でいいかも
    'type_vocab_size': 1,  # 対の文章を入れない。つまりtoken_type_embeddingsは完全に無駄になっている。
    'initializer_range': 0.02,
    'num_labels' : TRAIN_POSSIBLE_LABEL_COUNT, 
}
config = BertConfig.from_dict(TRAIN_MLM_CONFIG)
BERT_CLASSIFICATION_CONFIG = BertConfig.from_dict(TRAIN_CLASSIFICATION_CONFIG)


def argparse():
    parser = ArgumentParser(description='Convert pl checkpoint to transformers format')
    parser.add_argument('ckpt_path', type=str)
    parser.add_argument('-o', '--output', type=str, default = "pytorch_model.bin")
    args, _ = parser.parse_known_args()
    return args

def main(args):
    ckpt_path = Path(args.ckpt_path)
    ckpt_dir = ckpt_path.parent
    state_dict_path = args.output

    ckpt = torch.load(ckpt_path, map_location=torch.device('cpu'))
    print(ckpt.keys())
    state_dict = ckpt['state_dict']
    # print(state_dict.keys())
    state_dict = {'.'.join(k.split('.')[2:]): v for k, v in state_dict.items()}
    # print("---")
    # print(state_dict.keys())

    # 同一ディレクトリにpytorch_model.binとconfig.jsonが必要
    # state_dict_path = ckpt_dir / f'pytorch_model.bin'
    torch.save(state_dict, state_dict_path)
    # config.to_json_file(ckpt_dir / 'config.json')


if __name__ == '__main__':
    args = argparse()
    main(args)
