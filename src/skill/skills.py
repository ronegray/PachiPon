"""
スキル管理モジュール

キャラクタエンティティ毎に保持する、
所持スキルのリストおよびデータ取得
"""

import logging
from dataclasses import dataclass
import service_locater as di
# from item import ItemState

# import command.entity_command
from . import SkillID, SkillDef


# ロギング設定
logger = logging.getLogger(__name__)


@dataclass
class Skills:
    """スキル管理クラス（Chacacter/Enemyのコンポーネント）"""

    def __init__(self, owner_id: int):
        self.owner: int = owner_id
        self._learned_skills: set[SkillID] = set()

    def learn_skill(self, skill_id: SkillID):
        """指定したスキルを習得済リストに追加"""
        if skill_id not in SkillID:
            errmsg = f"スキルIDが定義されていません：ID={skill_id}"
            logger.critical(errmsg, exc_info=True)
            raise ValueError(errmsg)
        self._learned_skills.add(skill_id)

    def get_skills(self, skill_id: SkillID) -> SkillDef | None:
        """指定したIDのスキル情報を取得"""
        if skill_id not in self._learned_skills:
            errmsg = f"未習得のスキルIDが指定されました：ID={skill_id}"
            logger.warning(errmsg)
            return None
        return di.ref.sklmgr.get_def(skill_id)

    def get_learned_skills(self) -> set[SkillID]:
        """習得済スキルのIDセット情報を取得"""
        return self._learned_skills

    # def use_skill(self, skill_id: SkillID):
    #     """指定したIDのスキルコマンドを生成してコマンドマネージャへ登録"""
    #     from entity import EntityContext
    #     import command.entity_command
    #     # スキル情報の取得
    #     skill_info = self.get_skills(skill_id)
    #     if skill_info is None:
    #         errmsg = f"スキル情報が取得出来ません：ID={skill_id}"
    #         logger.critical(errmsg, exc_info=True)
    #         raise ValueError(errmsg)
    #     # スキルコマンドの生成
    #     skill_command = getattr(command.entity_command, skill_info.effect_func, None)
    #     if skill_command is None:
    #         errmsg = f"スキル情報が取得出来ません：ID={skill_id}"
    #         logger.critical(errmsg, exc_info=True)
    #         raise ValueError(errmsg)
    #     # コマンドコンテキストの生成
    #     # situation = di.ref.pt.get_situation()
    #     actor = di.ref.pt.get_member(self.owner)
    #     allies = di.ref.pt.get_allmember()
    #     ctx = EntityContext(situation, actor, allies, [])

    #     command_obj = skill_command(ctx,)
