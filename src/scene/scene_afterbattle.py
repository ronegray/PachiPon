"""
シーンモジュール：レベルアップ
"""

import logging
from enum import IntEnum, auto
import pyxel as px
from const import SoundID
from gameutils.lib import MenuYesNo
import service_locater as di
import command.entity_command as en_cmd
from menu import MenuLevelup
from . import BaseScene, SceneBattle

# ロギング設定
logger = logging.getLogger(__name__)


class LocalPhase(IntEnum):
    REWARD = auto()
    CHECK_LEVELUP = auto()
    CHOOSE_DESTINATION = auto()


class SceneAfterBattle(BaseScene):
    def __init__(self):
        super().__init__()
        self.situation = "system"
        parent_scene = di.ref.scnmgr.get_now_scene()
        if not isinstance(parent_scene, SceneBattle):
            errmsg = f"想定外のシーンから呼び出されました：{parent_scene.__class__.__name__}"
            logger.critical(errmsg, exc_info=True)
            raise TypeError(errmsg)
        (
            self.ctx,
            _,
            self.message_window,
            self.bgimage,
        ) = parent_scene.transfer_battledata()

        di.ref.cmdmgr.push_command(en_cmd.GrantReward(self.ctx, self.message_window, di.ref.pt))
        self.target_param: list[str] = []

        self.phase: LocalPhase = LocalPhase.REWARD
        self.ans: dict[str, bool | None] = {"answer": None, "finished": False}

    def check_levelup(self) -> bool:
        """レベルアップチェックとレベルアップ処理"""
        result = False
        for member in di.ref.pt.get_allmember():
            if member.check_levelup() > 0:
                member.param.level += 1
                self.ctx.actor = member
                di.ref.cmdmgr.push_command(en_cmd.CharacterLevelup(self.ctx, self.message_window))
                self.wndmgr.push_stack(MenuLevelup, member, self.target_param)
                result = True
                break
        return result

    def update(self):
        match self.phase:
            case LocalPhase.REWARD:
                if di.ref.cmdmgr.is_empty:
                    self.phase = LocalPhase.CHECK_LEVELUP
                else:
                    return
            case LocalPhase.CHECK_LEVELUP:
                if di.ref.cmdmgr.is_empty:
                    if self.wndmgr.has_stack or self.check_levelup():
                        self.wndmgr.update()
                        if self.target_param:
                            self.ctx.actor.gain_parameter(self.target_param[0])
                            di.ref.cmdmgr.push_command(
                                en_cmd.CharacterGainHPMP(self.ctx, self.message_window)
                            )
                            self.target_param.clear()
                    else:
                        self.phase = LocalPhase.CHOOSE_DESTINATION
                return
            case LocalPhase.CHOOSE_DESTINATION:
                if self.wndmgr.has_stack:
                    self.wndmgr.update()
                    if self.ans["answer"]:
                        di.ref.scnmgr.previous_scene(step=2)
                    elif self.ans["answer"] is False:
                        di.ref.pt.set_current_point(di.ref.pt._current_point.id)
                        di.ref.pt._pt_is_moving = False
                        di.ref.pt.set_current_route()
                        di.ref.pt._field_sprite._is_moving = False
                        di.ref.sndmgr.play_se_sustain(SoundID.ENTERING)
                        while di.ref.sndmgr.wait_se_fin() is False:
                            pass
                        di.ref.scnmgr.change_scene("map")
                else:
                    self.wndmgr.push_stack(
                        MenuYesNo,
                        self.ans,
                        [
                            "このまま先に進みますか？",
                            "（拒否の場合は、移動前の場所へ引き返します）",
                        ],
                    )

    def draw(self):
        px.blt(0, 0, self.bgimage, 0, 0, self.bgimage.width, self.bgimage.height)
        if di.ref.cmdmgr.is_empty:
            self.wndmgr.draw()
