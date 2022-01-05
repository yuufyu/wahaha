# wahaha train
import pathlib
import json
import glob

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.utils.data import Dataset
from transformers import AdamW
from transformers import BertConfig, BertForMaskedLM, BertModel, BertForSequenceClassification
import pytorch_lightning as pl
from pytorch_lightning import loggers as pl_loggers
from pytorch_lightning.callbacks import ModelCheckpoint

TRAIN_NAME="wahaha_train"
TRAIN_LOG_DIRECTORY='drive/MyDrive/dl/wahaha/log'
TRAIN_MLM_MODEL_DIR = 'drive/MyDrive/dl/wahaha/model'
TRAIN_PRETRAIN_MODEL_BIN = "../wahaha_model/mlm_220105/pytorch_model.bin"

TRAIN_FILE='drive/MyDrive/dl/wahaha/train/train_feature.txt'
TEST_FILE='drive/MyDrive/dl/wahaha/train/test_feature.txt'
# TRAIN_DATA_DIRECTORY='drive/MyDrive/dl/kanachan/train'
# TEST_DATA_DIRECTORY='drive/MyDrive/dl/kanachan/test'

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
TRAIN_CLASSIFICATION_MODEL_CONFIG = {
    'checkpoint_callback' : False, 
    'gpus' : [0], # 環境にあわせて変更
    'val_check_interval' : 10000, # validationおよびcheckpointの間隔step数
    'max_epochs' : 3,
    'model_bin' : TRAIN_PRETRAIN_MODEL_BIN, # インポートするモデル
}
TRAIN_CLASSIFICATION_LOADER_CONFIG = {
    'batch_size' : 128,
    'num_workers' : 2,
    'pin_memory' : True,
    'drop_last' : True
}
VAL_CLASSIFICATION_LOADER_CONFIG = {
    'batch_size' : 128,
    'num_workers' : 2,
    'pin_memory' : True,
    'drop_last' : False
}
config = BertConfig.from_dict(TRAIN_MLM_CONFIG)
BERT_CLASSIFICATION_CONFIG = BertConfig.from_dict(TRAIN_CLASSIFICATION_CONFIG)

class BertPolicyValue(nn.Module):
    def __init__(self, model_dir=None):
        super().__init__()
        if model_dir is None:
            self.bert = BertModel(BERT_CLASSIFICATION_CONFIG)
        else:
            self.bert = BertModel.from_pretrained(model_dir)

        self.policy_head = nn.Sequential(
            nn.Linear(TRAIN_HIDDEN_SIZE, TRAIN_HIDDEN_SIZE * 2),
            nn.Tanh(),
            nn.Linear(TRAIN_HIDDEN_SIZE * 2, 9 * 9 * 27)
        )

        self.value_head = nn.Sequential(
            nn.Linear(TRAIN_HIDDEN_SIZE, TRAIN_HIDDEN_SIZE * 2),
            nn.Tanh(),
            nn.Linear(TRAIN_HIDDEN_SIZE * 2, 1),
            nn.Sigmoid()
        )

        self.loss_policy_fn = nn.CrossEntropyLoss()
        self.loss_value_fn = nn.MSELoss()

    def forward(self, input_ids, labels=None):
        features = self.bert(input_ids=input_ids)['last_hidden_state']
        policy = self.policy_head(features).mean(axis=1)
        value = self.value_head(features).mean(axis=1).squeeze(1)
        if labels is None:
            return {'policy': policy, 'value': value}
        else:
            loss_policy = self.loss_policy_fn(policy, labels['labels'])
            loss_value = self.loss_value_fn(value, labels['values'])
            loss = loss_policy + loss_value
            return {'loss_policy': loss_policy, 'loss_value': loss_value, 'loss': loss}
        # loss = self.loss_policy_fn(policy, labels['labels'])
        # return {'loss' : loss}



# BERT分類モデルの定義
class BERTClass(nn.Module):
    def __init__(self, drop_rate, otuput_size):
        super().__init__()
        # self.bert = BertModel.from_pretrained('bert-base-uncased')
        self.bert = BertModel(BERT_CLASSIFICATION_CONFIG)
        self.drop = torch.nn.Dropout(drop_rate)
        self.fc = torch.nn.Linear(768, otuput_size)  # BERTの出力に合わせて768次元を指定

    def forward(self, ids, mask):
        # _, out = self.bert(ids, attention_mask=mask)
        out = self.bert(ids, attention_mask=mask)
        # _, out = self.bert(ids)
        out = out['pooler_output']
        # print("[BertClass]",out)
        out = self.fc(self.drop(out))
        return out



