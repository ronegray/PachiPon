"""
ダイスロールエフェクト
"""

from typing import Callable
import pyxel as px

# import service_locater as di
from assets.asset_map import AssetMap, AssetID
from gameutils.base import is_pressed
from const import DICEROLL_FRAME, SoundID, SE_CH

# --- サイコロ画像の仕様 ---
# images[0] の (0,0) から右方向へ 16x16 px で 1〜6 の目が並んでいる前提

# DICE_IMG_BANK = 0


# # サイコロが転がるプレイエリア (64,64)〜(192,192)
# roll_x1, roll_y1 = 84, 84
# roll_x2, roll_y2 = 172, 172


class DiceRollEffect:
    """サイコロを投げて転がすグラフィック演出クラス。
    ・最終位置を重ならないよう先に決定
    ・開始位置(左上隅)から最終位置へ到達する初速を逆算
    update() と draw() を毎フレーム呼ぶだけで完結する。
    """

    dice_size = 16
    dice_margin = 2  # 最終配置でのサイコロ間の最低余白 (px)
    # サイコロが転がるプレイエリア (64,64)〜(192,192)
    roll_x1, roll_y1 = 80, 64
    roll_x2, roll_y2 = 176, 152
    friction = 0.94  # 摩擦係数
    rot_scale = 4.0  # 速度→回転速度の倍率

    def __init__(self):
        self.roll_frames: int
        # Σ FRICTION^t (t=0..roll_frames-1) = (1 - FRICTION^n) / (1 - FRICTION)
        # 初速逆算時の定数。roll_frames が変わらない限り毎回同じ値。
        self._total_scale: float  # = (1.0 - self.friction**self.roll_frames) / (
        # 1.0 - self.friction
        # )

        self.dice_img: px.Image
        self.count: int = 0
        self.values: list[int] = []
        self.final_values: list[int] = []
        self.elapsed = 0
        self.flick_t = 0
        self.is_rolling = False

        self.draw_commands: list[Callable] = []

        # per-die 状態 (start() で初期化)
        self.positions: list[list[float]] = []
        self.velocities: list[list[float]] = []
        self.rotations: list[float] = []
        self.rot_speeds: list[float] = []
        self._final_positions: list[list[float]] = []  # 確定後のスナップ先

    def load_diceimage(self) -> None:
        """マップ画像データの遅延ロード（pyxpalロード後に実行）"""
        self.dice_img = px.Image.from_image(AssetMap.get_assetpath(AssetID.IMAGE_DICE))

    def _make_final_positions(self, count: int) -> list[list[float]]:
        """重ならない最終位置を rejection sampling で決定。

        スタートは左上隅(PLAY_X1, PLAY_Y1)周辺なので、
        最終位置は必ず右下方向になるよう x/y の下限を少し上げている。
        """
        positions: list[list[float]] = []

        # vx, vy が必ず正になるようスタート最大オフセット(6px)より大きく取る
        x_min = DiceRollEffect.roll_x1 + 8
        y_min = DiceRollEffect.roll_y1 + 8
        x_max = DiceRollEffect.roll_x2 - DiceRollEffect.dice_size
        y_max = DiceRollEffect.roll_y2 - DiceRollEffect.dice_size

        sep = (
            DiceRollEffect.dice_size + DiceRollEffect.dice_margin
        )  # 重なりなしに必要な最低距離

        for _ in range(count):
            placed = False
            for _ in range(500):  # rejection sampling
                x = float(px.rndi(x_min, x_max))
                y = float(px.rndi(y_min, y_max))
                # 既存のどの位置とも重ならなければ採用
                if all(
                    abs(x - px) >= sep or abs(y - py) >= sep for px, py in positions
                ):
                    positions.append([x, y])
                    placed = True
                    break

            if not placed:
                # フォールバック: グリッド配置（rejection が500回外れた極限状況用）
                cols = max(1, (x_max - x_min) // sep)
                idx = len(positions)
                gx = float(x_min + (idx % cols) * sep)
                gy = float(y_min + (idx // cols) * sep)
                positions.append([gx, gy])

        return positions

    def start(self, count: int, roll_frames: int = DICEROLL_FRAME) -> None:
        """指定個数のサイコロを左上から放り投げ始める"""
        self.roll_frames = roll_frames
        # Σ FRICTION^t (t=0..roll_frames-1) = (1 - FRICTION^n) / (1 - FRICTION)
        # 初速逆算時の定数。roll_frames が変わらない限り毎回同じ値。
        self._total_scale = (1.0 - self.friction**self.roll_frames) / (
            1.0 - self.friction
        )
        self.count = count
        self.elapsed = 0
        self.flick_t = 0
        self.is_rolling = True
        self.values = [px.rndi(1, 6) for _ in range(count)]
        self.final_values = [px.rndi(1, 6) for _ in range(count)]

        # ① 重ならない最終位置を先に確定
        self._final_positions = self._make_final_positions(count)

        self.positions = []
        self.velocities = []
        self.rotations = []
        self.rot_speeds = []

        for i in range(count):
            # ② スタート位置: 左上隅に小さなばらつき
            sx = float(DiceRollEffect.roll_x1 + px.rndi(0, 6))
            sy = float(DiceRollEffect.roll_y1 + px.rndi(0, 6))
            self.positions.append([sx, sy])

            # ③ 最終位置に届く初速を逆算
            #    pos(n) = pos(0) + v0 * total_scale  →  v0 = Δpos / total_scale
            fx, fy = self._final_positions[i]
            vx = (fx - sx) / self._total_scale
            vy = (fy - sy) / self._total_scale
            self.velocities.append([vx, vy])

            self.rotations.append(float(px.rndi(0, 359)))
            speed0 = (vx**2 + vy**2) ** 0.5
            self.rot_speeds.append(speed0 * self.rot_scale)
        px.play(SE_CH, SoundID.DICE_ROLL, resume=True)

    def update(self) -> None:
        if not self.is_rolling:
            return

        if is_pressed("decide", "hold") or is_pressed("cancel", "hold"):
            self.elapsed = self.roll_frames
            self._finish()

        self.elapsed += 1
        self.flick_t += 1

        for i in range(self.count):
            vx, vy = self.velocities[i]

            # 移動
            self.positions[i][0] += vx
            self.positions[i][1] += vy

            # 摩擦で減速
            vx *= self.friction
            vy *= self.friction
            self.velocities[i] = [vx, vy]

            # 速度に連動して回転も減速
            speed = (vx**2 + vy**2) ** 0.5
            self.rot_speeds[i] = speed * self.rot_scale
            self.rotations[i] = (self.rotations[i] + self.rot_speeds[i]) % 360

        # ちらつき間隔を進捗に応じて 3→11 フレームへ伸ばす
        progress = self.elapsed / self.roll_frames
        flick_interval = 3 + int(progress * 8)
        if self.flick_t >= flick_interval:
            self.flick_t = 0
            self.values = [px.rndi(1, 6) for _ in range(self.count)]

        # 演出終了: 浮動小数点の誤差を消すため最終位置へスナップして確定
        if self.elapsed >= self.roll_frames:
            self._finish()

    def _finish(self) -> None:
        self.values = self.final_values
        self.positions = [list(fp) for fp in self._final_positions]
        self.rotations = [0.0] * self.count
        self.rot_speeds = [0.0] * self.count
        self.is_rolling = False

    def draw(self) -> None:
        """各サイコロをそれぞれの位置に描画"""
        self.draw_commands.clear()
        for i, v in enumerate(self.values):
            sx = (v - 1) * DiceRollEffect.dice_size
            dx = int(self.positions[i][0])
            dy = int(self.positions[i][1])
            rot = int(self.rotations[i])
            # px.blt(
            #     dx,
            #     dy,
            #     self.dice_img,
            #     sx,
            #     0,
            #     DiceRollEffect.dice_size,
            #     DiceRollEffect.dice_size,
            #     px.COLOR_GREEN,
            #     rot,
            # )
            self.draw_commands.append(
                lambda dx=dx, dy=dy, sx=sx, rot=rot: px.blt(
                    dx,
                    dy,
                    self.dice_img,
                    sx,
                    0,
                    DiceRollEffect.dice_size,
                    DiceRollEffect.dice_size,
                    px.COLOR_GREEN,
                    rot,
                )
            )
            # self.draw_commands[-1]

    def get_draw_commands(self) -> list[Callable]:
        """コマンドジェネレータ用にdraw内容を取得"""
        self.draw()
        return self.draw_commands

    @property
    def total(self) -> int:
        """確定後の合計値"""
        return sum(self.values)
