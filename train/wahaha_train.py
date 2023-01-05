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

#--------------------------------
# MLM config
#--------------------------------
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
TRAIN_MLM_MODEL_CONFIG = {
    'checkpoint_callback' : False, 
    'gpus' : [0], # 環境にあわせて変更
    'val_check_interval' : 10000, # validationおよびcheckpointの間隔step数
    'max_epochs' : 5,
    'model_dir' : None, # インポートするモデル
}
TRAIN_MLM_LOADER_CONFIG = {
    'batch_size' : 64,
    'num_workers' : 8,
    'pin_memory' : False,
    'drop_last' : True
}
VAL_MLM_LOADER_CONFIG = {
    'batch_size' : 64,
    'num_workers' : 8,
    'pin_memory' : False,
    'drop_last' : False
}
BERT_MLM_CONFIG = BertConfig.from_dict(TRAIN_MLM_CONFIG)

#--------------------------------
# Clasiffication config
#--------------------------------
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
BERT_CLASSIFICATION_CONFIG = BertConfig.from_dict(TRAIN_CLASSIFICATION_CONFIG)

# https://github.com/PyTorchLightning/pytorch-lightning/issues/2534#issuecomment-674582085
class CheckpointEveryNSteps(pl.Callback):
    """
    Save a checkpoint every N steps, instead of Lightning's default that checkpoints
    based on validation loss.
    """

    def __init__(
        self,
        save_step_frequency,
        prefix="N-Step-Checkpoint",
        use_modelcheckpoint_filename=False,
    ):
        """
        Args:
            save_step_frequency: how often to save in steps
            prefix: add a prefix to the name, only used if
                use_modelcheckpoint_filename=False
            use_modelcheckpoint_filename: just use the ModelCheckpoint callback's
                default filename, don't use ours.
        """
        self.save_step_frequency = save_step_frequency
        self.prefix = prefix
        self.use_modelcheckpoint_filename = use_modelcheckpoint_filename

    def on_batch_end(self, trainer: pl.Trainer, _):
        """ Check if we should save a checkpoint after every train batch """
        epoch = trainer.current_epoch
        global_step = trainer.global_step
        if global_step % self.save_step_frequency == 0:
            if self.use_modelcheckpoint_filename:
                filename = trainer.checkpoint_callback.filename
            else:
                #filename = f"{self.prefix}_{epoch}_{global_step}.ckpt"
                filename = f"{self.prefix}.ckpt"
            ckpt_path = os.path.join(TRAIN_LOG_DIRECTORY, filename)
            trainer.save_checkpoint(ckpt_path)

#--------------------------------
# MLM model
#--------------------------------
class BertMLM(nn.Module):
    def __init__(self, model_dir=None):
        super().__init__()
        if model_dir is None:
            self.bert = BertForMaskedLM(BERT_MLM_CONFIG)
        else:
            self.bert = BertForMaskedLM.from_pretrained(model_dir)

    def forward(self, input_ids, labels):
        return self.bert(input_ids=input_ids, labels=labels)
class MLMModule(pl.LightningModule):
    def __init__(self, hparams):
        super().__init__()
        model_dir = hparams["model_dir"]
        self.save_hyperparameters(hparams)
        self.model = BertMLM(model_dir)

    def forward(self, batch):
        input_ids = batch['input_ids']
        labels = batch['labels']
        return self.model(input_ids=input_ids, labels=labels)

    def training_step(self, batch, batch_idx):
        outputs = self(batch)
        loss = outputs[0]
        self.log('loss', loss)
        return loss

    def validation_step(self, batch, batch_idx):
        outputs = self(batch)
        loss = outputs[0].detach().cpu().numpy()
        return {'loss': loss}

    def validation_epoch_end(self, outputs):
        val_loss = np.mean([out['loss'] for out in outputs])
        #self.log('steps', self.global_step)
        self.log('val_loss', val_loss)

    def configure_optimizers(self):
        return AdamW(self.parameters(), lr=5e-5)

class MLMDataset(Dataset):
    def __init__(self, filename):
        self.filename = filename # input text file
        with open(self.filename, 'r') as file :
            print("[MLMDataset]--- start setup ---")
            self.content = file.readlines()
            print("[MLMDataset]--- loading is completed ---")

        self.mask_token_id = TRAIN_TOKEN_MASK  # 駒が割り振られていないid

    def __len__(self):
        return len(self.content)

    def __getitem__(self, idx):
        line = self.content[idx]
        inputs, _ = line.split('\t') # labelは破棄
        inputs = json.loads('[' + inputs + ']')
        inputs = [TRAIN_TOKEN_CLS] + inputs + [TRAIN_TOKEN_SEP]
        
        inputs = np.array(inputs)
        inputs = np.pad(inputs,(0, TRAIN_MAX_TOKEN_LENGTH - len(inputs)), constant_values = TRAIN_TOKEN_PADDING)
        labels = inputs.copy()

        # 予想対象
        masked_indices = np.random.random(labels.shape) < 0.15
        labels[~masked_indices] = -100

        # 80%はマスクトークンに
        indices_replaced = (np.random.random(labels.shape) < 0.8) & masked_indices
        inputs[indices_replaced] = self.mask_token_id

        # 10%はランダムに置き換え
        indices_random = (np.random.random(labels.shape) < 0.5) & masked_indices & ~indices_replaced
        random_words = np.random.choice(TRAIN_ID_LIST, labels.shape)
        inputs[indices_random] = random_words[indices_random]

        # 残り10%はそのままのものが残る
        ret_dict = {'input_ids': torch.tensor(inputs, dtype=torch.long),
                    'labels': torch.tensor(labels, dtype=torch.long)}
        return ret_dict

class MLMDataModule(pl.LightningDataModule):
    def __init__(self):
        super().__init__()
        # self.cfg = cfg

    def setup(self, stage=None) :
        self.train_dataset = MLMDataset(TRAIN_FILE)
        self.val_dataset = MLMDataset(TEST_FILE)

    def train_dataloader(self):
        return DataLoader(self.train_dataset, **TRAIN_MLM_LOADER_CONFIG)

    def val_dataloader(self):
        return DataLoader(self.val_dataset, **VAL_MLM_LOADER_CONFIG)
        
#--------------------------------
# Classification model
#--------------------------------
# model = BertModel.from_pretrained('Japanese_L-12_H-768_A-12_E-30_BPE/pytorch_model.bin', config=config)
class BertClassification(nn.Module) :
    def __init__(self):
        super().__init__()
        # self.bert = BertForSequenceClassification.from_pretrained(model_bin, config = BERT_CLASSIFICATION_CONFIG)
        self.bert = BertForSequenceClassification(BERT_CLASSIFICATION_CONFIG)

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

#--------------------------------------------------------------------------------
# Print Network
#--------------------------------------------------------------------------------
from torchinfo import summary

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

def parameter_freeze() :
    model = BertForSequenceClassification(BERT_CLASSIFICATION_CONFIG)
    for name, param in model.named_parameters() :
         # bert.pooler.*, classifier.*を重み更新する対象(requires_grad=True)とする
        param.requires_grad = (name.startswith('bert.pooler') or name.startswith('classifier.'))

    for name, param in model.named_parameters(recurse=True) :
        print(name, param.requires_grad, param.size())

       
def main() :
    parameter_freeze()
    # printBertClassification()
    # printBertForMaskedLM()

if __name__ == '__main__':
    main()