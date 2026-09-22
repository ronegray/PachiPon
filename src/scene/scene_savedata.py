from datetime import datetime
import pyxel as px
from gameutils.base import is_pressed, get_filelist, read_json, check_file, write_json  # , read_bin
from gameutils.lib import Window  # , WindowAction
from assets.asset_map import AssetID, AssetMap
import service_locater as di
from helper import upper_str, upper_int_spaced, upper_int_zeroed, format_leftright
from entity import Party, PlayerSprite, EntityParam, Character, EquipSlot
from skill import SkillID
from field_map import MapGraph
from . import BaseScene


class SceneBaseSavedata(BaseScene):
    # カーソルイメージアドレス
    _img_cursor = [16, 0, Window._chip_size, Window._chip_size]
    # データウインドウ描画数
    _max_draw_datas: int = 5

    def __init__(self) -> None:
        """初期化"""
        super().__init__()
        self.situation = "system"
        # データファイルの中身を読み込んで辞書化
        self.savedatas: list[dict] = []
        savedata_pathlist = get_filelist(AssetMap.get_assetpath(AssetID.SAVEDATA_DIR))
        if savedata_pathlist is None:  # or len(savedata_pathlist) < self._max_draw_datas:
            return
        for i, path in enumerate(savedata_pathlist):
            self.savedatas.append({"data": read_json(path)})
            self.savedatas[i]["img"] = None
            str_line = ["", "", ""]

            # データウインドウ描画内容生成
            dat = self.savedatas[i]["data"]
            str_line = ["", "", ""]
            datano = "オートセーブ" if i == 0 else "データ" + upper_int_zeroed(i, 2)
            savetime = upper_str(dat["savetime"][:-6])
            str_line[0] = format_leftright(datano, savetime, 60)

            charimg_size = 16
            padding = 3
            img = px.Image(len(dat["chars"]) * (charimg_size + padding), charimg_size)
            img.rect(0, 0, img.width, img.height, px.COLOR_GREEN)
            for idx, (char_id, chara) in enumerate(dat["chars"].items()):
                tmp_sprite = PlayerSprite(0, 0, chara[0]["sprite_type"])
                img.blt(
                    padding + idx * (charimg_size + padding),
                    0,
                    tmp_sprite.img,
                    0,
                    0,
                    charimg_size,
                    charimg_size,
                )

            turn = f"ターン：{upper_int_spaced(dat["pt"]["turns"], 4)}"
            point = f"現在地：{di.ref.map.get_point(dat["pt"]["point"]).name}"  # type: ignore
            str_line[2] = "　" * 9 + turn + "　　" + point

            self.savedatas[i]["img"] = img
            self.savedatas[i]["str_line"] = str_line

        for i in range(len(self.savedatas), self._max_draw_datas):
            self.savedatas.append({"data": None})
            # self.savedatas[i]["img"] = None
            str_line = ["", "", ""]

            # データウインドウ描画内容生成
            dat = self.savedatas[i]["data"]
            str_line = ["", "", ""]
            datano = "オートセーブ" if i == 0 else "データ" + upper_int_zeroed(i, 2)
            savetime = "００００／００／００　００：００：００"
            str_line[0] = format_leftright(datano, savetime, 60)

            str_line[1] = "　データなし"

            turn = "ターン：－－－－"
            point = "現在地：－－－－"
            str_line[2] = "　" * 9 + turn + "　　" + point

            img = px.Image(1, 1)
            img.rect(0, 0, 1, 1, px.COLOR_NAVY)
            self.savedatas[i]["img"] = img
            self.savedatas[i]["str_line"] = str_line

        self.max_data_count: int = max(2, len(self.savedatas))
        # カーソル関連
        self.data_index: int = 0  # ターゲットデータのインデックス
        self.cursor_index: int = 0  # 画面上の何個目のデータを指すか(0~draw_datas)
        # データ表示ウインドウリスト
        self.data_windows: list[Window] = []
        self.draw_start_index: int = 0
        datwnd_x, datwnd_y = 0, 0
        datwnd_w, datwnd_h = px.width, 48
        # y_offset = 0
        for i in range(self._max_draw_datas):
            # ウインドウインスタンス生成＆イメージ用変数
            self.data_windows.append(
                Window("basic", datwnd_x, datwnd_y + datwnd_h * i, datwnd_w, datwnd_h, "view")
            )
        self.set_datawindow()

    def set_datawindow(self) -> None:
        """データウインドウに表示する内容を設定／更新"""
        draw_x, draw_y = 8, 24
        for i, wnd in enumerate(self.data_windows):
            targetdata_index = i + self.draw_start_index
            wnd.set_message(self.savedatas[targetdata_index]["str_line"])
            img = self.savedatas[targetdata_index]["img"]
            wnd.window_image.rect(draw_x, draw_y, img.width, img.height, px.COLOR_NAVY)
            wnd.window_image.blt(draw_x, draw_y, img, 0, 0, img.width, img.height, px.COLOR_GREEN)

    def update(self) -> None:
        """更新処理"""

        # for wnd in self.data_windows:
        #     if wnd.update() != WindowAction.CONTINUE:
        #         # キー入力時の処理
        #         # 開発中の為スキップしている
        #         return

        if is_pressed("up"):
            # データの選択位置は常に変化
            self.data_index = (self.data_index - 1) % self.max_data_count
            # カーソル位置（=選択データウインドウ）によって、描画データ内容の更新
            max_draw_index = self._max_draw_datas - 1
            if self.cursor_index == 0:
                if self.draw_start_index == 0:
                    # 操作前カーソルが最上段にあって先頭データから表示されている→最下段、最終データへループ
                    self.cursor_index = max_draw_index
                    self.draw_start_index = self.max_data_count - self._max_draw_datas
                    self.set_datawindow()
                # 操作前カーソルが最上段にある→１つ前のデータが表示される
                else:
                    self.draw_start_index -= 1
                    self.set_datawindow()
            else:
                # カーソルのみ移動する
                self.cursor_index -= 1

        elif is_pressed("down"):
            # データの選択位置は常に変化
            self.data_index = (self.data_index + 1) % self.max_data_count
            # カーソル位置（=選択データウインドウ）によって、描画データ内容の更新
            max_draw_index = self._max_draw_datas - 1
            if self.data_index == 0:
                # 操作後データ表示位置が先頭なら、先頭データへループ
                self.cursor_index = self.draw_start_index = 0
                self.set_datawindow()
            elif self.cursor_index == max_draw_index:
                # 操作前カーソル位置が最大ウインドウ表示位置→１つ後ろのデータが表示される
                # 前段ifと判定対象が異なるので注意
                self.draw_start_index += 1
                self.set_datawindow()
            else:
                # カーソルのみ移動する
                self.cursor_index += 1

    def draw(self) -> None:
        # for i, wnd in enumerate(self.data_windows):
        for wnd in self.data_windows:
            wnd.draw()
            wnd.draw_message(offset_y=-4)

        px.blt(
            3,
            20 + self.cursor_index * 48,
            self.data_windows[0]._image_chips,
            *self._img_cursor,
            colkey=px.COLOR_BLACK,
        )
        return
        # # 以下デバッグ用
        # y = 0
        # for dat in self.savedatas:
        #     img = dat["img"]
        #     px.blt(0, 0 + y, img, 0, 0, img.width, img.height, px.COLOR_GREEN)
        #     y += 24


