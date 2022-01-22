import torch
from transformers import BertForSequenceClassification

class BertClassification :
    def __init__(self, model_path):
        self.bert = BertForSequenceClassification.from_pretrained(model_path)

    def solve(self, input_ids, attention_mask):
        input_ids = torch.LongTensor([input_ids])
        attention_mask = torch.FloatTensor([attention_mask])

        outputs = self.bert(input_ids, attention_mask = attention_mask)
        logit = outputs[0].to('cpu').detach().numpy().copy()
        return logit[0]
