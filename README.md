# wahaha

A mahjong AI that supports 3-player Japanese Riichi Mahjong.

## Method


## Encoder specification

### Train data
|Class|Token|Offset|Count|Range|Note|
|----|----|----|----|----|----|
|Special|[PAD]|0|1|0 - 0|-|
| |[CLS]|1|1|1 - 1|-|
| |[SEP]|2|1|2 - 2|-|
|GameState|style|3|2|3 - 4|東風[0] 半荘[1]|
| |player_id|5|3|5 - 7|東家[0],南家[1],西家[2]|
| |bakaze|8|3|8 - 10|東場[0], 南場[1], 西場[2]|
| |kyoku|11|3|11 - 13|[0,1,2]|
| |honba|14|4|14 - 17|min(honba, 4)|
| |kyotaku|18|3|18 - 20|min(kyotaku 3)|
| |dora_markers[0]|21|37|21 - 57|tile37|
| |dora_markers[1]|58|37|58 - 94|tile37|
| |dora_markers[2]|95|37|95 - 131|tile37|
| |dora_markers[3]|132|37|132 - 168|tile37|
| |dora_markers[4]|169|37|169 - 205|tile37|
| |delta_score(自家 - 上家)|206|97|206 - 302|clip(delta_score/1000, -48, 48) + 48|
| |delta_score(自家 - 下家)|303|97|303 - 399|clip(delta_score/1000, -48, 48) + 48|
| |tehai|400|136|400 - 535|tile136, (副露牌を含めない打牌可能な手牌. 自摸牌は含む.)|
| |tsumo(自摸牌)|536|37|536 - 572|tile37, (直前のtsumoでツモった牌.dahai後は空.)|
|Record|start_kyoku|573|1|573 - 573|-|
|Player0|dahai|574|74|574 - 647|tile37 * 2(tsumogiri = False[0..36],  tsumogiri = Trud[37..73])|
| |reach|648|1|648 - 648|-|
| |pon|649|37|649 - 685|tile37|
| |daiminkan|686|34|686 - 719|tile34|
| |ankan|720|34|720 - 753|tile34|
| |kakan|754|34|754 - 787|tile34|
| |nukidora|788|1|788 - 788|-|
|Player1|dahai|789|74|789 - 862|tile37 * 2(tsumogiri = False[0..36],  tsumogiri = Trud[37..73])|
| |reach|863|1|863 - 863|-|
| |pon|864|37|864 - 900|tile37|
| |daiminkan|901|34|901 - 934|tile34|
| |ankan|935|34|935 - 968|tile34|
| |kakan|969|34|969 - 1002|tile34|
| |nukidora|1003|1|1003 - 1003|-|
|Player2|dahai|1004|74|1004 - 1077|tile37 * 2(tsumogiri = False[0..36],  tsumogiri = Trud[37..73])|
| |reach|1078|1|1078 - 1078|-|
| |pon|1079|37|1079 - 1115|tile37|
| |daiminkan|1116|34|1116 - 1149|tile34|
| |ankan|1150|34|1150 - 1183|tile34|
| |kakan|1184|34|1184 - 1217|tile34|
| |nukidora|1218|1|1218 - 1218|-|
 
 ### Label
|Class|Token|Offset|Count|Range|Note|
|----|----|----|----|----|----|
|Actual action|dahai|0|74|0 - 73|tile37 * 2(tsumogiri = False[0..36],  tsumogiri = Trud[37..73])|
| |reach|74|1|74 - 74|-|
| |pon|75|37|75 - 111|tile37|
| |daiminkan|112|34|112 - 145|tile34|
| |ankan|146|34|146 - 179|tile34|
| |kakan|180|34|180 - 213|tile34|
| |nukidora|214|1|214 - 214|-|
| |hora(tsumo)|215|1|215 - 215|-|
| |hora(rong)|216|1|216 - 216|-|
| |ryukyoku|217|1|217 - 217|-|
| |none(skip)|218|1|218 - 218|-|

