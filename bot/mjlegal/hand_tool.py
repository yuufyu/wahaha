import copy

from mahjong.agari import Agari
from mahjong.hand_calculating.hand import HandCalculator
from mahjong.hand_calculating.hand_config import HandConfig, OptionalRules
from mahjong.constants import EAST, SOUTH, WEST, NORTH

from .mjtypes import TilesUtil

class HandTool :
    WINDS = {"E": EAST, "S" : SOUTH, "W" : WEST, "N" : NORTH}
    
    def __init__ (self) :
        self.agari  = Agari()
        self.hand = HandCalculator()
    
    def can_hora(self, game_state, actor, win_tile, is_tsumo, is_rinshan) :
        player_state = game_state.player_states[actor]
        tiles = player_state.tiles
        tehai = tiles + [win_tile]
        if TilesUtil.include_closed_tile(tehai) :
            return False

        full_tehai = player_state.full_tehai
        if player_state.tsumo_tile is None :
            full_tehai.append(win_tile)
        
        tehais34 = TilesUtil.tiles_to_tiles34(tehai)
        
        if not is_tsumo : 
            tiles34 = TilesUtil.tiles_to_tiles34(tiles)
            machi_tiles34 = self.get_machi_tiles34(tiles34)
            if self.is_furiten(game_state, actor, machi_tiles34) :
                return False # furiten

        is_agari = False
        if self.agari.is_agari(tehais34) :
            tehai136 = TilesUtil.tiles_to_tiles136(tehai)
            melds136 = player_state.melds136
            full_tehai136 = TilesUtil.tiles_to_tiles136(full_tehai)
            if len(melds136) == 0 :
                melds136 = None
            
            win_tile136 = tehai136[-1]
            dora_ind = TilesUtil.tiles_to_tiles136(game_state.dora_markers)
            is_riichi= player_state.is_reach
            player_wind = game_state.player_wind(actor)
            hand_config = self.make_hand_config(is_tsumo   = is_tsumo,
                                                is_riichi  = is_riichi,
                                                is_ippatsu = False,  # TODO ippatsu
                                                is_rinshan = is_rinshan,
                                                is_chankan = False, # TODO chankan
                                                is_haitei  = is_tsumo and game_state.num_pipais == 0,
                                                is_houtei  = not(is_tsumo) and game_state.num_pipais == 0,
                                                is_daburu_riichi = False, # TODO double reach
                                                is_nagashi_mangan = False, # TODO nagashi mangan
                                                is_tenhou = False, # TODO tenhou
                                                is_renhou = False, # TODO renhou
                                                is_chiihou = False, # TODO chiihou
                                                player_wind = HandTool.WINDS[player_wind],
                                                round_wind = HandTool.WINDS[game_state.bakaze])
            hand_value = self.hand.estimate_hand_value(tiles = full_tehai136, win_tile = win_tile136,
                                            melds = melds136, dora_indicators = dora_ind, config = hand_config)
            # print(hand_value.cost)
            is_agari = hand_value.cost is not None
        return is_agari

    def is_furiten(self, game_state, actor, machi_tiles34) :
        player_state = game_state.player_states[actor]
        sutehais = player_state.sutehais
        anpai_tiles =  sutehais + player_state.extra_anpais
        anpai_tiles34 = TilesUtil.tiles_to_tiles34(anpai_tiles)
        is_furiten = any(machi * furiten != 0 for machi, furiten in zip(machi_tiles34, anpai_tiles34))
        return is_furiten

    def get_tenpai_tiles(self, tiles) :
        if TilesUtil.include_closed_tile(tiles) :
            return []
        tiles34 = TilesUtil.tiles_to_tiles34(tiles)
        tenpai_tiles_34 = self.get_tenpai_tiles34(tiles34)
        tenpai_dahais = []
        if sum(tenpai_tiles_34) > 0 :
            tenpai_dahais = TilesUtil.find_tiles_34_in_tiles(tiles, tenpai_tiles_34)
        return tenpai_dahais

    def get_machi_tiles34(self, tiles_34) :
        tile_count = sum(tiles_34)
        assert tile_count < 14 and (tile_count - 1) % 3 == 0

        machi_tiles_34 = [0] * 34
        for i in range(0,34) :
            temp_tiles = copy.copy(tiles_34)
            if temp_tiles[i] < 4 :
                temp_tiles[i] += 1
                if self.agari.is_agari(temp_tiles) :
                    machi_tiles_34[i] = 1
        return machi_tiles_34

    def get_tenpai_tiles34(self, tiles_34) :
        tenpai_tiles_34 = [0] * 34
        for i in range(0,34) :
            if tiles_34[i] > 0 :
                temp_tiles = copy.copy(tiles_34)
                temp_tiles[i] -= 1
                machi_tiles_34 = self.get_machi_tiles34(temp_tiles)
                if sum(machi_tiles_34) > 0 :
                    tenpai_tiles_34[i] = 1
        return tenpai_tiles_34

    def make_hand_config(self,
        is_tsumo=False,
        is_riichi=False,
        is_ippatsu=False,
        is_rinshan=False,
        is_chankan=False,
        is_haitei=False,
        is_houtei=False,
        is_daburu_riichi=False,
        is_nagashi_mangan=False,
        is_tenhou=False,
        is_renhou=False,
        is_chiihou=False,
        player_wind=None,
        round_wind=None,
    ):
        options = OptionalRules(
            has_open_tanyao=True,
            has_aka_dora=True,
            has_double_yakuman=True,
            renhou_as_yakuman=False,
            has_daisharin=False,
            has_daisharin_other_suits=False,
            # has_daichisei=False,
            # has_sashikomi_yakuman=False,
            # limit_to_sextuple_yakuman=True,
            # paarenchan_needs_yaku=False,
        )
        return HandConfig(
            is_tsumo=is_tsumo,
            is_riichi=is_riichi,
            is_ippatsu=is_ippatsu,
            is_rinshan=is_rinshan,
            is_chankan=is_chankan,
            is_haitei=is_haitei,
            is_houtei=is_houtei,
            is_daburu_riichi=is_daburu_riichi,
            is_nagashi_mangan=is_nagashi_mangan,
            is_tenhou=is_tenhou,
            is_renhou=is_renhou,
            is_chiihou=is_chiihou,
            player_wind=player_wind,
            round_wind=round_wind,
            # is_open_riichi=False,
            # paarenchan=0,
            options=options,
        )