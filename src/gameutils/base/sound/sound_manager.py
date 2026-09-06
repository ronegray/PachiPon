"""
サウンド機能関連
"""
import pyxel as px

# import json
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable
from .. import check_file, read_json, read_string
from ...libconfig import ResourcePath

# ===================== 定数 =====================
NUM_CHANNELS = 8
BGM_CHANNELS = tuple(range(6))  # 0-5: BGM用
SE_INSTANT_CH = 6  # 瞬間SE用（上書き方式・固定ch）
SE_SUSTAIN_CH = 7  # 持続SE用（上書き方式・固定ch）

# # BGM用に予約するpyxel資源スロット（常に「現在再生中の曲」専用として使い回す）
# BGM_SOUND_SLOTS = tuple(range(len(BGM_CHANNELS)))  # sounds[0]〜sounds[5]
# BGM_MUSIC_SLOT = 0                                  # musics[0]を「現在のBGM」専用に固定使用

TARGET_TOTAL_GAIN = 0.98  # 全ch同時最大振幅時の合計上限（1.0未満に収める）

# VOLUME_LEVEL_FACTORS = (1.0, 0.5, 0.25, 0.125, 0.0625, 0.0)  # -6dBずつ + ミュート


def compute_base_gain(num_channels: int, target_total: float = TARGET_TOTAL_GAIN) -> float:
    """全ch同時最大振幅・完全同位相でも合計が target_total を超えないための channel.gain 基準値"""
    return target_total / num_channels


# ===================== BGM出力倍率のステートマシン =====================
class FadeState(Enum):
    NONE = auto()
    FADE_IN = auto()
    FADE_OUT = auto()


@dataclass
class FadeController:
    """複数チャンネルへ一括適用するBGM出力倍率の状態。
    current_factorが常に「今実際に出ている出力倍率」を表し、
    フェード完了後もインスタンスは保持され続け、current_factorだけが値として残る。
    """

    state: FadeState = FadeState.NONE
    elapsed_frames: int = 0
    duration_frames: int = 0
    start_factor: float = 0.0
    target_factor: float = 0.0
    current_factor: float = 1.0
    on_complete: Callable | None = None

    def begin(
        self,
        target_factor: float,
        duration_frames: int,
        on_complete: Callable | None = None,
    ):
        """現在値(current_factor)を起点に新しいフェードを開始する"""
        self.state = (
            FadeState.FADE_IN if target_factor > self.current_factor else FadeState.FADE_OUT
        )
        self.start_factor = self.current_factor
        self.target_factor = target_factor
        self.duration_frames = max(duration_frames, 1)
        self.elapsed_frames = 0
        self.on_complete = on_complete

    def set_immediate(self, factor: float):
        """フェードなしで即座に値を確定させる"""
        self.state = FadeState.NONE
        self.current_factor = factor
        self.on_complete = None

    def step(self) -> float:
        """1フレーム進行させ、現在のfactorを返す"""
        if self.state == FadeState.NONE:
            return self.current_factor
        self.elapsed_frames += 1
        t = min(self.elapsed_frames / self.duration_frames, 1.0)
        self.current_factor = self.start_factor + (self.target_factor - self.start_factor) * t
        if t >= 1.0:
            callback = self.on_complete
            self.state = FadeState.NONE
            self.on_complete = None
            if callback:
                callback()
        return self.current_factor


# ===================== 楽曲データの保持（pyxel資源には非依存） =====================
class MusicScoreLibrary:
    """マスタ一覧(index→ファイルパス)と、各曲のトラックMMLテキストの読み込み・保持を担当。
    px.Sound/Musicの構築や再生には一切関与しない。
    """

    def __init__(self):
        self._score_list: dict[str, str] = {}  # score_name -> 曲データファイルパス
        # self._track_cache: dict[int, list[str]] = {}  # index -> list[各トラックのMMLテキスト]
        self._score_book: dict[str, list[str]] = {}  # score_name -> [ch別MML譜面]
        # self.load_scorelist()

    def load_scorelist(self) -> bool:  # , master_json_path: str):
        """譜面一覧を読み込み、譜面"""
        # with open(master_json_path, encoding="utf-8") as f:
        #     raw = json.load(f)
        # self._master = {int(k): v for k, v in raw.items()}
        path = check_file(ResourcePath.SCORE_LIST)
        if path is None:
            print("譜面ファイル一覧が見つからない為、BGMは再生されません")
            return False
        self._score_list = read_json(path)
        return True

    def load_score(self, score_name: str) -> bool:
        """譜面一覧から指定名の譜面ファイルパスを取得し譜面データをロード"""
        score_path = self._score_list.get(score_name, "dummy")
        path = check_file(score_path)
        if path is None:
            print("譜面ファイルが見つからない為、このシーンのBGMは再生されません")
            self._score_book[score_name] = []
            return False
        score = read_string(path)
        self._score_book[score_name] = score
        return True

    def preload_allscore(self) -> None:
        """全スコア一括ロード"""
        for score_name in self._score_list:
            self.load_score(score_name)

    # def get_tracks(self, index: int) -> list[str]:
    #     """指定indexの各トラックMMLテキストのリストを返す（未ロードなら遅延ロード）"""
    #     if index not in self._track_cache:
    #         self._load_tracks(index)
    #     return self._track_cache[index]

    def get_tracks(self, score_name: str) -> list[str]:
        """指定indexの各トラックMMLテキストのリストを返す（未ロードなら遅延ロード）"""
        if score_name not in self._score_book:
            self.load_score(score_name)
        return self._score_book[score_name]

    # def preload_all(self):
    #     """起動時などにまとめて全曲を読み込みたい場合に使用"""
    #     for index in self._score_list:
    #         self.get_tracks(index)

    # def _load_tracks(self, index: int):
    #     file_path = self._score_list.get(index)
    #     if file_path is None:
    #         raise KeyError(f"music index {index} が master に見つかりません")
    #     # 曲データファイルは {"tracks": ["<MMLテキスト0>", "<MMLテキスト1>", ...]} を想定
    #     # （実際のフォーマットに合わせて調整してください）
    #     with open(file_path, encoding="utf-8") as f:
    #         data = json.load(f)
    #     self._track_cache[index] = data["tracks"]


