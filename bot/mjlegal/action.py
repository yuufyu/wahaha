import dataclasses
import json
from .mjtypes import Tile, TilesUtil
from .mjtypes import ActionType

@dataclasses.dataclass
class Action :
    type : ActionType
    actor : int
    target : int = -1
    tile : Tile = None
    consumed : list = None
    tsumogiri : bool = False
    rinshan   : bool = False
    reach_decleared : bool = False
    reason : str = None

    # FIXME 関数名に反して、本APIはmjai形式でないpaiを返す。既存のテストを壊さないため、本来のmjai形式変換はto_mjai_jsonに実装。
    def to_mjai(self) :
        res = {
            "type" : self.type.value ,
            "actor" : self.actor
        }
        if self.target != -1 :
            res["target"] = self.target
        if self.tile is not None :
            res["pai"] = self.tile.to_str()
        if self.consumed is not None :
            res["consumed"] = [tile.to_str() for tile in self.consumed]
        if self.type == ActionType.DAHAI :
            res["tsumogiri"] = self.tsumogiri
        if self.type == ActionType.TSUMO :
            res["rinshan"] = self.rinshan
        if self.reason is not None :
            res["reason"] = self.reason
        return res
    
    def to_mjai_json(self) :
        res = {
            "type" : self.type.value ,
            "actor" : self.actor
        }
        if self.target != -1 :
            res["target"] = self.target
        if self.tile is not None :
            res["pai"] = self.tile.to_mjai_str()
        if self.consumed is not None :
            res["consumed"] = [tile.to_mjai_str() for tile in self.consumed]
        if self.type == ActionType.DAHAI :
            res["tsumogiri"] = self.tsumogiri
        if self.reason is not None :
            res["reason"] = self.reason
        return res

    def to_str(self) :
        return json.dumps(self.to_mjai())

    def __str__(self) :
        return self.to_str()

    def __repr__ (self) :
        return self.to_str()