# model = BertModel.from_pretrained('Japanese_L-12_H-768_A-12_E-30_BPE/pytorch_model.bin', config=config)
class BertClassification(nn.Module) :
    def __init__(self, model_bin):
        super().__init__()
        self.bert = BertForSequenceClassification.from_pretrained(model_bin, config = BERT_CLASSIFICATION_CONFIG)

    def forward(self, input_ids, labels):
        outputs = self.bert(input_ids, labels = labels)
        loss = outputs[0]
        # logit = outputs[1]
        return loss

class BertClassificationModule(pl.LightningModule):
    def __init__(self, hparams):
        super().__init__()
        model_bin = hparams["model_bin"]
        self.save_hyperparameters(hparams)
        self.model = BertClassification(model_bin)

    def forward(self, input_ids, labels):
        return self.model(input_ids=input_ids, labels=labels)

    def training_step(self, batch, batch_idx):
        input_ids = batch.pop('input_ids')
        outputs = self(input_ids, batch)
        loss = outputs['loss']
        return loss

    def validation_step(self, batch, batch_idx):
        input_ids = batch.pop('input_ids')
        output = self(input_ids, batch)
        for k, v in output.items():
            output[k] = v.detach().cpu().numpy()
        return output

    def validation_epoch_end(self, outputs):
        val_loss = np.mean([out['loss'] for out in outputs])
        self.log('val_loss', val_loss)

    def configure_optimizers(self):
        return AdamW(self.parameters(), lr=5e-5)

class BertClassificationDataset(Dataset):
    def __init__(self, filename):
        # まとめて読み出し
        self.filename = filename
        with open(self.filename, 'r') as file :
            print("[MLMDataset]--- start setup ---")
            self.content = file.readlines()
            print("[MLMDataset]--- loading is completed ---")

    def __len__(self):
        return len(self.content)

    def __getitem__(self, idx):
        line = self.content[idx]
        inputs, label = line.split('\t')
        inputs = json.loads('[' + inputs + ']')
        inputs = [TRAIN_TOKEN_CLS] + inputs + [TRAIN_TOKEN_SEP]
        
        # padding付与
        inputs = np.array(inputs)
        inputs = np.pad(inputs,(0, TRAIN_MAX_TOKEN_LENGTH - len(inputs)), constant_values = TRAIN_TOKEN_PADDING)

        label = int(label)

        ret_dict = {'input_ids': torch.tensor(inputs, dtype=torch.long),
                    'labels': torch.tensor(label, dtype=torch.long)}
        return ret_dict

class BertClassificationDataModule(pl.LightningDataModule):
    def __init__(self):
        super().__init__()

    def setup(self, stage=None) :
        self.train_dataset = BertClassificationDataset(TRAIN_FILE)
        self.val_dataset = BertClassificationDataset(TEST_FILE)

    def train_dataloader(self):
        return DataLoader(self.train_dataset, **TRAIN_CLASSIFICATION_LOADER_CONFIG)

    def val_dataloader(self):
        return DataLoader(self.val_dataset, **VAL_CLASSIFICATION_LOADER_CONFIG)

from torchinfo import summary
def printModel() :
    model = BertPolicyValue()
    summary(model, input_size=(1,TRAIN_MAX_TOKEN_LENGTH),dtypes=[torch.long])

def printBERTClass() :
    model = BERTClass(0.5, TRAIN_POSSIBLE_LABEL_COUNT)
    inshape = (1, 10)
    mask = torch.LongTensor(np.ones(inshape))
    summary(model, input_size=inshape, mask = mask, dtypes=[torch.long])

def printBertClassification() :
    model = BertClassification()
    inshape = (1, 10)
    label = torch.LongTensor(np.array([[0]]))
    summary(model, input_size=inshape, labels = label , dtypes=[torch.long], depth = 4)

def main() :
    print("--- BertPolicyValue ---")
    printModel()
    # print("--- BERTClass ---")
    # printBERTClass()
    print("--- BertClassification ---")
    printBertClassification()

if __name__ == '__main__':
    main()