class SceneDataLoad(SceneBaseSavedata):
    def __init__(self) -> None:
        """初期化"""
        super().__init__()
        self.situation = "system"

    def update(self) -> None:
        if is_pressed("decide"):
            if self.savedatas[self.data_index]["data"] is None:
                # 何かデータがない系エラーメッセージを入れる
                return
            self.manupilate_data(self.savedatas[self.data_index]["data"])
            # シーンスタックはクリアしてフィールドマップへ遷移
            di.ref.scnmgr.change_scene("map")
            return

        super().update()

    def manupilate_data(self, savedata: dict):
        """データロード"""
        # savedatas = self.savedatas[slot_no]
        # # savedatas["savetime"] = datetime.now().strftime("%Y/%m/%d %H:%M:%S.%f")[:-4]
        # savedatas["pl_item"] = di.ref.pl_item.save_item()
        # savedatas["pl_stack"] = di.ref.pl_stack.save_stack()
        # # savedatas["events"] = di.ref.map~~~
        # savedatas["pt"] = di.ref.pt.save_party()
        # savedatas["chars"] = [mem.save_character()
        #         for mem in di.ref.pt.get_allmember()]
        # savedatas["equips"] = [mem.equipments.save_equip()
        #         for mem in di.ref.pt.get_allmember()]
        #
        # # 情報作成時＝データ内容変更時と捉えて、データ内容をファイルに出力
        # savefilename = (AssetMap.get_assetpath(AssetID.SAVEDATA_DIR)
        #                 + AssetMap.get_assetpath(AssetID.SAVEDATA_FILE)
        #                 + str(slot_no))
        # path = check_file(savefilename, "w")
        # if path is None:
        #     raise SystemError("セーブデータファイルが出力出来ません")

        # write_json(path, savedatas)

        di.ref.cmdmgr.clear_commands()

        di.ref.pl_stack.load_stack(savedata["pl_stack"])
        print(di.ref.pl_stack._stacks)
        di.ref.pl_item.load_item(savedata["pl_item"])
        print(di.ref.pl_item._items)

        # マップデータの初期化
        map = MapGraph()
        di.register(di.ServiceKey.MAPGRAPH, map)
        di.ref.map.load_mapimage()
        # パーティデータの初期化
        pt = Party(map=di.ref.map)
        di.register(di.ServiceKey.PARTY, pt)
        di.ref.pt.load_party(savedata["pt"])

        # キャラクタ情報の生成とデータ反映
        char_x = 112  # 初期X座標(多分中央から動く事ない)
        char_y = 112  # 初期Y座標

        for char_id, memdata in savedata["chars"].items():
            # キャラクタ
            sprite = PlayerSprite(char_x, char_y, memdata[0]["sprite_type"])
            params = EntityParam(**memdata[1])
            char = Character(params, sprite, int(char_id), memdata[0]["sprite_type"])
            # キャラクタ装備
            for slot, pool_id in savedata["equips"][char_id].items():
                if pool_id is None:
                    continue
                pooled = di.ref.pl_item.get(pool_id)
                char.equipments._equipped_items[EquipSlot(slot)] = (pool_id, pooled)  # type: ignore
            # キャラクタスキル
            for skill_id in savedata["skills"][char_id]:
                char.skills.learn_skill(SkillID(skill_id))
            # リセット済Partyへキャラクタを追加
            di.ref.pt.add_ptmember(char)

        # PT情報初期化後の再設定
        di.ref.pt.generate_pt_window()
        di.ref.pt.set_field_sprite()

        # イベントポイント状態の反映
        di.ref.map.load_event(savedata["events"])


