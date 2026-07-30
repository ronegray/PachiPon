"""party.py
プレイヤーキャラクターのメンバーリストとメンバー全体情報の管理
"""

import logging
from math import hypot
import pyxel as px
from const import ENCOUNT_THRESHOLD, FIELD_MESSAGE_HEIGHT
from gameutils.lib import Window
import service_locater as di
from field_map import EventPoint, Route
from helper import diceroll
import command.system_command as s_cmd
from field_map import MapGraph  # , ROUTE_DIR

# from command import CommandManager
# from scene import SceneManager
from . import Character, FieldSprite, EntityParam, PlayerSprite

# ロギング設定
logger = logging.getLogger(__name__)


class Party:
    """パーティーメンバー統括クラス
    - フィールドでの先頭キャラ描画およびフィールド移動処理
    """

    _member_list: list[Character] = []
    _max_members = 3  # 最大パーティメンバー数
    _top_index = 0  # リスト先頭キャラのインデックス
    _field_sprite: FieldSprite
    _is_event_point: bool
    _pt_is_moving: bool
    _pt_is_encount: bool
    _pt_on_route: Route | None
    _move_speed: float
    _current_point: EventPoint
    _move_target_point_id: str = ""
    _world_x: float
    _world_y: float
    _pt_foods: int
    _pt_golds: int
    _pt_eventflg: dict[str, bool]
    past_turns: int = 0
    info_window: Window
    pt_msg_window: Window

    def __init__(
        self, map: MapGraph
    ):  # , cmdmgr: CommandManager, scnmgr: SceneManager):
        """初期化"""
        self.map = map
        self.cmdmgr = di.ref.cmdmgr
        self.scnmgr = di.ref.scnmgr
        # self.cmdmgr = cmdmgr
        # self.scnmgr = scnmgr
        # # 初期PTメンバ（主人公）の登録
        # self.regist_dummy_hero()  # そもそもやるべきではない？
        # self.regist_dummy_hero()
        # self.regist_dummy_hero()
        # self.add_ptmember(di.ref.hero)

        # フィールド画面用スプライトの設定
        self._field_sprite: FieldSprite  # = self.set_field_sprite()

        # 関連フラグの設定
        self._pt_is_moving = False  # 移動中フラグ
        self._pt_is_encount = False  # エンカウントフラグ
        self._pt_on_route = None  # 現在ルートの設定
        self._pt_is_battle = False  # 戦闘中フラグ
        self._is_event_point = True
        self._move_speed = 2.0  # 移動速度（ピクセル/フレーム）

        # 現在地の設定
        start_point = "p01"
        tmp_point = self.map.get_point(start_point)
        if tmp_point is None:
            errmsg = f"指定されたイベントポイント({start_point})は定義されていません"
            logger.critical(errmsg, exc_info=True)
            raise KeyError(errmsg)
        self._current_point = tmp_point
        self._world_x = self._current_point.x
        self._world_y = self._current_point.y

        # パーティー単位のパラメータ
        self._pt_foods = 0
        self._pt_golds = 50
        self._pt_eventflg = {}
        # # パーティーメッセージウインドウの生成
        # x_offset = 4
        # message_pos = (x_offset, px.height // 2 - (FIELD_MESSAGE_HEIGHT // 2))
        # message_size = (px.width - (x_offset * 2), FIELD_MESSAGE_HEIGHT)
        # self.pt_msg_window = Window("basic", *message_pos, *message_size, "once", 0)

        # 移動用ジェネレータ変数にダミーを定義
        # self.move_generator = self._update_movement(self._current_point)
        self.move_generator = None

    def generate_pt_window(self) -> None:
        # 現在表示ウインドウ
        self.info_window = Window("small", px.width, 0, 56, 32, "once")
        # パーティーメッセージウインドウの生成
        x_offset = 4
        message_pos = (x_offset, px.height // 2 - (FIELD_MESSAGE_HEIGHT // 2))
        message_size = (px.width - (x_offset * 2), FIELD_MESSAGE_HEIGHT)
        self.pt_msg_window = Window("basic", *message_pos, *message_size, "once", 0)

    def regist_dummy_hero(self):
        """ダミー主人公データの登録"""
        # キャラクターの初期化
        # hero_param = EntityParam(
        #     name="メンバー" + str(len(self._member_list)),
        #     strength=px.rndi(1, 10),
        #     arcane=px.rndi(1, 10),
        #     endurance=px.rndi(1, 10),
        #     speed=px.rndi(1, 10),
        #     luck=px.rndi(1, 10),
        #     max_hp=px.rndi(1, 10),
        #     max_mp=px.rndi(1, 10),
        # )
        # PlayerSprite は pyxel.blt同様pyxel.Imageオブジェクトを受け取り可能
        charimage = px.Image.from_image("assets/image/character16.bmp")
        char_x = 20  # 初期X座標
        char_y = 20  # 初期Y座標
        # hero_sprite = PlayerSprite(char_x, char_y, charimage)  # img=0 を明示的に指定
        # hero = Character(id=0, param=hero_param, sprite=hero_sprite)  # id=1を設定
        hero = Character(
            id=len(self._member_list),
            param=EntityParam(
                name="ほげほげふーばー" + str(len(self._member_list)),
                strength=px.rndi(1, 10) * 10,
                arcane=px.rndi(1, 10) * 10,
                endurance=px.rndi(1, 10) * 10,
                speed=px.rndi(1, 10) * 10,
                luck=px.rndi(1, 10) * 10,
                max_hp=px.rndi(5, 10) * 10,
                max_mp=px.rndi(5, 10) * 10,
            ),
            sprite=PlayerSprite(char_x, char_y, charimage),
        )
        # if len(self._member_list) == 0:
        #     di.register(di.ServiceKey.HERO, hero)
        #     self.add_ptmember(di.ref.hero)
        # elif len(self._member_list) == 1:
        #     di.register(di.ServiceKey.MEMBER1, hero)
        #     self.add_ptmember(di.ref.mem1)
        # elif len(self._member_list) == 2:
        #     di.register(di.ServiceKey.MEMBER2, hero)
        #     self.add_ptmember(di.ref.mem2)
        self.add_ptmember(hero)
        self.set_field_sprite()

    def get_top_index(self) -> int:
        """生存中PTメンバーの先頭キャラのリストインデックスを取得"""
        return self._top_index

    def get_member_count(self) -> int:
        """PTメンバーの人数を取得（生死問わず）"""
        return len(self._member_list)

    def get_active_member_count(self) -> int:
        """PTメンバーの生存人数を取得"""
        return len([mem for mem in self._member_list if mem.is_alive])

    def update_top_index(self) -> None:
        """生存中PTメンバーの先頭キャラのリストインデックスを更新"""
        for i, member in enumerate(self._member_list):
            if member.is_alive:
                self._top_index = i
                return

    def get_member(self, member_id: int = 0) -> Character:
        """指定したリストインデックスが示すPTメンバーを取得
        - 範囲外の値はメンバー数の剰余にて指定"""
        rounded_index = member_id % len(self._member_list)
        return self._member_list[rounded_index]

    def get_active_member(self) -> list[Character]:
        """生存中メンバーのリストを取得"""
        return [member for member in self._member_list if member.is_alive]

    def get_allmember(self) -> list[Character]:
        """パーティーメンバー全員を取得"""
        return self._member_list

    def add_ptmember(self, new_member: Character) -> None:
        """パーティーメンバーの追加"""
        if len(self._member_list) >= self._max_members:
            #!!!! ここでメンバー交代の選択処理（メニュー
            return
        self._member_list.append(new_member)

    def set_field_sprite(self):
        """先頭キャラのスプライトイメージをフィールド描画用として設定"""
        x, y = 0, 0  # 描画位置
        u, v = 0, 0  # イメージの取得相対位置
        w, h = 16, 16  # 取得するイメージのサイズ
        # return FieldSprite(x, y, self._member_list[0].sprite.img, u, v, w, h)
        self._field_sprite = FieldSprite(
            x, y, self._member_list[0].sprite.img, u, v, w, h
        )

    def set_sprite_direction(self, direction: str) -> None:
        """パーティのフィールドスプライトの方向設定用ラッパー"""
        self._field_sprite.set_direction(direction)

    # def _update_movement(self, target_point: EventPoint):
    #     """移動中の現在位置および描画位置の更新"""
    #     target_x, target_y = target_point.x, target_point.y

    #     while True:
    #         dx = target_x - self._world_x
    #         dy = target_y - self._world_y
    #         distance = hypot(dx, dy)

    #         if distance <= self._move_speed:
    #             self._current_point = target_point
    #             self._pt_is_moving = False
    #             self._field_sprite._is_moving = False
    #             return
    #         else:
    #             # 移動方向を正規化
    #             if distance > 0:
    #                 direction_x = dx / distance
    #                 direction_y = dy / distance
    #             else:
    #                 direction_x = 0
    #                 direction_y = 0

    #         self._world_x += direction_x * self._move_speed
    #         self._world_y += direction_y * self._move_speed

    #         yield

    # def move_to(self, target_point_id: str):
    #     """フィールド移動先の設定と移動ジェネレータ生成"""
    #     target_point = di.ref.map.get_point(target_point_id)
    #     if target_point is None:
    #         quit()
    #     self._pt_is_moving = self._field_sprite._is_moving = True
    #     self.move_generator = self._update_movement(target_point)

    def _update_move_route(self, target_point: EventPoint, to_route: Route):
        """移動中の現在位置および描画位置の更新"""
        target_x, target_y = target_point.x, target_point.y
        dx = target_x - self._world_x
        dy = target_y - self._world_y
        distance = hypot(dx, dy)
        encount_interval = distance // (to_route.cost + 1)
        encounts = 0
        current_count = 0

        while True:
            dx = target_x - self._world_x
            dy = target_y - self._world_y
            distance = hypot(dx, dy)

            if encount_interval <= current_count:
                self.past_turns += 1
                if self.encount_check(encounts):
                    encounts += 1
                    # di.ref.scnmgr.next_scene("battle")
                    # di.ref.scnmgr.next_scene("battlesplash")
                    # self.scnmgr.next_scene("battlesplash")
                    self._pt_is_encount = True
                current_count = 0
                self.have_food()
                yield
            else:
                current_count += self._move_speed

            if distance <= self._move_speed:
                # 目的地到着
                self._current_point = target_point
                self._pt_is_moving = False
                self.set_current_route()
                self._field_sprite._is_moving = False
                return
            else:
                # 移動方向を正規化
                if distance > 0:
                    direction_x = dx / distance
                    direction_y = dy / distance
                else:
                    direction_x = 0
                    direction_y = 0

            self._world_x += direction_x * self._move_speed
            self._world_y += direction_y * self._move_speed

            yield

    def get_current_point(self) -> EventPoint:
        """現在のパーティー所在地イベントポイントを取得
        移動中は移動前のイベントポイントを指す"""
        return self._current_point

    def set_current_route(self, on_route: Route | None = None) -> None:
        """現在の移動中ルートを設定"""
        self._pt_on_route = on_route

    def get_current_route(self) -> Route:
        """現在の移動中ルートを取得※静止状態の場合はNoneを返す"""
        if self._pt_on_route is None:
            errmsg = "非移動中の呼び出しは想定されていません"
            logger.critical(errmsg, exc_info=True)
            raise RuntimeError(errmsg)
        return self._pt_on_route

    def move_route(self, to_route: Route):
        """フィールド移動先の設定と移動ジェネレータ生成"""
        target_point = di.ref.map.get_point(to_route.to_id)
        if target_point is None:
            quit()
        self._pt_is_moving = self._field_sprite._is_moving = True
        self.move_generator = self._update_move_route(target_point, to_route)

    def encount_check(self, encounts: int) -> bool:
        """モンスター遭遇チェック(遭遇する毎に頻度低下)"""
        roll = diceroll(3)
        if roll + encounts <= ENCOUNT_THRESHOLD:
            return True
        return False

    # def set_event_point_status(self, status: bool):
    #     self._is_event_point = status

    def set_moving_status(self, status: bool):
        self._pt_is_moving = status

    def get_pt_world_address(self) -> tuple[float, float]:
        """パーティのワールド座標を取得"""
        return self._world_x, self._world_y

    def earn_gold(self, gold: int) -> int:
        """獲得ゴールドをPTに加算し総額を取得"""
        self._pt_golds += gold
        return self._pt_golds

    def have_food(self):
        """食事処理"""
        is_foods = self._pt_foods > 0
        actives = self.get_active_member()
        comsume_foods = px.ceil(sum([mem.param.level for mem in actives]) / 10)
        self._pt_foods -= comsume_foods
        # 減少によりフードが0以下になった場合
        if self._pt_foods <= 0:
            cmd1 = s_cmd.FoodShortageEffect(self.pt_msg_window)
            self.cmdmgr.push_command(cmd1)
            for mem in actives:
                mem.decrease_hp(mem.param.hp // 10)
                mem.decrease_mp(mem.param.mp // 10)
            if is_foods:
                # 0以下になった初回だけメッセージ表示
                cmd2 = s_cmd.FoodShortageMessage(self.pt_msg_window)
                self.cmdmgr.push_command(cmd2)

    def update(self):
        """移動時のジェネレータとスプライト描画内容を更新"""
        if self._pt_is_moving:
            try:
                next(self.move_generator)  # type:ignore
                # 戦闘開始
                if self._pt_is_encount and self.cmdmgr.is_empty:
                    self.scnmgr.next_scene("battlesplash")
                    self._pt_is_encount = False
            except StopIteration:
                pass
        self._field_sprite.update()

    def draw(self, screen_x: int, screen_y: int):
        """パーティ先頭キャラの描画"""
        # パーティ先頭キャラの描画
        self._field_sprite.draw(screen_x // 2, screen_y // 2)

        # ルート情報の表示
        if not self._pt_is_moving:
            route_list = self._current_point.get_reachable_routes()
            for route in route_list:
                match route.direction:
                    case "up":
                        info_x, info_y = 108, 84
                    case "left":
                        info_x, info_y = 60, 120
                    case "right":
                        info_x, info_y = 156, 120
                    case "down":
                        info_x, info_y = 108, 152
                px.dither(0.5)
                px.rect(info_x, info_y, 40, 16, px.COLOR_GRAY)
                px.dither(1)
                px.rectb(info_x, info_y, 40, 16, px.COLOR_RED)
                px.text(
                    info_x + 2,
                    info_y + 2,
                    f"cost:{route.cost}\nthreat:{route.threat}",
                    px.COLOR_BLACK,
                )

    def draw_ptinfo(self):
        # パーティー情報ウインドウの描画
        self.info_window.draw()
        offset = 3
        self.info_window.drawText(
            self.info_window.x + (Window._chip_size // 2) + offset,
            self.info_window.y + (Window._chip_size // 2) + offset,
            [
                [f"TURN:{self.past_turns:>6}"],
                [f"GOLD:{self._pt_golds:>6}"],
                [f"FOOD:{self._pt_foods:>6}"],
            ],
            px.COLOR_WHITE,
        )
