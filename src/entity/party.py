"""party.py
プレイヤーキャラクターのメンバーリストとメンバー全体情報の管理
"""
from math import hypot
import pyxel as px
from entity import Character, EntityParam, PlayerSprite, FieldSprite
from field_map import EventPoint
import service_locater as di

# ロギング設定
import logging

logger = logging.getLogger(__name__)


class Party:
    """パーティーメンバー統括クラス
    - フィールドでの先頭キャラ描画およびフィールド移動処理
    """

    _player_list: list[Character] = []
    _max_members = 3  # 最大パーティメンバー数
    _field_sprite: FieldSprite
    _is_event_point: bool
    _pt_is_moving: bool
    _move_speed: float
    _current_point: EventPoint
    _move_target_point_id: str = ""
    _world_x: float
    _world_y: float
    _pt_foods: int
    _pt_golds: int
    _pt_eventflg: dict[str, bool]

    def __init__(self):
        """初期化"""
        # 初期PTメンバ（主人公）の登録
        self.regist_dummy_hero()  # そもそもやるべきではない？
        self.add_ptmember(di.ref.hero)

        # フィールド画面用スプライトの設定
        self._field_sprite = self.set_field_sprite()
        self._pt_is_moving = False  # 移動中フラグ
        self._is_event_point = True
        self._move_speed = 2.0  # 移動速度（ピクセル/フレーム）

        # 現在地の設定
        start_point = "p17"
        tmp_point = di.ref.map.get_point(start_point)
        if tmp_point is None:
            errmsg = f"指定されたイベントポイント({start_point})は定義されていません"
            logger.critical(errmsg, exc_info=True)
            raise KeyError(errmsg)
        self._current_point = tmp_point
        self._world_x = self._current_point.x
        self._world_y = self._current_point.y

        # パーティー単位のパラメータ
        self._pt_foods = 10
        self._pt_golds = 50
        self._pt_eventflg = {}

        # ジェネレータ変数にダミーを定義
        self.move_generator = self._update_movement(self._current_point)

    def regist_dummy_hero(self):
        """ダミー主人公データの登録"""
        # キャラクターの初期化
        hero_param = EntityParam(
            name="勇者",
            hp=100,
            mp=20,
            strength=10,
            arcane=5,
            endurance=8,
            speed=12,
            luck=10,
        )
        # PlayerSprite は pyxel.blt同様pyxel.Imageオブジェクトを受け取り可能
        charimage = px.Image.from_image("assets/image/character16.bmp")
        char_x = 20  # 初期X座標
        char_y = 20  # 初期Y座標
        hero_sprite = PlayerSprite(char_x, char_y, charimage)  # img=0 を明示的に指定
        hero = Character(id=0, base_param=hero_param, sprite=hero_sprite)  # id=1を設定
        di.register(di.ServiceKey.HERO, hero)

    def add_ptmember(self, new_member: Character) -> None:
        """パーティーメンバーの追加"""
        if len(self._player_list) >= self._max_members:
            #!!!! ここでメンバー交代の選択処理（メニュー
            return
        self._player_list.append(new_member)

    def set_field_sprite(self):
        """先頭キャラのスプライトイメージをフィールド描画用として設定"""
        x, y = 0, 0  # 描画位置
        u, v = 0, 0  # イメージの取得相対位置
        w, h = 16, 16  # 取得するイメージのサイズ
        return FieldSprite(x, y, self._player_list[0].sprite.img, u, v, w, h)

    def set_sprite_direction(self, direction: str) -> None:
        """パーティのフィールドスプライトの方向設定用ラッパー"""
        self._field_sprite.set_direction(direction)

    def _update_movement(self, target_point: EventPoint):
        """移動中の現在位置および描画位置の更新"""
        target_x, target_y = target_point.x, target_point.y

        while True:
            dx = target_x - self._world_x
            dy = target_y - self._world_y
            distance = hypot(dx, dy)

            if distance <= self._move_speed:
                self._current_point = target_point
                self._pt_is_moving = False
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

    def move_to(self, target_point_id: str):
        """フィールド移動先の設定と移動ジェネレータ生成"""
        target_point = di.ref.map.get_point(target_point_id)
        if target_point is None:
            quit()
        self._pt_is_moving = self._field_sprite._is_moving = True
        self.move_generator = self._update_movement(target_point)

    def set_event_point_status(self, status: bool):
        self._is_event_point = status

    def set_moving_status(self, status: bool):
        self._pt_is_moving = status

    def get_pt_world_address(self) -> tuple[float, float]:
        """パーティのワールド座標を取得"""
        return self._world_x, self._world_y

    def update(self):
        if self._pt_is_moving:
            try:
                next(self.move_generator)
            except StopIteration:
                pass
        self._field_sprite.update()

    def draw(self, screen_x: int, screen_y: int):
        """パーティ先頭キャラの描画"""
        self._field_sprite.draw(screen_x, screen_y)
