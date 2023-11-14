from enum import Enum, auto
from mahjong.tile import TilesConverter
from mahjong import meld

class ActionType(Enum) : 
    NONE = "none"
    TSUMO = "tsumo"
    DAHAI = "dahai"
    CHI = "chi"
    PON = "pon"
    ANKAN = "ankan"
    KAKAN = "kakan"
    DAIMINKAN = "daiminkan"
    NUKI = "nukidora"
    HORA = "hora"
    RYUKYOKU = "ryukyoku"

class Tile :
    # const
    LOOKUP_MJAI_PAI_NAME_TABLE = {'5mr': '0m', '5pr': '0p', '5sr': '0s', 'E': '1z', 'S': '2z', 'W': '3z', 'N': '4z', 'P': '5z', 'F': '6z', 'C': '7z'}
    LOOKUP_MSPZ_PAI_NAME_TABLE = {v: k for k, v in LOOKUP_MJAI_PAI_NAME_TABLE.items()}
    TILES136_SUIT_OFFSET = {"m" : 0, "p" : 36, "s" : 72, "z" : 108}

    def to_str(self) :
        s = "?"
        if self.number > -1 and self.suit != "?" :
            s = str(self.number) + self.suit + ("r" if self.is_aka else "")
        return s

    def to_mjai_str(self) :
        s = self.to_str()
        return Tile.LOOKUP_MSPZ_PAI_NAME_TABLE[s] if s in Tile.LOOKUP_MSPZ_PAI_NAME_TABLE else s

    @property
    def is_yaochu(self) :
        return self.number == 1 or self.number == 9 or self.suit == 'z'

    def __str__(self):
        return self.to_str()
    
    def __repr__(self):
        return self.to_str()

    def __eq__ (self, other) :
        return Tile.equal(self, other) 
    
    @staticmethod
    def tile136_suit_offset(suit_str) :
        return Tile.TILES136_SUIT_OFFSET[suit_str]

    @staticmethod
    def from_str(tile_str) :
        if tile_str == "?" :
            tile = Tile()
            tile.number = -1
            tile.suit = "?"
            tile.is_aka = False
            return tile
            
        if tile_str in Tile.LOOKUP_MJAI_PAI_NAME_TABLE :
            tile_str = Tile.LOOKUP_MJAI_PAI_NAME_TABLE[tile_str]

        num = int(tile_str[0])
        suit = tile_str[1]
        is_aka = (num == 0)
        number = 5 if is_aka else num

        tile = Tile()
        tile.number = number
        tile.suit = suit
        tile.is_aka = is_aka

        return tile

    @staticmethod
    def from_tile136(tile136) :
        tile_str = TilesConverter.to_one_line_string([tile136])
        return Tile.from_str(tile_str)

    @staticmethod
    def from_tile34_index(tile34_index, with_akadora = False) :
        tile136_offset = tile34_index * 4
        offset = 0 if with_akadora else 1 # 赤ドラ回避のためのオフセット
        return Tile.from_tile136(tile136_offset + offset) 

    @staticmethod
    def equal(tile1, tile2, ignore_akadora = False)  :
        same_mark = tile1.suit == tile2.suit and tile1.number == tile2.number
        if ignore_akadora :
            return same_mark
        else :
            return same_mark and (tile1.is_aka == tile2.is_aka)

class Meld : 
    CHI = ActionType.CHI
    PON = ActionType.PON
    ANKAN = ActionType.ANKAN
    KAKAN = ActionType.KAKAN
    DAIMINKAN = ActionType.DAIMINKAN
    NUKI = ActionType.NUKI

    LOOKUP_TABLE_MELD136_TYPE = {CHI : "chi", PON : "pon", ANKAN : "kan", KAKAN : "kan", DAIMINKAN : "kan", NUKI : "nuki"}

    def __init__(self, meld_type=None, tiles=None, from_who=None):
        self.type = meld_type
        self.tiles = tiles or []
        self.from_who = from_who

    def __str__(self):
        return "Type: {}, Tiles: {}".format(self.type, self.tiles)

    # for calls in array
    def __repr__(self):
        return self.__str__()

    @property
    def is_opened(self) :
        return not (self.type in (Meld.ANKAN, Meld.NUKI))
    
    def to_meld136(self) :
        meld_type = self.LOOKUP_TABLE_MELD136_TYPE[self.type]
        tiles136 = TilesUtil.tiles_to_tiles136(self.tiles)
        is_open = self.is_opened
        return meld.Meld(meld_type = meld_type, tiles = tiles136, called_tile = tiles136[0], from_who = self.from_who, opened = is_open)

class TilesUtil :
    @staticmethod
    def tiles136_to_tiles(tiles136) :
        return [Tile.from_tile136(tile136) for tile136 in tiles136]

    @staticmethod
    def str_to_tiles(tehai_str) :
        tiles136 = TilesConverter.one_line_string_to_136_array(tehai_str, True)
        return TilesUtil.tiles136_to_tiles(tiles136)

    @staticmethod
    def tiles_to_tiles136(tiles) :
        result_tiles136 = []
        for tile_obj in tiles :
            offset = Tile.tile136_suit_offset(tile_obj.suit)
        
            if tile_obj.is_aka :
                num_offset = offset + (tile_obj.number - 1) * 4
                count = sum(tile == num_offset for tile in result_tiles136)
            else :
                num_offset = offset + (tile_obj.number - 1) * 4
                num_offset_end = num_offset + 4
                if tile_obj.number == 5 and tile_obj.suit != "z":
                    num_offset = num_offset + 1
                count = sum(num_offset <= tile and tile < num_offset_end for tile in result_tiles136)
            
            tile136 = num_offset + count
            result_tiles136.append(tile136)
        
        return result_tiles136

    @staticmethod
    def tiles_to_tiles34(tiles) :
        filtered_tiles = [tile for tile in tiles if tile.to_str() != "?"]
        tiles136 = TilesUtil.tiles_to_tiles136(filtered_tiles)
        return TilesConverter.to_34_array(tiles136)

    @staticmethod
    def tiles_to_str(tiles) :
        tiles136 = TilesUtil.tiles_to_tiles136(tiles)
        return TilesConverter.to_one_line_string(tiles136, True)

    # For mjai protocol
    @staticmethod
    def tiles_str_array_to_tiles(tehai_str_array) :
        return [Tile.from_str(tile_str) for tile_str in tehai_str_array]

    @staticmethod
    def filter_tiles(tiles, filter_tile, ignore_akadora = True) :
        return [tile for tile in tiles if tile.equal(filter_tile, tile, ignore_akadora)]

    @staticmethod
    def tiles_34_to_tiles(tiles_34) :
        # 制限 : 赤ドラなし
        tiles_136 = TilesConverter.to_136_array(tiles_34)
        return TilesUtil.tiles136_to_tiles(tiles_136)

    @staticmethod
    def find_tiles_34_in_tiles(tiles, find_tiles_34) :
        founded = []
        find_tiles = TilesUtil.tiles_34_to_tiles(find_tiles_34)
        for tile in tiles :
            if sum(Tile.equal(find_tile, tile, True) for find_tile in find_tiles) > 0 :
                founded.append(tile)
        return founded

    @staticmethod
    def include_closed_tile(tiles) :
        return any(tile.to_str() == "?" for tile in tiles)



    
