import numpy as np
import torch
import torch.nn as nn
from transformers import BertConfig, BertForMaskedLM, BertModel, BertForSequenceClassification
from torchinfo import summary

TRAIN_TOKEN_VOCAB_COUNT = 1200 # 2(PADDING, MASK)
TRAIN_MAX_TOKEN_LENGTH = 2 + 139 + 1 # 26(sparse)+81(progression)+32(possible)

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
    'num_labels' : 500, 
}
BERT_MLM_CONFIG = BertConfig.from_dict(TRAIN_MLM_CONFIG)
BERT_CLASSIFICATION_CONFIG = BertConfig.from_dict(TRAIN_CLASSIFICATION_CONFIG)

def printBertClassification() :
    model = BertForSequenceClassification(BERT_CLASSIFICATION_CONFIG)
    inshape = (1, 10)
    label = torch.LongTensor(np.array([[0]]))
    summary(model, input_size=inshape, labels = label , dtypes=[torch.long], depth = 4)

def printBertForMaskedLM() :
    model = BertForMaskedLM(BERT_MLM_CONFIG)
    inshape = (1, 10)
    label = torch.LongTensor(np.array([[0]*10]))
    summary(model, input_size=inshape, labels = label , dtypes=[torch.long], depth = 4)

def main() :
    printBertClassification()
    printBertForMaskedLM()

if __name__ == '__main__':
    main()