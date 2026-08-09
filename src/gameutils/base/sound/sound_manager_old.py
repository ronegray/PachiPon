"""sound_manager.py
サウンド機能関連
依存：custom_tone.py

- pyxel基本channel・toneの拡張
- mml楽譜ファイルの読み込み（json形式、1ch=1要素）
"""

import pyxel as px
from . import custom_tone
from ...base import check_file, read_json, read_string
from ...libconfig import ResourcePath


class SoundManager:
    _music_list: dict[str, str] = {}  # 利用シーンID:曲名（＝ファイル名）
    _now_bgm: int = 0  # BGM再生するMusic番号（クロスフェードで入れ替わる）
    _range_se_ch: tuple[int, int] = (5, 7)  # SEで利用できるchの開始番号と終了番号
    _custom_tones: list[custom_tone.CustomTone] = []

    def __init__(self, channel_num: int = 8, tone_num: int = 24):
        # global _music_list, custom_tones
        # pyxel.channelsリストの再定義
        channel_list = []
        for _ in range(channel_num):
            channel = px.Channel()
            channel.gain = 0.95 / channel_num
            channel.detune = 0
            channel_list.append(channel)
        px.channels[0:channel_num] = channel_list

        # pyxel.tonesリストの再定義とカスタムトーン定義
        tone_list = []
        for i in range(tone_num):
            # カスタムトーン生成
            customtone = custom_tone.CustomTone()
            self._custom_tones.append(customtone)
            # カスタムトーン内のトーンオブジェクトを取得
            tone = customtone.get_parameter("tone")
            if i < len(px.tones):
                tone = px.tones[i]  # 標準トーン0～3は確保しておく
            tone_list.append(tone)
        px.tones[0:tone_num] = tone_list

        # 楽曲リストのロード {scene_id(int):filename(str)}
        # music_list = "musiclist.json"
        music_list = ResourcePath.SCORE_LIST
        path = check_file(music_list)
        if path is not None:
            self._music_list = read_json(path)

    def play_bgm(self, bgm_id: int) -> None:
        px.playm(bgm_id)

    def play_se(self, se_id: int) -> None:
        """指定されたIDのSEを、空きチャンネルを探して鳴らす"""
        for ch in self._range_se_ch:
            if px.channels[ch].play_pos() is None:
                px.play(ch, se_id)
                return

    def stop(self) -> None:
        """全ての再生音を一括停止"""
        px.stop()

    def load_bgm(self, bgm_id: int) -> None:
        """指定シーンIDのBGMをロードして再生"""
        # BGMIDから
        score_name = self._get_score_name(bgm_id)
        if score_name:
            self._load_score(score_name)

        # BGM範囲の音だけ停止
        for ch, _ in enumerate(px.channels):
            if ch < self._range_se_ch[0]:
                px.stop(ch)

        px.playm(self._now_bgm, loop=True)

    def fadeout(self):
        pass

    def fadein(self):
        pass

    def _get_score_name(self, scene_id: int) -> str | None:
        """シーンIDを元にミュージックリストからBGMファイル名を取得"""
        return self._music_list.get(str(scene_id))

    def _load_score(self, score_name: str):
        """MML楽譜ファイルの読み込み"""
        # global _now_bgm
        filepath = check_file(score_name)
        if not filepath:
            raise FileNotFoundError
        from pathlib import Path

        ext = Path(filepath).suffix.lower()
        if ext == ".json":
            score_data = read_json(filepath)
        else:
            score_data = read_string(filepath)

        for i, [mml, tonefile] in enumerate(score_data):
            px.sounds[i + (self._now_bgm * 8)].mml = mml
            if tonefile:
                self._custom_tones[i + 4].load_parameter(tonefile)
        self._build_music()

    def _build_music(self):
        """８チャンネル分のサウンドを対象にミュージックデータを生成"""
        # global _now_bgm
        trackset: list = [[i] for i in range(len(px.channels) + (self._now_bgm * 8))]
        px.musics[self._now_bgm].set(trackset)
        _now_bgm = abs(self._now_bgm - 1)
