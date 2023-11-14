import numpy as np
import copy

from mjlegal.mjai_possible_action import MjaiPossibleActionGenerator
from mjlegal.mjai_player_loader import MjaiPlayerLoader
from bert import BertClassification
from features.mjai_encoder import MjaiEncoderClient, Action, MAX_TOKEN_LENGTH, TRAIN_TOKEN_SEP


class Client:
    """
    mjai client
    """

    def __init__(self, model_path, mjai_name, room):
        self.model = BertClassification(model_path)
        self.possible_client = MjaiPlayerLoader()
        self.possible_action_generator = MjaiPossibleActionGenerator(mjai_name, room)
        self.encoder = MjaiEncoderClient()

    def update_state(self, event):
        if event["type"] == "dahai":
            if self.previous_event["type"] in ("pon", "daiminkan"):
                """
                [FIXME] 副露後の打牌がtsumogiri=Trueになってしまう場合があるため、常にFalseに書き換える。
                """
                event["tsumogiri"] = False

        self.possible_client.action_receive(event)
        self.encoder.update(event)

        self.previous_event = event

    def choose_action(self):
        # 合法手から次のアクションを選択する
        possible_actions = self.possible_action_generator.possible_mjai_action(self.possible_client.game)
        rule_base = self.rule_base_choose_action()
        if len(possible_actions) == 1:
            choosed_action = possible_actions[0]
        elif rule_base is not None:
            choosed_action = rule_base
        elif len(possible_actions) > 1:
            player_id = self.possible_client.game.player_id
            input_ids, attention_mask, positional_ids = self.encode(player_id)

            logit = self.model.solve(input_ids, attention_mask, positional_ids)

            # possible_actionsをエンコード
            possible_action_dict = {Action.encode(action): action for action in possible_actions}
            possible_action_ids = list(possible_action_dict.keys())

            # possible_actionのindexでlogitをマスクする
            mask = np.zeros(logit.shape, dtype=bool)
            mask[possible_action_ids] = True

            masked_logit = np.ma.masked_array(logit, mask=~mask)

            # possible_actionのうち、最もlogit値が高いactionのindexを取得
            pred_id = masked_logit.argmax()

            choosed_action = copy.copy(possible_action_dict[pred_id])

            # --- @debug --- #
            softmax_logit = np.exp(logit) / np.sum(np.exp(logit))  # softmax
            choosed_action["ext_bot"] = {"token": int(pred_id), "prob": str(softmax_logit[pred_id])}
            candidate_probs = [
                {"action": action, "prob": str(softmax_logit[token_id])}
                for token_id, action in possible_action_dict.items()
            ]
            choosed_action["ext_bot"]["candidate"] = candidate_probs
            # choosed_action["ext_bot"]["possible_actions"] = copy.deepcopy(possible_actions)
            # --- @debug --- #
        else:
            choosed_action = {"type": "none"}

        return choosed_action

    def encode(self, player_id):
        inputs = self.encoder.encode(player_id)
        pad_length = MAX_TOKEN_LENGTH - len(inputs)
        attention_mask = np.array([1] * len(inputs) + [0] * pad_length)
        inputs = np.array(inputs)

        # positional ids
        positional_idx_start = np.where(inputs == TRAIN_TOKEN_SEP)[0][0] - 1
        positional_arange = np.arange(inputs.shape - positional_idx_start)
        positional_ids = np.zeros(inputs.shape)
        positional_ids[positional_idx_start:] = positional_arange

        inputs = np.pad(inputs, (0, pad_length), constant_values=0)
        positional_ids = np.pad(positional_ids, (0, pad_length), constant_values=0)

        return inputs, attention_mask, positional_ids

    def rule_base_choose_action(self):
        # 暫定：和了できるときは確定で和了する
        if "possible_actions" in self.previous_event:
            mjai_possible_actions = self.previous_event["possible_actions"]
            hora_actions = [action for action in mjai_possible_actions if action["type"] == "hora"]
            if len(hora_actions) > 0:
                return hora_actions[0]

        return None
