"""
シーンモジュール：レベルアップ
"""
import logging
import pyxel as px
import service_locater as di
import command.entity_command as e_cmd
from menu import MenuLevelup
from . import BaseScene, SceneBattle

# ロギング設定
logger = logging.getLogger(__name__)


class SceneLevelup(BaseScene):
    def __init__(self):
        super().__init__()
        self.situation = "system"
        parent_scene = di.ref.scnmgr.get_now_scene()
        if not isinstance(parent_scene, SceneBattle):
            errmsg = (
                f"想定外のシーンから呼び出されました：{parent_scene.__class__.__name__}"
            )
            logger.critical(errmsg, exc_info=True)
            raise TypeError(errmsg)
        (
            self.ctx,
            _,
            self.message_window,
            self.bgimage,
        ) = parent_scene.transfer_battledata()

        di.ref.cmdmgr.push_command(
            e_cmd.GrantReward(self.ctx, self.message_window, di.ref.pt)
        )
        self.target_param: list[str] = []

    def check_levelup(self) -> bool:
        """レベルアップチェックとレベルアップ処理"""
        result = False
        for member in di.ref.pt.get_allmember():
            if member.check_levelup() > 0:
                member.param.level += 1
                self.ctx.actor = member
                di.ref.cmdmgr.push_command(
                    e_cmd.CharacterLevelup(self.ctx, self.message_window)
                )
                self.wndmgr.push_stack(MenuLevelup, member, self.target_param)
                result = True
                break
        return result

    def update(self):
        if di.ref.cmdmgr.is_empty:
            if self.wndmgr.has_stack or self.check_levelup():
                self.wndmgr.update()
                if self.target_param:
                    self.ctx.actor.gain_parameter(self.target_param[0])
                    di.ref.cmdmgr.push_command(
                        e_cmd.CharacterGainHPMP(self.ctx, self.message_window)
                    )
                    self.target_param.clear()
            else:
                di.ref.scnmgr.previous_scene(step=2)

    def draw(self):
        # px.dither(0.3)
        px.blt(0, 0, self.bgimage, 0, 0, self.bgimage.width, self.bgimage.height)
        # px.dither(1)
        if di.ref.cmdmgr.is_empty:
            self.wndmgr.draw()
