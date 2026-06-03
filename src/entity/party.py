"""party.py
プレイヤーキャラクターのメンバーリストとメンバー全体情報の管理
"""
from math import hypot
import pyxel as px
from entity import Character, CharacterParam, PlayerSprite, FieldSprite
from field_map import EventPoint
import service_locater as di

# ロギング設定
import logging

logger = logging.getLogger(__name__)


class Party:
    """パーティーメンバー統括クラス
    - フィールドでの先頭キャラ描画およびフィールド移動処理
    """

    _max_members = 3

    def __init__(self):
        """初期化"""
        # サービスロケータ登録
        self.player_list: list[Character] = []

        # 初期PTメンバ（主人公）の登録
        self.regist_dummy_hero()  # ここでやるべきではない？
        self.add_ptmember(di.ref.hero)

        # フィールド画面用スプライトの設定
        self.field_sprite: FieldSprite = self.set_field_sprite()

        self.is_moving: bool = False  # 移動中フラグ
        self.move_speed: float = 2.0  # 移動速度（ピクセル/フレーム）

        # 現在地の設定
        start_point = "p01"
        tmp_point = di.ref.map.get_point(start_point)
        if tmp_point is None:
            logger.critical(
                f"指定されたイベントポイント({start_point})は定義されていません"
            )
            quit()
        self.current_point: EventPoint = tmp_point

        start_point = di.ref.map.get_point(self.current_point.id)
        if start_point:
            # プレイヤー座標はワールドマップ上の絶対座標
            di.ref.hero.set_position(start_point.x, start_point.y)

        # ジェネレータ変数にダミーを定義
        self.move_generator = self._update_movement(self.current_point)

    def regist_dummy_hero(self):
        """ダミー主人公データの登録"""
        # キャラクターの初期化
        hero_param = CharacterParam(
            name="勇者",
            hp=100,
            mp=20,
            strength=10,
            magic=5,
            defense=8,
            speed=12,
            luck=10,
        )
        # PlayerSprite は pyxel.blt同様pyxel.Imageオブジェクトを受け取り可能
        charimage = px.Image.from_image("assets/image/charatest.bmp")
        char_x = 20  # 初期X座標
        char_y = 20  # 初期Y座標
        hero_sprite = PlayerSprite(char_x, char_y, charimage)  # img=0 を明示的に指定
        hero = Character(param=hero_param, sprite=hero_sprite, id=1)  # id=1を設定
        di.register(di.ServiceKey.HERO, hero)

    def add_ptmember(self, new_member: Character) -> None:
        """パーティーメンバーの追加"""
        if len(self.player_list) >= self._max_members:
            #!!!! ここでメンバー交代の選択処理（メニュー
            return
        self.player_list.append(new_member)

    def set_field_sprite(self):
        """先頭キャラのスプライトイメージをフィールド描画用として設定"""
        x, y = 0, 0  # 描画位置
        u, v = 0, 0  # イメージの取得相対位置
        w, h = 16, 16  # 取得するイメージのサイズ
        return FieldSprite(x, y, self.player_list[0].sprite.img, u, v, w, h)

    def _update_movement(self, target_point: EventPoint):
        """移動中の現在位置および描画位置の更新"""
        target_x, target_y = target_point.x, target_point.y
        current_x, current_y = self.current_point.x, self.current_point.x

        while True:
            dx = target_x - current_x
            dy = target_y - current_y
            distance = hypot(dx, dy)

            if distance <= self.move_speed:
                self.current_point = target_point
                self.is_moving = False
                return

            yield

    def move_to(self, target_point_id: str):
        """フィールド移動先の設定と移動ジェネレータ生成"""
        target_point = di.ref.map.get_point(target_point_id)
        if target_point is None:
            quit()
        self.is_moving = True
        self.move_generator = self._update_movement(target_point)

    def update(self):
        if self.is_moving:
            try:
                next(self.move_generator)
            except StopIteration:
                pass

    def draw(self, screen_x: int, screen_y: int):
        self.field_sprite.draw(screen_x, screen_y)
