import torch
from transformers import BertConfig, BertForSequenceClassification

TRAIN_POSSIBLE_LABEL_COUNT = 219 # label count

TRAIN_TOKEN_CLS     = 0
TRAIN_TOKEN_SEP     = 1
TRAIN_TOKEN_PADDING = 2 + 382 + 648 + 219 # 2(CLS,SEP)+382(sparse)+648(progression)+219(possible)
TRAIN_TOKEN_MASK    = TRAIN_TOKEN_PADDING + 1

TRAIN_TOKEN_VOCAB_COUNT = TRAIN_TOKEN_PADDING + 2 # 2(PADDING, MASK
TRAIN_HIDDEN_SIZE = 768

BERT_CONFIG = {
    'vocab_size': TRAIN_TOKEN_VOCAB_COUNT,  # MASK_TOKEN_ID, MASK, CLS, SEP
    'hidden_size': TRAIN_HIDDEN_SIZE,
    'num_hidden_layers': 12,
    'num_attention_heads': 12,
    'intermediate_size': 3072,  # hidden_size * 4が目安
    'hidden_act': 'gelu',
    'hidden_dropout_prob': 0.1,
    'attention_probs_dropout_prob': 0.1,
    'max_position_embeddings': 512,
    'type_vocab_size': 1,
    'initializer_range': 0.02,
    'num_labels' : TRAIN_POSSIBLE_LABEL_COUNT, 
}

BERT_CLASSIFICATION_CONFIG = BertConfig.from_dict(BERT_CONFIG)

class BertClassification :
    def __init__(self, model_path):
            self.bert = BertForSequenceClassification.from_pretrained(model_path, config = BERT_CLASSIFICATION_CONFIG)

    def solve(self, input_ids, attention_mask):
        input_ids = torch.LongTensor([input_ids])
        attention_mask = torch.FloatTensor([attention_mask])

        outputs = self.bert(input_ids, attention_mask = attention_mask)
        logit = outputs[0].to('cpu').detach().numpy().copy()
        return logit[0]
