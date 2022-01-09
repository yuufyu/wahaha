import numpy as np

from .bert import BertClassification
from features.mj2vec import Sparse2Vec, Players2Vec, ActionElem
from features.mj2vec import SPARSE_FEATURE_PADDING, PROGRESSION_FEATURE_PADDING, POSSIBLE_FEATURE_PADDING

MJAI_BOT_NAME = "wahaha"

TRAIN_TOKEN_OFFSET = 2 # 0:CLS, 1:SEP
TRAIN_TOKEN_CLS     = 0
TRAIN_TOKEN_SEP     = 1
TRAIN_TOKEN_PADDING = 2 + 382 + 648 + 219 # 2(CLS,SEP)+382(sparse)+648(progression)+219(possible)
TRAIN_TOKEN_MASK    = TRAIN_TOKEN_PADDING + 1
TRAIN_MAX_TOKEN_LENGTH = 2 + 139 + 1 # 139 = 26(sparse)+81(progression)+32(possible)

class Client :
    
    def __init__(self, model_path) :
        self.model = BertClassification(model_path)
        self.sparse2vec = Sparse2Vec()
        self.players2vec = Players2Vec()
        self.previous_event = None
    
    def update_state(self, event) :
        event_type = event["type"]

        if event_type == "dahai" :
            if self.previous_event["type"] in ("pon", "daiminkan") :
                """
                [FIXME] 副露後の打牌がtsumogiri=Trueになってしまう場合があるため、常にFalseに書き換える。
                """
                event["tsumogiri"] = False

        if event_type == "start_game" :
            self.player_id = event["id"]
        
        self.sparse2vec.action(event)
        self.players2vec.action(event)
        
        self.previous_event = event

    def choose_action(self) :
        choosed_action = {"type" : "none"}

        prev_type = self.previous_event["type"]
        if prev_type == "hello" : 
            choosed_action = {"type":"join","name":MJAI_BOT_NAME,"room":"default"}
        else :
            possible_actions = self.players2vec.get_possible_action(self.player_id)
            if len(possible_actions) == 1 :
                choosed_action = possible_actions[0]
            elif len(possible_actions) > 1 :
                feature = self.get_feature()
                input_ids, attention_mask = self.encode(feature)
                logit = self.model.solve(input_ids, attention_mask)

                # possible_actionのうち、最も確率が高いアクションを選択
                possible_ids = [self.action_to_token(action) for action in possible_actions]
                mask = np.zeros(logit.shape, dtype=bool)
                mask[possible_ids] = True
                masked_logit = np.ma.masked_array(logit, mask = ~mask)
                pred = masked_logit.argmax()

                pred_actions = [action for action in possible_actions if self.action_to_token(action) == pred]
                choosed_action = pred_actions[0]

                #@debug
                print(f"[BERT] probably : {masked_logit[pred]}") #@debug
                print(f"[BERT] prediction : {pred}, prediction(no masked) : {logit.argmax()}") #@debug

        return choosed_action

    def get_feature(self) :
        # sparse feature
        player_elem = self.players2vec.get_player_elem(self.player_id)
        sparse_feature = self.sparse2vec.to_feature(self.player_id) \
                        + player_elem.to_sparse_feature()
        # print(f"sparse[{self.player_id}] : {sparse_feature}")

        # numeric feature
        # numeric_feature = player_elem.scores

        # progression feature
        progression_feature = self.players2vec.progression_feature(self.player_id)
        # print(f"progression : {progression_feature}")

        # possible_action feature
        possible_feature = self.players2vec.to_possible_feature(self.player_id)
        # print(f"possible : {possible_feature}")

        # concat features
        sparse      = [num + TRAIN_TOKEN_OFFSET for num in sparse_feature]
        progression = [num + TRAIN_TOKEN_OFFSET + SPARSE_FEATURE_PADDING for num in progression_feature]
        possible    = [num + TRAIN_TOKEN_OFFSET + SPARSE_FEATURE_PADDING + PROGRESSION_FEATURE_PADDING for num in possible_feature]

        return sparse + progression + possible

    def encode(self, feature) :
        # Append special tokens
        input_ids = [TRAIN_TOKEN_CLS] + feature + [TRAIN_TOKEN_SEP]
        inputs = np.array(input_ids)
        
        # attention mask
        pad_length = TRAIN_MAX_TOKEN_LENGTH - len(inputs)
        attention_mask = np.array([1] * len(inputs) + [0] * pad_length)
        
        # padding
        inputs = np.pad(inputs,(0, pad_length), constant_values = TRAIN_TOKEN_PADDING)

        return inputs, attention_mask

    def action_to_token(self, possible_action) :
        action_type = possible_action["type"]
        elem = ActionElem(type = "skip", value = 0) #skip
        if action_type in ("dahai", "reach", "pon", "daiminkan", "ankan", "kakan", "nukidora", "hora", "ryukyoku") :
            elem = ActionElem.from_mjai(possible_action)
        return ActionElem.possible_action_feature(elem)