# ===================== SoundManager =====================
class SoundManager:
    _base_gain: float = TARGET_TOTAL_GAIN / NUM_CHANNELS

    def __init__(self):
        # --- 構造的セットアップ（config非依存） ---
        px.channels[:] = [px.Channel() for _ in range(NUM_CHANNELS)]
        self.sounds = [px.Sound() for _ in range(NUM_CHANNELS)]  # 各チャンネル用サウンドデータ

        self._gain_factor: float = 1.0
        # self._base_gain_value: float = computebase_gain(NUM_CHANNELS)
        self._ch_base_gain: dict[int, float] = {}
        # self._update_basegain_cache()
        # self._apply_base_gain_all()
        for ch in range(NUM_CHANNELS):
            self._update_basegain_cache(ch)
            self._apply_base_gain(ch)

        self._bgm_fade = FadeController()  # current_factor=1.0からスタート
        # self._current_music_index: int = -1 # 負を未設定としたint確定のパラメタとする
        self._lib_music_score = MusicScoreLibrary()

    # ---------- config反映 ----------
    def set_basegain_factor(self, factor_level: float = 0.7, seq_ch: tuple = BGM_CHANNELS):
        # if factor > 1.0:
        #     print(f"[SoundManager] gain_factor={factor} は1.0を超えています。1.0にクランプします。")
        #     factor = 1.0
        # self._gain_factor = factor
        # self._recalculate_base_gain()
        # self._apply_bgm_gain()
        # px.channels[SE_INSTANT_CH].gain = self._ch_base_gain[SE_INSTANT_CH]
        # px.channels[SE_SUSTAIN_CH].gain = self._ch_base_gain[SE_SUSTAIN_CH]
        """音量コンフィグ定義値factor_level(1.0~0.0)をベースに音量係数を設定"""
        if factor_level < 0.0 or factor_level > 1.0:
            print(
                f"範囲外のfactor_level({factor_level})が指定された為、デフォルト値0.7を設定します"
            )
            factor_level = 0.7
        factor = factor_level**2  # 小さい音量程変化幅が小さくなる

        self._gain_factor = factor
        # self._update_basegain_cache()
        # self._apply_base_gain_all()
        for ch in seq_ch:
            self._update_basegain_cache(ch)
            self._apply_base_gain(ch)

    def _update_basegain_cache(self, ch: int):
        """全チャンネルのデフォルト音量値キャッシュを更新"""
        gain = self._base_gain * self._gain_factor
        self._ch_base_gain[ch] = gain

    def _apply_base_gain(self, ch: int):
        """チャンネルの音量値をキャッシュから設定"""
        px.channels[ch].gain = self._ch_base_gain.get(ch, self._base_gain / 10)

    # def _update_basegain_cache(self):
    #     """全チャンネルのデフォルト音量値キャッシュを更新"""
    #     gain = self._base_gain * self._gain_factor
    #     self._ch_base_gain = {ch: gain for ch in range(NUM_CHANNELS)}

    # def _apply_base_gain_all(self):
    #     # for ch, gain in self._ch_base_gain.items():
    #     #     px.channels[ch].gain = gain
    #     """全チャンネルの音量値をキャッシュから設定
    #     チャンネル側を軸として定義をおこなう"""
    #     # for ch, gain in self._ch_base_gain.items():
    #     #     px.channels[ch].gain = gain
    #     for i, ch in enumerate(px.channels):
    #         ch.gain = self._ch_base_gain.get(i, self._base_gain / 10)

    # ---------- リソースロード ----------
    # def load_assets(self, resource_path: str):
    #     """.pyxres等、画像・SE定義を含むリソースファイルの読み込み"""
    #     px.load(resource_path)

    # def load_music_master(self, master_json_path: str):
    #     """楽曲マスタ一覧(index→ファイルパス)の読み込み"""
    #     # self._lib_music_score.load_scorelist(master_json_path)
    def load_music_master(self) -> None:
        self._lib_music_score.load_scorelist()

    def preload_all_music(self):
        self._lib_music_score.preload_allscore()

    # ---------- BGM変更要求（外部のシーン管理から呼ばれる想定） ----------
    def request_bgm(self, score_name: str, fade_in_frames: int = 0):
        """曲indexを指定してBGMを切り替える。fade_in_framesを指定すればフェードイン再生になる。
        シーンとの対応関係はこのメソッドを呼ぶ側（外部）が解決してから index を渡すこと。
        """
        tracks = self._lib_music_score.get_tracks(score_name)
        self._build_bgm(tracks)
        # self._current_music_index = index

        def playbgm(factor: float):
            self._bgm_fade.set_immediate(factor)
            self._apply_bgm_gain()
            for ch_no in BGM_CHANNELS:
                px.channels[ch_no].play(self.sounds[ch_no], loop=True)

        if fade_in_frames > 0:
            # self._bgm_fade.set_immediate(0.0)
            # self._apply_bgm_gain()
            # # px.playm(BGM_MUSIC_SLOT, loop=True)
            playbgm(0.0)
            self._bgm_fade.begin(target_factor=1.0, duration_frames=fade_in_frames)
        else:
            # self._bgm_fade.set_immediate(1.0)
            # self._apply_bgm_gain()
            # # px.playm(BGM_MUSIC_SLOT, loop=True)
            playbgm(1.0)

    # def _build_bgm_resources(self, tracks: list[str]):
    #     # """トラックMMLテキストを、予約済みのpyxel Sound/Musicスロットへ書き込む"""
    #     # px.stop(*BGM_CHANNELS)
    #     # seqs = []
    #     # for i, _ch in enumerate(BGM_CHANNELS):
    #     #     sound_slot = BGM_SOUND_SLOTS[i]
    #     #     if i < len(tracks):
    #     #         px.sounds[sound_slot].mml(tracks[i])
    #     #         seqs.append([sound_slot])
    #     #     else:
    #     #         seqs.append([])  # このトラックは使用しない
    #     # px.musics[BGM_MUSIC_SLOT].set(*seqs)
    def _build_bgm(self, tracks: list[str]):
        """楽曲を構成するMMLトラックデータを再生用独自Soundオブジェクトに割り付け"""
        for i, ch_idx in enumerate(BGM_CHANNELS):
            mml = "R1"
            if i < len(tracks):
                mml = tracks[i]
            self.sounds[ch_idx].mml(mml)

    # ---------- BGM停止 ----------
    def stop_music(self):
        # # px.stop(*BGM_CHANNELS) #<-複数チャンネルの停止はエラーになる
        # px.stop()
        for ch in BGM_CHANNELS:
            px.channels[ch].stop()
        self._bgm_fade.set_immediate(1.0)  # 次回再生に備えて基準へ戻す
        # self._current_music_index = None

    def stop_music_fadeout(self, fade_frames: int, on_complete: Callable | None = None):
        if self._bgm_fade.state != FadeState.NONE:
            return  # フェード中の重複要求は無視
        self._bgm_fade.begin(
            target_factor=0.0, duration_frames=fade_frames, on_complete=on_complete
        )

    # ---------- 効果音（固定ch・上書き方式） ----------
    def play_se_instant(self, sound_id: int | px.Sound):
        px.channels[SE_INSTANT_CH].gain = self._ch_base_gain[SE_INSTANT_CH]
        px.play(SE_INSTANT_CH, sound_id)

    def play_se_sustain(self, sound_id: int | px.Sound):
        px.channels[SE_SUSTAIN_CH].gain = self._ch_base_gain[SE_SUSTAIN_CH]
        px.play(SE_SUSTAIN_CH, sound_id)

    def wait_se_fin(self) -> bool:
        """SEの鳴り終わりを検出"""
        return px.play_pos(SE_SUSTAIN_CH) is None

    # def stop_se_instant(self):
    #     px.stop(SE_INSTANT_CH)

    # def stop_se_sustain(self):
    #     px.stop(SE_SUSTAIN_CH)

    def stop_all(self):
        px.stop()
        self._bgm_fade.set_immediate(1.0)

    """# ---------- 毎フレーム呼ぶ進行処理 ----------
    というコメントが付いているが実際はフェード中のみ呼び出し"""

    def _apply_bgm_gain(self):
        """フェード中の音量変化を各チャンネルに反映"""
        for ch in BGM_CHANNELS:
            px.channels[ch].gain = self._ch_base_gain[ch] * self._bgm_fade.current_factor

    def update(self):
        """フェード中のみ音量変化についての状態更新を実行"""
        if self._bgm_fade.state is not FadeState.NONE:
            self._bgm_fade.step()
            self._apply_bgm_gain()
