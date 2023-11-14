
from .mjtypes import Tile
from .mjtypes import Meld

from .mjtypes import TilesUtil
from .mjtypes import ActionType
from .action import Action

class PlayerState :
    def __init__(self) :
        self.name = "mjlegal_player"
        self.score = 35000
        self.kyoku_reset()

    def kyoku_reset(self) :
        # 現在第一巡目か(九種九牌で流せるかの判断に使う)
        # 残り自摸の牌数(4枚以下の場合立直はかけられない)
        # 副露しているか(立直できるかの判断に使う)
        self._tiles = []
        self.reach_ho_index = -1 #
        self.jun = 0 # 九種九牌, ダブリー, 海底チェック用
        self.sutehais = [] # 河(鳴かれた牌を含む)
        self.ho = [] # 河(鳴かれた牌を含まない)
        self.prev_action = None
        self.melds = []
        self.tsumo_tile = None
        self.extra_anpais = [] # sutehais以外のこのプレーヤに対する安牌
    
    @property
    def is_reach(self) :
        return self.reach_ho_index >= 0

    @property
    def is_menzen(self) :
        return len(self.furos) == 0

    # 他家から副露した牌
    @property
    def furos(self) : 
        return list(filter(lambda meld : not(meld.type in (Meld.ANKAN, Meld.NUKI)) , self.melds) )

    @property
    def player_id(self) :
        return self._player_id 

    @player_id.setter
    def player_id(self, player_id) : #TODO ガード
        self._player_id = player_id

    def set_tehai_str(self, tiles_str) :
        tiles = TilesUtil.str_to_tiles(tiles_str)
        self.tiles = tiles

    def set_score(self, score) :
        self.score = score
        
    def remove_tile(self, tile) : 
        remove_tile = tile
        if self._tiles[0] == Tile.from_str("?") :
            # 手牌が不明な他家の動作
            remove_tile = Tile.from_str("?")
        if self.tsumo_tile :
            if self.tsumo_tile == remove_tile:
                pass
            else :
                self._tiles.remove(remove_tile)
                self._tiles.append(self.tsumo_tile)
            self.tsumo_tile = None
        else :
            self._tiles.remove(remove_tile)
        return tile

    def pop_ho(self) :
        return self.ho.pop(-1)
    
    # tehai : ツモ牌を含むtiles
    @property
    def tehai(self) :
        if self.tsumo_tile :
            tehai = self._tiles + [self.tsumo_tile]
        else :
            tehai = self._tiles
        return tehai

    @property
    def full_tehai(self) :
        tehai = self.tehai[:]
        if len(self.melds) > 0 :
            # meld_tiles = sum([meld.tiles for meld in self.melds if meld.is_opened], [])
            meld_tiles = sum([meld.tiles[:3] for meld in self.melds if meld.type != ActionType.NUKI], [])
            tehai += meld_tiles
        return tehai

    @property
    def tiles(self) :
        return self._tiles

    @tiles.setter
    def tiles(self, tiles) :
        len_tiles = len(tiles)
        assert len_tiles <= 14, "Too many tiles"
        if len_tiles == 14 :
            self.tsumo_tile = tiles.pop(-1)
        self._tiles = tiles
            
    def tsumo(self, pai) :
        assert self.tsumo_tile is None, "Too many tsumo."
        tile = Tile.from_str(pai)
        self.tsumo_tile = tile
        rinshan = False if self.prev_action is None else self.prev_action.type in (ActionType.ANKAN, ActionType.KAKAN, ActionType.DAIMINKAN, ActionType.NUKI)
        self.prev_action = Action(type = ActionType.TSUMO, actor = self.player_id, tile = tile, rinshan = rinshan)
        return self.prev_action

    def dahai(self, pai, reach_declear = False) :
        tile = Tile.from_str(pai)
        sutehai = self.remove_tile(tile)
        self.sutehais.append(sutehai)
        self.ho.append(sutehai)
        if reach_declear :
            self.reach_ho_index = len(self.ho)
        self.prev_action = Action(type = ActionType.DAHAI, actor = self.player_id, tile = tile, reach_decleared = reach_declear)
        return self.prev_action
        
    def pon(self, pai, consumed, from_id):
        consumed_tiles = [Tile.from_str(ts) for ts in consumed]
        tile = Tile.from_str(pai)
        for t in consumed_tiles :
            self.remove_tile(t)

        meld = Meld(meld_type=Meld.PON, tiles=consumed_tiles + [tile], from_who=from_id)
        self.melds.append(meld)
        self.prev_action = Action(type = ActionType.PON, actor = self.player_id, target = from_id, tile = tile, consumed = consumed_tiles)
        return self.prev_action

    def chi(self, pai, consumed, from_id) :
        consumed_tiles = [Tile.from_str(ts) for ts in consumed]
        tile = Tile.from_str(pai)
        for t in consumed_tiles :
            self.remove_tile(t)

        meld = Meld(meld_type=Meld.CHI, tiles=consumed_tiles + [tile], from_who=from_id)
        self.melds.append(meld)
        self.prev_action = Action(type = ActionType.CHI, actor = self.player_id, target = from_id, tile = tile, consumed = consumed_tiles)
        return self.prev_action

    def ankan(self, consumed):
        consumed_tiles = [Tile.from_str(tile) for tile in consumed]
        for t in consumed_tiles :
            self.remove_tile(t)
        meld = Meld(meld_type = Meld.ANKAN, tiles = consumed_tiles)
        self.melds.append(meld)
        self.prev_action = Action(type = ActionType.ANKAN, actor = self.player_id, target = self.player_id, tile = consumed_tiles[0], consumed = consumed_tiles)
        return self.prev_action

    def kakan(self, pai):
        tile = Tile.from_str(pai)
        self.remove_tile(tile)

        pon_idx = [idx for idx, meld in enumerate(self.melds) 
                    if meld.type == Meld.PON
                    and Tile.equal(tile, meld.tiles[0], True) ][0]
        pon_meld = self.melds[pon_idx]
        
        tiles = pon_meld.tiles + [tile]
        kan_meld = Meld(meld_type = Meld.KAKAN, tiles = tiles, from_who = pon_meld.from_who)
        self.melds[pon_idx] = kan_meld
        self.prev_action = Action(type = ActionType.KAKAN, actor = self.player_id, target = self.player_id, tile = tile)
        return self.prev_action

    def daiminkan(self, pai, consumed, from_id):
        consumed_tiles = [Tile.from_str(ts) for ts in consumed]
        tile = Tile.from_str(pai)
        for t in consumed_tiles :
            self.remove_tile(t)

        meld = Meld(meld_type=Meld.DAIMINKAN, tiles=consumed_tiles + [tile], from_who=from_id)
        self.melds.append(meld)
        self.prev_action = Action(type = ActionType.DAIMINKAN, actor = self.player_id, target = from_id, tile = tile, consumed = consumed_tiles)
        return self.prev_action

    def nukidora(self, pai) :
        tile = Tile.from_str(pai)
        self.remove_tile(tile)
        nukidora_meld = Meld(Meld.NUKI, tiles = [tile])
        self.melds.append(nukidora_meld)
        self.prev_action = Action(type = ActionType.NUKI, actor = self.player_id, target = self.player_id, tile = tile)
        return self.prev_action
        
    def dump(self) :
        return {
            'tiles' : TilesUtil.tiles_to_str(self._tiles), 
            'tsumo':self.tsumo_tile,
            'ho' : TilesUtil.tiles_to_str(self.ho),
            'melds' : self.melds,
            'reach_ho_index' : self.reach_ho_index
        }
    
    @property
    def melds136(self) :
        return [meld.to_meld136() for meld in self.melds if meld.is_opened]

    def export_tile136(self) :
        return {
            'tiles' : TilesUtil.tiles_to_str(self._tiles),
            'melds'     : self.melds136
        }

