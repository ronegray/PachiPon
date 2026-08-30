"""
アイテム情報管理モジュール
- マスタ定義ファイルの情報を保持
- 指定したID(ItemDef)のアイテム情報を提供
"""

import logging
import pyxel as px
from gameutils.base import check_file
from assets.asset_map import AssetID, AssetMap
from item import WeaponType
from skill import SkillID

# ロギング設定
logger = logging.getLogger(__name__)


class EffectRepository:
    # _efx_weapon_def [type,(image_index, [duration,...])]
    _efx_weapon_def: dict[WeaponType, tuple[int, list[int]]]
    _image_weapon: px.Image  # = px.Image(0,0)
    _efx_skill_def: dict[SkillID, tuple[int, list[int]]]
    _image_skill: px.Image  # = px.Image(0,0)
    _efx_size: int = 16

    @property
    def efx_img_size(self) -> int:
        """エフェクトイメージサイズの外部公開用プロパティ"""
        return EffectRepository._efx_size

    def __init__(self) -> None:
        """エフェクト用画像ファイル読込およびタイプ別画像表示定義"""
        path_check = AssetMap.get_assetpath(AssetID.IMAGE_EFX_WEAPON)
        img_path = check_file(path_check)
        if img_path:
            EffectRepository._image_weapon = px.Image.from_image(path_check)
        else:
            errmsg = "武器エフェクト画像ファイルが見つかりません"
            logger.critical(errmsg, exc_info=True)
            raise FileNotFoundError(errmsg)

        path_check = AssetMap.get_assetpath(AssetID.IMAGE_EFX_SKILL)
        img_path = check_file(path_check)
        if img_path:
            EffectRepository._image_skill = px.Image.from_image(path_check)
        else:
            errmsg = "スキルエフェクト画像ファイルが見つかりません"
            logger.critical(errmsg, exc_info=True)
            raise FileNotFoundError(errmsg)

        EffectRepository._efx_weapon_def = {  #: dict[WeaponType, tuple[int, list[int]]]
            WeaponType.NONE: (0, [1, 3, 2, 5]),
            WeaponType.CHOP: (1, [1, 3, 2, 5]),
            WeaponType.BASH: (0, [1, 3, 2, 5]),
            WeaponType.STUB: (2, [1, 3, 2, 5]),
            WeaponType.FULL: (1, [1, 3, 2, 5]),
        }

        EffectRepository._efx_skill_def = {  #: dict[SkillID, tuple[int, list[int]]]
            SkillID.SACRED_ARROW: (0, [1, 1, 1, 1]),
            SkillID.SANCTUARY: (0, [1, 1, 1, 1]),
            SkillID.HOLY_SMITE: (0, [1, 1, 1, 1]),
            # 呪毒(curse)
            SkillID.CURSE_PAIN: (1, [1, 1, 1, 1]),
            SkillID.POISON_CLOUD: (1, [1, 1, 1, 1]),
            SkillID.STATUE_GAZE: (1, [1, 1, 1, 1]),
            # 火炎(fire)
            SkillID.FIRE_BOLT: (2, [1, 1, 1, 1]),
            SkillID.BURN_FLOOD: (2, [1, 1, 1, 1]),
            SkillID.INFERNO: (2, [1, 1, 1, 1]),
            # 氷結(ice)
            SkillID.ICE_NEEDLE: (3, [1, 1, 1, 1]),
            SkillID.FROST_CIRCLE: (3, [1, 1, 1, 1]),
            SkillID.BLIZZARD: (3, [1, 1, 1, 1]),
            # 雷電(bolt)
            SkillID.BOLT_SHOWER: (4, [1, 1, 1, 1]),
            SkillID.THUNDER_PILLER: (4, [1, 1, 1, 1]),
            SkillID.ELECTROMAGNETIC: (4, [1, 1, 1, 1]),
            # 精神(mind)
            SkillID.SLEEP_SONG: (5, [1, 1, 1, 1]),
            SkillID.DISTURB_MIND: (5, [1, 1, 1, 1]),
            SkillID.CHARM_ILLUSION: (5, [1, 1, 1, 1]),
            # 衝撃(shock)
            SkillID.SHOCK_BULLET: (6, [1, 1, 1, 1]),
            SkillID.SONIC_WAVE: (6, [1, 1, 1, 1]),
            SkillID.BLOW_AWAY: (6, [1, 1, 1, 1]),
            # 霊光(light)
            SkillID.HEALING_HAND: (7, [1, 1, 1, 1]),
            SkillID.CURE_POISON: (7, [1, 1, 1, 1]),
            SkillID.ANGEL_STAIR: (7, [1, 1, 1, 1]),
        }

    def get_efx(self, effect_id: WeaponType | SkillID) -> tuple[px.Image, list[int]]:
        """指定されたIDのエフェクト定義を取得する"""
        match effect_id:
            case WeaponType():
                efx_images: px.Image = EffectRepository._image_weapon
                efx_def = EffectRepository._efx_weapon_def[effect_id]
            case SkillID():
                efx_images: px.Image = EffectRepository._image_skill
                efx_def = EffectRepository._efx_skill_def[effect_id]
        efx_image: px.Image = px.Image(EffectRepository._efx_size * 4, EffectRepository._efx_size)
        efx_image.blt(
            0,
            0,
            efx_images,
            0,
            efx_def[0] * EffectRepository._efx_size,
            EffectRepository._efx_size * 4,
            EffectRepository._efx_size,
        )
        return (efx_image, efx_def[1])
