"""scene_manager.py
シーン管理クラス

- 管理機能
  - シーンのスタックを管理（追加・削除）
  - 最終スタックの更新と描画
"""

from __future__ import annotations
from . import SCENE_NAME, get_scene, BaseScene


class SceneManager:
    """Sceneインスタンス管理クラス"""

    _instance: SceneManager | None = None

    def __init__(self):
        """初期化"""
        self._stacks: list[BaseScene] = []

    def next_scene(self, scene_name: SCENE_NAME):
        """次のシーンへ進む"""
        instance = get_scene(scene_name)()
        self._stacks.append(instance)

    def previous_scene(self):
        """前のシーンに戻る"""
        self._stacks.pop()

    def get_now_scene(self) -> BaseScene:
        """現在のシーンを返す"""
        return self._stacks[-1]

    def change_scene(self, scene_name: SCENE_NAME):
        """完全に別のシーンへ切り替える（前シーン戻り不可）"""
        self._stacks.clear()
        self.next_scene(scene_name)

    def update(self):
        """管理クラス配下のインスタンス更新およびインスタンス応答の処理"""
        if len(self._stacks):
            self._stacks[-1].update()

    def draw(self):
        """管理クラス配下のインスタンスを描画"""
        if len(self._stacks):
            self._stacks[-1].draw()
