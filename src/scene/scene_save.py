# from datetime import datetime
# from gameutils.base import check_file, read_json, write_json
# from assets.asset_map import AssetID, AssetMap
# import service_locater as di
# # from item import ItemPool, StackPool
# # from entity import Party, Character, Equips
# from . import BaseScene


# class SceneSavedata(BaseScene):
#     """同じクラスにしてモードとか継承で切り分けすべき？"""
#     def __init__(self) -> None:
#         """初期化"""
#         super().__init__()
#         self.situation = "system"

#         self.save()

#         """このシーンでは遷移元のBGMを引き継ぐ為load_bgmは無し"""

#     def update(self):
#         pass

#     def draw(self):
#         pass

#     def save(self, slot_no: int = 0):
#         savedatas = {}
#         savedatas["savetime"] = datetime.now().strftime("%Y/%m/%d %H:%M:%S.%f")[:-4]
#         savedatas["pl_item"] = di.ref.pl_item.save_item()
#         savedatas["pl_stack"] = di.ref.pl_stack.save_stack()
#         # savedatas["events"] = di.ref.map~~~
#         savedatas["pt"] = di.ref.pt.save_party()
#         savedatas["chars"] = [mem.save_character()
#                 for mem in di.ref.pt.get_allmember()]
#         savedatas["equips"] = [mem.equipments.save_equip()
#                 for mem in di.ref.pt.get_allmember()]

#         # 情報作成時＝データ内容変更時と捉えて、データ内容をファイルに出力
#         savefilename = (AssetMap.get_assetpath(AssetID.SAVEDATA_DIR)
#                         + AssetMap.get_assetpath(AssetID.SAVEDATA_FILE)
#                         + str(slot_no))
#         path = check_file(savefilename, "w")
#         if path is None:
#             raise SystemError("セーブデータファイルが出力出来ません")

#         write_json(path, savedatas)
