from .possible_action import PossibleActionGenerator

class MjaiPossibleActionGenerator :
    
    def __init__(self, name = "mjlegal", room = "default") :
        self.possibleAction = PossibleActionGenerator()
        self.name = name
        self.room = room

    # "dummy" is unused argument.
    def possible_mjai_action(self, game_state, dummy = None) :
        possible_actions = []
        if hasattr(game_state,"mjai_previous_action") and game_state.mjai_previous_action is not None :
            previous_mjai_action = game_state.mjai_previous_action
            action_type = previous_mjai_action["type"]
            if action_type == "hello" :
                join_action = {"type" : "join", "name" : self.name, "room" : self.room}
                possible_actions.append(join_action)
            elif action_type in ("start_game", "start_kyoku", "reach_accepted", "dora", "hora", "ryukyoku", "end_kyoku", "end_game") :
                none_action = {"type" : "none"}
                possible_actions.append(none_action)
            elif previous_mjai_action["actor"] is not None :
                actor = previous_mjai_action["actor"]
                if actor != game_state.player_id :
                    none_action = {"type" : "none"}
                    possible_actions.append(none_action)
                    mjai_possible = self.possible_game_action_furo(game_state)
                    possible_actions += mjai_possible
                elif actor == game_state.player_id :
                    if action_type == "reach" :
                        reach_dahai_actions = self.possible_game_action_with_reach(game_state)
                        possible_actions += reach_dahai_actions
                    else :
                        if action_type in ("dahai", "nukidora", "daiminkan", "ankan", "kakan") :
                            none_action = {"type" : "none"}
                            possible_actions.append(none_action)
                        elif self.can_reach(game_state) :
                            reach_action = {"type" : "reach", "actor" : actor}
                            possible_actions.append(reach_action)
                        mjai_possible = self.possible_game_action_dahai_turn(game_state)
                        possible_actions += mjai_possible
            else :
                raise Exception("invalid action ", previous_mjai_action)
        else :
            none_action = {"type" : "none"}
            possible_actions.append(none_action)
        return possible_actions

    def possible_game_action_dahai_turn(self, game_state) :
        possible_game_actions = (self.possibleAction.possible_actions_hora(game_state)
                + self.possibleAction.possible_actions_ryukyoku(game_state)
                + self.possibleAction.possible_actions_nukidora(game_state)
                + self.possibleAction.possible_actions_ankan(game_state)
                + self.possibleAction.possible_actions_kakan(game_state)
                + self.possibleAction.possible_action_dahai(game_state))
        mjai_possible = [action.to_mjai_json() for action in possible_game_actions if action.actor == game_state.player_id]
        return mjai_possible
    
    def possible_game_action_furo(self, game_state) :
        possible_game_actions = (self.possibleAction.possible_actions_hora(game_state) 
                + self.possibleAction.possible_actions_pon(game_state)
                + self.possibleAction.possible_actions_daiminkan(game_state))
        mjai_possible = [action.to_mjai_json() for action in possible_game_actions if action.actor == game_state.player_id]
        return mjai_possible

    def possible_game_action_with_reach(self, game_state) :
        reach_dahai_actions = self.possibleAction.possible_actions_dahai_with_reach(game_state)
        mjai_possible = [action.to_mjai_json() for action in reach_dahai_actions]
        return mjai_possible

    def can_reach(self, game_state) :
        possible_reach_actions = self.possibleAction.possible_actions_dahai_with_reach(game_state)
        return len(possible_reach_actions) > 0


        