class SceneDataSave(SceneBaseSavedata):
    def __init__(self) -> None:
        """初期化"""
        super().__init__()
        self.situation = "system"
        # オートセーブデータの情報を削除（セーブ時は選択不可）
        # self.savedatas.pop(0)
        # self.max_data_count: int = max(2, len(self.savedatas))
        # self.set_datawindow()

    def manupilate_data(self, slot_no: int = 0):
        """データセーブ"""
        savedatas = {}
        savedatas["savetime"] = datetime.now().strftime("%Y/%m/%d %H:%M:%S.%f")[:-4]
        # savedatas["flags"] = di.ref.
        savedatas["events"] = di.ref.map.save_event()
        savedatas["pt"] = di.ref.pt.save_party()
        savedatas["chars"] = {
            str(mem.chara_id): mem.save_character() for mem in di.ref.pt.get_allmember()
        }
        savedatas["equips"] = {
            str(mem.chara_id): mem.equipments.save_equip() for mem in di.ref.pt.get_allmember()
        }
        savedatas["skills"] = {
            str(mem.chara_id): mem.skills.save_skill() for mem in di.ref.pt.get_allmember()
        }
        savedatas["pl_item"] = di.ref.pl_item.save_item()
        savedatas["pl_stack"] = di.ref.pl_stack.save_stack()

        # 情報作成時＝データ内容変更時と捉えて、データ内容をファイルに出力
        savefilename = (
            AssetMap.get_assetpath(AssetID.SAVEDATA_DIR)
            + AssetMap.get_assetpath(AssetID.SAVEDATA_FILE)
            + str(slot_no)
        )
        path = check_file(savefilename, "w")
        if path is None:
            raise SystemError("セーブデータファイルが出力出来ません")

        write_json(path, savedatas)
