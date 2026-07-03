"""
シーンモジュール：バトル

- 移動中のルート脅威度に該当するエネミーの生成
- バトルコマンドの生成とユーザコマンド入力
- 算出イニシアチブ値の順にコマンドを実行し、結果を表示
"""
import logging
import pyxel as px
from gameutils.base import check_file, read_string
from gameutils.lib import Window
from const import ENEMY_ID_BASE
import service_locater as di
from helper import diceroll
from field_map import Route
from entity import Enemy, EntityParam, EnemyParam, BaseSprite, ActionPattern, Character
from . import BaseScene
import command.entity_command as e_cmd
from entity import EntityBase, EntityContext
from menu import MenuBattle

# ロギング設定
logger = logging.getLogger(__name__)


class SceneBattle(BaseScene):
    """バトルシーン"""

    _disp_addr_center: int = 128  # エネミースプライト配置のセンター位置
    _sprite_under: int = 160
    _status_width: int = 80
    _status_height: int = 48
    _enemy_name_suffix: list = ["Ａ", "Ｂ", "Ｃ", "Ｄ", "Ｅ", "Ｆ"]
    _enemy_commands: dict[ActionPattern, type[e_cmd.CommandBaseEntity]] = {
        ActionPattern.ATTACK: e_cmd.Attack,
        ActionPattern.ESCAPE: e_cmd.EnemyEscape,
        ActionPattern.SKILL: e_cmd.UseSkill,
        ActionPattern.SPECIAL: e_cmd.EnemySpecial,
        ActionPattern.DEFEND: e_cmd.DefenceMode,
    }

    def __init__(self):
        super().__init__()
        self.situation = "battle"
        self.initiative_dict = {}  # イニシアチブ値格納辞書
        self.battle_commands = {}  # 行動コマンド格納辞書
        self.is_battle_over: bool = False  # 戦闘終了フラグ
        # 背景用に直前画面のスクリーンポインタからイメージ生成
        self.bgimage: px.Image = px.Image(px.width, px.height)
        bgpointer = self.bgimage.data_ptr()
        bgpointer[:] = px.screen.data_ptr()
        # 戦闘メッセージウインドウの生成
        message_pos = (0, 192)
        message_size = (px.width, 64)
        self.message_window = Window("basic", *message_pos, *message_size, "once")
        self.message_window.update_row_max(self.message_window._max_msg_rows + 1)
        # 移動中ルート情報から脅威度を取得
        route: Route = di.ref.pt.get_current_route()
        threat = route.threat
        # 出現エネミーの決定
        candidate_list = di.ref.enmmgr.get_threat_enemies(threat)
        enemy_index = px.rndi(0, len(candidate_list) - 1)
        enemy_data = candidate_list[enemy_index]
        enemy_image = px.Image.from_image(f"assets/image/{enemy_data["name"]}.bmp")
        # エネミー出現数の算出
        enemy_count = min(enemy_data["bodysize"], diceroll(1))
        # エネミーインスタンスの生成
        sprite_offset = enemy_image.width // 8
        sprite_x = SceneBattle._disp_addr_center - (
            (enemy_image.width * enemy_count + sprite_offset * (enemy_count - 1)) // 2
        )

        self.enemy_list: list[Enemy] = []
        for i in range(enemy_count):
            # ベースパラメータ
            base_param = EntityParam(
                name=enemy_data["name"] + SceneBattle._enemy_name_suffix[i],
                strength=enemy_data["strength"],
                arcane=enemy_data["arcane"],
                endurance=enemy_data["endurance"],
                speed=enemy_data["speed"],
                luck=enemy_data["luck"],
                max_hp=diceroll(enemy_data["threat"] + enemy_data["level"]),
                max_mp=diceroll(enemy_data["threat"] + enemy_data["level"]),
                exp=enemy_data["exp"],
            )
            enemy_param = EnemyParam(
                threat=enemy_data["threat"],
                gold=diceroll(enemy_data["gold"]),
                hitdice=enemy_data["hitdice"],
                defvalue=enemy_data["defvalue"],
                magpenalty=enemy_data["magpenalty"],
                guardtype=enemy_data["guardtype"],
                weaktype=enemy_data["weaktype"],
                action_pattern=enemy_data["action_pattern"],
            )
            # スプライト
            enemy_sprite = BaseSprite(
                sprite_x,
                SceneBattle._sprite_under - enemy_image.height,
                enemy_image,
                0,
                0,
                enemy_image.width,
                enemy_image.height,
                px.COLOR_GREEN,
            )
            # 次のスプライト描画位置を更新
            sprite_x += enemy_image.width + sprite_offset
            # インスタンスをリストに追加
            self.enemy_list.append(
                Enemy(base_param, enemy_param, enemy_sprite, i + ENEMY_ID_BASE)
            )

        # メンバーステータスウインドウの生成
        status_offset = Window._chip_size // 2
        pt_mems = di.ref.pt.get_member_count()
        status_x = SceneBattle._disp_addr_center - (
            (SceneBattle._status_width * pt_mems + status_offset * (pt_mems - 1)) // 2
        )
        self.status_windows: list[Window] = []
        for i in range(0, pt_mems):
            self.status_windows.append(
                Window(
                    "basic",
                    status_x,
                    0,
                    SceneBattle._status_width,
                    SceneBattle._status_height,
                    "once",
                )
            )
            status_x += SceneBattle._status_width + status_offset

        """暫定処理：BGMロード"""
        path = check_file("assets/sound/battle.txt")
        if path is not None:
            score_data = read_string(path)
        else:
            raise FileNotFoundError("ファイルがない！")
        for i, mml in enumerate(score_data):
            px.sounds[i].mml(mml)
        px.musics[0].set([0], [1], [2], [3])
        px.stop()
        px.playm(0, loop=True)

    def select_enemy_target(self) -> tuple[int, list[Character]]:
        """エネミーエンティティの敵対ターゲット決定"""
        target_list = di.ref.pt.get_active_member()
        target_index = px.rndi(0, len(target_list) - 1)
        # return [target_list[target_index]]
        return target_index, target_list

    def calc_initiative(self):
        """全員のイニシアチブ値を算出してリスト化"""
        self.initiative_dict = {}
        all_member = di.ref.pt.get_allmember() + self.enemy_list
        for member in all_member:
            if member.is_alive:
                initiative = diceroll(2) + member.bonus_spd
                self.initiative_dict[member.id] = initiative

    def generate_enemy_commands(self):
        """エネミーのコマンドオブジェクト生成"""
        for enemy in self.enemy_list:
            if enemy.is_alive:
                action_index = diceroll(1) - 1
                action = enemy.eparam.action_pattern[action_index]
                # match action:
                #     case ActionPattern.ATTACK:
                #         target_index, target_list = self.select_enemy_target()
                #         ctx = self.build_context(enemy, target_index, self.enemy_list, target_list)
                #         # cmd = e_cmd.EnemyAttack(ctx, self.message_window)
                #         cmd = e_cmd.Attack(ctx, self.message_window)
                #     case ActionPattern.ESCAPE:
                #         target_index, target_list = self.select_enemy_target()
                #         ctx = self.build_context(enemy, target_index, self.enemy_list, target_list)
                #         cmd = e_cmd.EnemyEscape(ctx, self.message_window)
                #     case ActionPattern.SKILL:
                #         target_index, target_list = self.select_enemy_target()
                #         ctx = self.build_context(enemy, target_index, self.enemy_list, target_list)
                #         cmd = e_cmd.UseSkill(ctx, self.message_window)
                #     case ActionPattern.SPECIAL:

                #         target_index, target_list = self.select_enemy_target()
                #         ctx = self.build_context(enemy, target_index, self.enemy_list, target_list)
                #         cmd = e_cmd.EnemySpecial(ctx, self.message_window)
                #     case ActionPattern.DEFEND:
                #         target_index, target_list = self.select_enemy_target()
                #         ctx = self.build_context(enemy, target_index, self.enemy_list, target_list)
                #         cmd = e_cmd.DefenceMode(ctx, self.message_window)
                #     case _:
                #         return
                # self.battle_commands[enemy.id] = enemy_command
                target_index, target_list = self.select_enemy_target()
                ctx = self.build_context(
                    enemy, target_index, self.enemy_list, target_list
                )
                # action = ActionPattern.ATTACK
                enemy_command = SceneBattle._enemy_commands.get(action)
                if enemy_command is None:
                    raise NameError
                self.battle_commands[enemy.id] = enemy_command(ctx, self.message_window)

    # def grant_rewards(self) -> None:
    # """戦闘報酬の獲得"""
    # # お金
    # reward_gold = sum([enemy.eparam.gold for enemy in self.enemy_list])
    # di.ref.pt.earn_gold(reward_gold)
    # # 経験値はメンバー人数割りで死亡者も全員獲得
    # reward_exp = sum([enemy.param.exp for enemy in self.enemy_list])
    # num = di.ref.pt.get_member_count()
    # for member in di.ref.pt.get_allmember():
    #     member.param.exp += px.ceil(reward_exp / num)
    # if di.ref.cmdmgr.is_empty:
    #     # 報酬の画面表示
    #     ctx = self.build_context(di.ref.hero, 0, di.ref.pt.get_allmember(),
    #                              self.enemy_list)
    #     di.ref.cmdmgr.push_command(e_cmd.GrantReward(ctx, self.message_window, di.ref.pt))
    # else:
    #     return None
    #     di.ref.scnmgr.previous_scene()

    def update(self):
        # if is_pressed("decide"):
        #     """暫定処理：BGMロード"""
        #     path = check_file("assets/sound/field.txt")
        #     if path is not None:
        #         score_data = read_string(path)
        #     else:
        #         raise FileNotFoundError("ファイルがない！")
        #     for i, mml in enumerate(score_data):
        #         px.sounds[i].mml(mml)
        #         px.musics[0].set([0], [1], [2], [3])
        #         px.stop()
        #         px.playm(0, loop=True)
        #     di.ref.scnmgr.previous_scene()

        if self.is_battle_over:
            # 戦闘終了処理
            # self.grant_rewards()
            if di.ref.cmdmgr.is_empty:
                # 報酬の画面表示
                ctx = self.build_context(
                    di.ref.hero, 0, di.ref.pt.get_allmember(), self.enemy_list
                )
                di.ref.cmdmgr.push_command(
                    e_cmd.GrantReward(ctx, self.message_window, di.ref.pt)
                )
                # 【コールバック登録ルール】
                # set_on_empty()は「次にスタックが空になった時」に一度だけ発火する。
                # GrantRewardをpushする直前に登録することで
                # 「報酬コマンド完了→シーン遷移」の順序を保証する。
                # 通常ターン終了時（コマンドスタック空→次ターン入力）では
                # 戦闘終了フラグが立っていない為この分岐に入らず、
                # set_on_empty()も呼ばれない。
                di.ref.cmdmgr.set_on_empty(di.ref.scnmgr.previous_scene)
            return None

        # 生存エネミーが0匹になったら戦闘終了して前のシーンに戻る
        if len([1 for enemy in self.enemy_list if enemy.is_alive]) == 0:
            # 戦闘終了フラグON
            self.is_battle_over = True
            return None

        # パーティメンバーの死亡を考慮し先頭キャラ再チェック
        di.ref.pt.update_top_index()

        # コマンドスタックが存在する場合はシーンを抜けてコマンド処理へ
        if di.ref.cmdmgr.is_empty:
            # if self.wndmgr.has_stack:
            #     self.wndmgr.update()
            # elif self.wndmgr.stack_count < di.ref.pt.get_active_member_count():
            #     # ユーザ行動コマンド入力用のメニューを生成し、メニュースタックに追加
            #     member_list = di.ref.pt.get_active_member()
            #     member = member_list[self.wndmgr.stack_count]
            #     member.defend(False) # コマンド入力時は一旦防御体勢解除
            #     self.wndmgr.push_stack(MenuBattle, self.build_context,
            #                            member.id, self.battle_commands,
            #                            self.message_window)
            # elif self.wndmgr.stack_count == di.ref.pt.get_active_member_count():
            #     # イニシアチブ値の大きいコマンドがスタック上位に来るようpush
            #     initive_list = [k for k, _ in sorted(self.initiative_dict.items(),
            #                                          key=lambda item: item[1])]
            #     for member_id in initive_list:
            #         di.ref.cmdmgr.push_command(self.battle_commands[member_id])
            # else:
            #     # バトル初期処理群
            #     self.calc_initiative()
            #     self.generate_enemy_commands()

            # コマンドリストにアクティブメンバー数のコマンドが揃うまでループ
            if len(self.battle_commands.keys()) < di.ref.pt.get_active_member_count():
                if self.wndmgr.has_stack:
                    self.wndmgr.update()
                else:  # メニュー未生成の場合は作成する
                    # 逆順メンバーリストを生成
                    member_list = di.ref.pt.get_active_member()
                    # logger.info(f"order member list {member_list}",)
                    member_list.reverse()
                    ctx = self.build_context(
                        member_list[0], 0, di.ref.pt.get_allmember(), self.enemy_list
                    )
                    # logger.info(f"source context {ctx}")
                    self.wndmgr.push_stack(
                        MenuBattle,
                        ctx,
                        member_list,
                        self.battle_commands,
                        self.message_window,
                    )
            else:
                # エネミー行動コマンドの生成
                self.generate_enemy_commands()
                # イニシアチブ値の計算
                self.calc_initiative()
                # イニシアチブ値の大きいコマンドがスタック上位に来るようpush
                initive_list = [
                    k
                    for k, _ in sorted(
                        self.initiative_dict.items(), key=lambda item: item[1]
                    )
                ]
                for member_id in initive_list:
                    di.ref.cmdmgr.push_command(self.battle_commands[member_id])
                self.battle_commands.clear()
        else:
            return None
        # # # メニューキー判定
        # # if is_pressed("other1"):
        # #     if self.wndmgr.has_stack:
        # #         self.wndmgr.pop_stack()
        # #     else:
        # #         self.wndmgr.push_stack(MenuField)
        # #     return

        # # WindowManagerにスタックがある場合はメニュー操作を優先
        # if self.wndmgr.has_stack:
        #     self.wndmgr.update()
        #     return

        # # 移動中は何もしない
        # # if self.field_chara.is_moving:
        # # self.field_chara.set_event_point_status(False)
        # # self.field_chara.update()
        # # return
        # if di.ref.pt._pt_is_moving:
        #     # di.ref.pt.set_event_point_status(False)
        #     di.ref.pt.update()
        #     # 移動中→移動完了への状態変化時に、前ポイントのイベント回復＆現在地修正
        #     if di.ref.pt._pt_is_moving is False:
        #         self.event_flags[self.current_node] = True
        #         self.last_visited_node = self.current_node = self.next_node
        #     return

        # # メニューキー判定
        # if is_pressed("other1"):
        #     if self.wndmgr.has_stack:
        #         self.wndmgr.pop_stack()
        #     else:
        #         self.wndmgr.push_stack(MenuField)
        #     return

        # # 通常のフィールド操作
        # # old_node = self.current_node

        # # ACTION_NAME 型に準拠させるための固定リスト
        # actions = ["up", "down", "left", "right"]
        # # for d in actions:
        # #     if is_pressed(d):  # type: ignore
        # #         next_node_id = di.ref.map.get_connected_node(self.current_node, d)
        # #         if next_node_id:
        # #             self.current_node = next_node_id
        # #             # プレイヤーの向きを設定
        # #             direction_map = {
        # #                 "up": "back",
        # #                 "down": "front",
        # #                 "left": "left",
        # #                 "right": "right",
        # #             }
        # #             # self.field_chara.set_direction(direction_map[d])
        # #             di.ref.pt.set_sprite_direction(direction_map[d])

        # #             # 移動開始
        # #             # target_point = di.ref.map.get_point(next_node)
        # #             # if target_point:
        # #             #     # self.field_chara.move_to(target_point.x, target_point.y)
        # #             #     di.ref.pt.move_to(target_point.id)
        # #             di.ref.pt.move_to(next_node_id)
        # #             # break
        # #             return
        # for d in actions:
        #     if is_pressed(d):  # type: ignore
        #         # next_node_id = di.ref.map.get_connected_node(self.current_node, d)
        #         to_route = di.ref.map.get_route(self.current_node, d)
        #         # if next_node_id:
        #         if to_route:
        #             # self.current_node = next_node_id
        #             self.next_node = to_route.to_id
        #             # プレイヤーの向きを設定
        #             direction_map = {
        #                 "up": "back",
        #                 "down": "front",
        #                 "left": "left",
        #                 "right": "right",
        #             }
        #             di.ref.pt.set_sprite_direction(direction_map[d])

        #             # 移動開始
        #             # di.ref.pt.move_to(next_node_id)
        #             # di.ref.pt.move_to(self.next_node)
        #             di.ref.pt.move_route(to_route)
        #             return

        # # if old_node != self.current_node:
        # #     self.event_flags[self.current_node] = True
        # #     self.last_visited_node = old_node

        # # # イベント発生判定
        # # is_event_point = self.event_flags.get(self.current_node, False)
        # # # self.field_chara.set_event_point_status(is_event_point)
        # # di.ref.pt.set_event_point_status(is_event_point)

        # # if is_pressed("decide") and is_event_point:
        # #     # self.event_manager.trigger_event(self.current_node, self.event_flags)
        # #     self.event_flags[self.current_node] = False

        # # # キャラクターのスプライトを更新（非移動時もアニメーション等のために必要）
        # # self.field_chara.update()

        # # カメラオフセットの計算 (プレイヤーを画面中央に固定)
        # # self.camera_x = px.width // 2 - self.field_chara.sprite.x
        # # self.camera_y = px.height // 2 - self.field_chara.sprite.y
        # self.camera_x = px.width // 2 - di.ref.pt._field_sprite.x
        # self.camera_y = px.height // 2 - di.ref.pt._field_sprite.y

        # # カメラのクランプ (ワールドマップの端が画面外に出ないように調整)
        # self.camera_x = max(px.width - di.ref.map.map_img_width, min(0, self.camera_x))
        # self.camera_y = max(
        #     px.height - di.ref.map.map_img_height, min(0, self.camera_y)
        # )

    def draw(self):
        """描画処理"""
        # di.ref.scnmgr._stacks[-2].draw()
        #
        # 背景描画
        px.dither(0.3)
        px.blt(0, 0, self.bgimage, 0, 0, self.bgimage.width, self.bgimage.height)
        # px.dither(0.5)
        # px.rect(0,0,px.width,px.height,px.COLOR_NAVY)
        px.dither(1)
        self.wndmgr.draw()
        for i, wnd in enumerate(self.status_windows):
            wnd.draw()
            barwidth = wnd.width - (Window._chip_size * 2)
            member = di.ref.pt.get_member(i)
            wnd.set_message([f"{member.param.name}"])
            state = [[text, px.COLOR_WHITE] for text in wnd.text_list]
            wnd.drawText(wnd.x + 6, wnd.y + 4, state)
            gauge_hp = member.param.hp / member.max_hp * barwidth
            px.rect(wnd.x + 8, wnd.y + 17, barwidth, 7, px.COLOR_RED)
            px.rect(wnd.x + 8, wnd.y + 17, gauge_hp, 7, px.COLOR_LIME)
            px.text(wnd.x + 10, wnd.y + 18, f"HP:{member.param.hp}", px.COLOR_BLACK)
            px.rectb(wnd.x + 8, wnd.y + 17, barwidth, 7, px.COLOR_WHITE)
            px.rectb(wnd.x + 7, wnd.y + 18, 1, 5, px.COLOR_WHITE)
            px.rectb(wnd.x + 6, wnd.y + 19, 1, 3, px.COLOR_WHITE)
            px.rectb(wnd.x + 7 + barwidth + 1, wnd.y + 18, 1, 5, px.COLOR_WHITE)
            px.rectb(wnd.x + 7 + barwidth + 2, wnd.y + 19, 1, 3, px.COLOR_WHITE)

            gauge_mp = member.param.mp / member.max_mp * barwidth
            px.rect(wnd.x + 8, wnd.y + 25, barwidth, 7, px.COLOR_RED)
            px.rect(wnd.x + 8, wnd.y + 25, gauge_mp, 7, px.COLOR_DARK_BLUE)
            px.text(wnd.x + 10, wnd.y + 26, f"MP:{member.param.mp}", px.COLOR_BLACK)
            px.rectb(wnd.x + 8, wnd.y + 25, barwidth, 7, px.COLOR_WHITE)
            px.rectb(wnd.x + 7, wnd.y + 26, 1, 5, px.COLOR_WHITE)
            px.rectb(wnd.x + 6, wnd.y + 27, 1, 3, px.COLOR_WHITE)
            px.rectb(wnd.x + 7 + barwidth + 1, wnd.y + 26, 1, 5, px.COLOR_WHITE)
            px.rectb(wnd.x + 7 + barwidth + 2, wnd.y + 27, 1, 3, px.COLOR_WHITE)

            px.rect(wnd.x + 6, wnd.y + 35, 8, 8, px.COLOR_GREEN)

        for enemy in self.enemy_list:
            if enemy.is_alive:
                enemy.sprite.draw()

        # # プレイヤーキャラのワールド座標を取得
        # # # px_ = self.field_chara.sprite.x
        # # # py_ = self.field_chara.sprite.y
        # # px_ = di.ref.pt._field_sprite.x
        # # py_ = di.ref.pt._field_sprite.y
        # wx, wy = di.ref.pt.get_pt_world_address()

        # # カメラオフセットを計算 (プレイヤーが画面中央に来るように)
        # # ox = px.width // 2 - px_
        # # oy = px.height // 2 - py_
        # ox = px.width // 2 - wx
        # oy = px.height // 2 - wy

        # # # マップ背景の描画 (ワールド座標 (0,0) を ox, oy に描画)
        # # pyxel.blt(
        # #     ox, oy, di.ref.map.map_img, 0, 0,
        # #     di.ref.map.map_img_width, di.ref.map.map_img_height
        # # )

        # # マップ上のノードと線の描画 (オフセット適用)
        # di.ref.map.draw(ox, oy)

        # # # イベント発生可能フラグの表示 (デバッグ用)
        # # for node_id, point in di.ref.map.points.items():
        # #     if self.event_flags.get(node_id, False):
        # #         px.text(point.x + ox + 5, point.y + oy + 5, "E", 8)  # 黄色で表示

        # # プレイヤーキャラの描画 (常に画面中央)
        # # self.field_chara.draw(128 - 16, 128 - 16)
        # di.ref.pt.draw(px.width // 2, px.height // 2)

        # # WindowManagerの描画（メニュー等）
        # self.wndmgr.draw()

    def build_context(
        self,
        actor: EntityBase,
        target_index: int,
        ally_list: list = [],
        target_list: list = [],
    ) -> EntityContext:
        """エンティティコマンド用コンテキスト生成"""
        ctx = EntityContext(
            situation=self.situation,
            actor=actor,
            allies=ally_list,
            targets=target_list,
            target_index=target_index,
        )
        return ctx
