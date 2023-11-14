from .game_state import GameState
from .player_state import PlayerState
from .mjtypes import Tile, Meld, TilesUtil
from .mjtypes import ActionType
from .action import Action
from .hand_tool import HandTool

class PossibleActionGenerator :
    def __init__(self) :
        self.hand_tool = HandTool()

    def possible_game_actions(self, game_state) :
        actions = (self.possible_actions_hora(game_state) 
                + self.possible_actions_nukidora(game_state)
                + self.possible_actions_pon(game_state)
                + self.possible_actions_ankan(game_state)
                + self.possible_actions_kakan(game_state)
                + self.possible_actions_daiminkan(game_state)
                + self.possible_action_dahai(game_state)
                + self.possible_actions_dahai_with_reach(game_state)
                + self.possible_actions_ryukyoku(game_state) )
        return actions
        
    def possible_action_dahai(self, game_state) :
        actions = []
        previous_action = game_state.previous_action
        if previous_action is not None  :
            prev_type  = previous_action.type
            if prev_type in (ActionType.TSUMO, ActionType.PON, ActionType.CHI) :
                prev_actor = previous_action.actor
                prev_actor_state = game_state.player_states[prev_actor]
                if prev_actor_state.is_reach and prev_type == ActionType.TSUMO:
                    tsumogiri_action = tsumogiri_action = Action(type = ActionType.DAHAI, actor = prev_actor, 
                                            tile = prev_actor_state.tsumo_tile, tsumogiri = True)
                    actions.append(tsumogiri_action)
                else :
                    dahais = prev_actor_state.tiles
                    if prev_type == ActionType.PON :
                        prev_pon = prev_actor_state.melds[-1]
                        dahais = [tile for tile in dahais if not(Tile.equal(tile, prev_pon.tiles[0], True))]
                    elif prev_type == ActionType.CHI :
                        pass # TODO チーの喰い変え動作
                    actions = [Action(type = ActionType.DAHAI, actor = prev_actor, tile = tile) for tile in dahais]
                    if prev_actor_state.tsumo_tile :
                        tsumogiri_action = Action(type = ActionType.DAHAI, actor = prev_actor, 
                                            tile = prev_actor_state.tsumo_tile, tsumogiri = True)
                        actions.append(tsumogiri_action)
        #TODO 重複アクション削除
        return actions

    def possible_actions_pon(self, game_state):
        actions = []
        previous_action = game_state.previous_action
        if previous_action is not None and game_state.num_pipais > 0 :
            prev_type  = previous_action.type
            prev_actor = previous_action.actor
            if prev_type == ActionType.DAHAI :
                prev_dahai = previous_action.tile
                other_player_ids = filter(lambda id : id != prev_actor, range(0, game_state.num_players))
                for id in other_player_ids :
                    player_state = game_state.player_states[id]
                    if not player_state.is_reach :
                        tiles = player_state.tiles
                        consumed_list = []
                        consumed_tiles = [tile for tile in tiles if tile.equal(prev_dahai, tile, True)]
                        num_consumed = len(consumed_tiles)
                        if num_consumed == 3 :
                            # 手牌に赤ドラを含む場合、2通りのconsumedができる(赤含む、含まない)
                            exclude_aka = [tile for tile in consumed_tiles if not tile.is_aka]
                            if len(exclude_aka) == 3 :
                                consumed_list.append(consumed_tiles[0:2])
                            else :
                                consumed_list.append(exclude_aka)
                                consumed_tiles.remove(prev_dahai)
                                consumed_list.append(consumed_tiles)
                        elif num_consumed == 2 :
                            consumed_list.append(consumed_tiles)
                        
                        for consumed in consumed_list :
                            pon_action = Action(type = ActionType.PON, 
                                            actor = id,
                                            target = prev_actor,
                                            consumed = consumed,
                                            tile = prev_dahai
                                            )
                            actions.append(pon_action)
        return actions

    def possible_actions_ankan(self, game_state):
        actions = []
        previous_action = game_state.previous_action
        if previous_action is not None and game_state.num_pipais > 0 :
            prev_type  = previous_action.type
            if prev_type == ActionType.TSUMO :
                prev_actor = previous_action.actor
                prev_actor_state = game_state.player_states[prev_actor]
                tiles = prev_actor_state.tehai
                tiles34 = TilesUtil.tiles_to_tiles34(tiles)
                ankan_tiles = [Tile.from_tile34_index(i) for i, count in enumerate(tiles34) if count == 4]
                for ankan_t in ankan_tiles :
                    consumed = [tile for tile in tiles if Tile.equal(tile, ankan_t, True)]
                    kan_action = Action(type = ActionType.ANKAN, 
                                        actor = prev_actor,
                                        consumed = consumed)
                    actions.append(kan_action)
        return actions

    def possible_actions_kakan(self, game_state):
        actions = []
        previous_action = game_state.previous_action
        if previous_action is not None and game_state.num_pipais > 0 :
            prev_type  = previous_action.type
            if prev_type == ActionType.TSUMO :
                prev_actor = previous_action.actor
                prev_actor_state = game_state.player_states[prev_actor]
                tiles = prev_actor_state.tehai
                melds = prev_actor_state.melds
                for meld in melds :
                    if meld.type == Meld.PON :
                        kakan_tiles = [tile for tile in tiles if Tile.equal(meld.tiles[0], tile, True)]
                        if len(kakan_tiles) > 0 :
                            kan_action = Action(type = ActionType.KAKAN, actor = prev_actor, tile=kakan_tiles[0], consumed = meld.tiles)
                            actions.append(kan_action)
        return actions

    def possible_actions_daiminkan(self, game_state):
        actions = []
        previous_action = game_state.previous_action
        if previous_action is not None and game_state.num_pipais > 0 :
            prev_type  = previous_action.type
            prev_actor = previous_action.actor
            if prev_type == ActionType.DAHAI :
                prev_dahai = previous_action.tile
                other_player_ids = filter(lambda id : id != prev_actor, range(0, game_state.num_players))
                for id in other_player_ids :
                    player_state = game_state.player_states[id]
                    if not player_state.is_reach :
                        tiles = player_state.tiles
                        consumed_tiles = [tile for tile in tiles if tile.equal(prev_dahai, tile, True)]
                        num_consumed = len(consumed_tiles)
                        if num_consumed == 3 :
                            kan_action = Action(type = ActionType.DAIMINKAN, 
                                            actor = id,
                                            target = prev_actor,
                                            consumed = consumed_tiles,
                                            tile = prev_dahai
                                            )
                            actions.append(kan_action)
        return actions

    def possible_actions_nukidora(self, game_state):
        actions = []
        previous_action = game_state.previous_action
        if previous_action is not None and game_state.num_pipais > 0 :
            prev_type  = previous_action.type
            if prev_type == ActionType.TSUMO :
                prev_actor = previous_action.actor
                prev_actor_state = game_state.player_states[prev_actor]
                tiles = prev_actor_state.tehai
                nukidora_pai = Tile.from_str("N")
                nukidora = next((tile for tile in tiles if tile == nukidora_pai), None)
                if nukidora :
                    actions.append(Action(type = ActionType.NUKI, actor = prev_actor, tile = nukidora))
        return actions

    def possible_actions_dahai_with_reach(self, game_state):
        actions = []
        previous_action = game_state.previous_action
        if previous_action is not None  :
            prev_type  = previous_action.type
            if prev_type == ActionType.TSUMO :
                prev_actor = previous_action.actor
                prev_actor_state = game_state.player_states[prev_actor]
                if not(prev_actor_state.is_reach) and prev_actor_state.is_menzen and prev_actor_state.score >= 1000 and game_state.num_pipais >= game_state.num_players :
                    tiles = prev_actor_state.tehai
                    tenpai_tiles = self.hand_tool.get_tenpai_tiles(tiles)
                    all_dahais = self.possible_action_dahai(game_state)
                    for dahai in all_dahais :
                        if dahai.tile in tenpai_tiles :
                            actions.append(dahai)
        return actions

    def possible_actions_hora(self, game_state):
        actions = []
        previous_action = game_state.previous_action
        if previous_action is not None  :
            is_tsumo=True
            is_rinshan = False
            prev_type  = previous_action.type
            actors = []
            if prev_type == ActionType.TSUMO :
                player_id = previous_action.actor
                actors.append(player_id)
                target = player_id
                is_rinshan = previous_action.rinshan
            elif prev_type in (ActionType.DAHAI, ActionType.ANKAN, ActionType.KAKAN, ActionType.NUKI) :
                is_tsumo=False
                prev_actor = previous_action.actor
                target = prev_actor
                actors = filter(lambda id : id != prev_actor, range(0, game_state.num_players))
                
            for actor in actors :
                if self.hand_tool.can_hora(game_state, actor, previous_action.tile, is_tsumo, is_rinshan) :
                    hora_action = Action(type = ActionType.HORA, 
                                actor = actor, target = target, 
                                tile = previous_action.tile)
                    actions.append(hora_action)
        return actions

    def possible_actions_ryukyoku(self, game_state) :
        actions = []
        previous_action = game_state.previous_action
        if previous_action is not None  :
            prev_type  = previous_action.type
            if prev_type == ActionType.TSUMO :
                prev_actor = previous_action.actor
                prev_actor_state = game_state.player_states[prev_actor]
                if len(prev_actor_state.sutehais) == 0 and prev_actor_state.is_menzen: #first turn
                    tehai = prev_actor_state.tehai
                    if len( set(tile.to_str() for tile in tehai if tile.is_yaochu) ) >= 9 :
                        kyusyukyuhai_action = Action(type = ActionType.RYUKYOKU, actor = prev_actor, reason = "kyushukyuhai")
                        actions.append(kyusyukyuhai_action)

        return actions


