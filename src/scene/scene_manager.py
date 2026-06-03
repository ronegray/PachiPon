"""scene_manager.py
シーン管理クラス

- 管理機能
  - シーンのスタックを管理（追加・削除）
  - 最終スタックの更新と描画
"""
from __future__ import annotations

# from .scene_protocol import SceneTransition
from .scene_dictionary import SCENE_NAME, get_scene
from .scene_base import BaseScene


class SceneManager:
    """Sceneインスタンス管理クラス"""

    _instance: SceneManager | None = None
    # transition = SceneTransition

    def __init__(self):
        """初期化"""
        self.stacks: list[BaseScene] = []

    def next_scene(self, scene_name: SCENE_NAME):
        """次のシーンへ進む"""
        instance = get_scene(scene_name)()
        self.stacks.append(instance)

    def previous_scene(self):
        """前のシーンに戻る"""
        self.stacks.pop()

    def change_scene(self, scene_name: SCENE_NAME):
        """完全に別のシーンへ切り替える（前シーン戻り不可）"""
        self.stacks.clear()
        self.next_scene(scene_name)

    def update(self):
        """管理クラス配下のインスタンス更新およびインスタンス応答の処理"""
        if len(self.stacks):
            # action = self.stacks[-1].update()
            # match action:
            #     case SceneTransition.FORWARD:
            #         pass
            #     case SceneTransition.PREVIOUS:
            #         # 現在の階層をクローズして前のスタックへ戻る
            #         self.pop_stack()
            #     case SceneTransition.REPLACE:
            #         # 全階層をクローズしてスタックを全消去
            #         self.stacks.clear()
            self.stacks[-1].update()

    def draw(self):
        """管理クラス配下のインスタンスを描画"""
        if len(self.stacks):
            self.stacks[-1].draw()
