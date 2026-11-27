"""
サウンド機能関連
"""
import pyxel as px
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
TARGET_TOTAL_GAIN = 0.98  # 全ch同時最大振幅時の合計上限（1.0未満に収める）


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
        self.state = FadeState.FADE_IN if target_factor > self.current_factor else FadeState.FADE_OUT
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
        self._score_book: dict[str, list[str]] = {}  # score_name -> [ch別MML譜面]

    def load_scorelist(self) -> bool:
        """譜面一覧を読み込み、譜面"""
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

    def get_tracks(self, score_name: str) -> list[str]:
        """指定indexの各トラックMMLテキストのリストを返す（未ロードなら遅延ロード）"""
        if score_name not in self._score_book:
            self.load_score(score_name)
        return self._score_book[score_name]


# ===================== SoundManager =====================
class SoundManager:
    _base_gain: float = TARGET_TOTAL_GAIN / NUM_CHANNELS

    def __init__(self):
        # --- 構造的セットアップ（config非依存） ---
        px.channels[:] = [px.Channel() for _ in range(NUM_CHANNELS)]
        self.sounds = [px.Sound() for _ in range(NUM_CHANNELS)]  # 各チャンネル用サウンドデータ

        self._gain_factor: float = 1.0
        self._ch_base_gain: dict[int, float] = {}
        for ch in range(NUM_CHANNELS):
            self._update_basegain_cache(ch)
            self._apply_base_gain(ch)

        self._bgm_fade = FadeController()  # current_factor=1.0からスタート
        self._lib_music_score = MusicScoreLibrary()

    # ---------- config反映 ----------
    def set_basegain_factor(self, factor_level: float = 0.7, seq_ch: tuple = BGM_CHANNELS):
        """音量コンフィグ定義値factor_level(1.0~0.0)をベースに音量係数を設定"""
        if factor_level < 0.0 or factor_level > 1.0:
            print(f"範囲外のfactor_level({factor_level})が指定された為、デフォルト値0.7を設定します")
            factor_level = 0.7
        factor = factor_level**2  # 小さい音量程変化幅が小さくなる

        self._gain_factor = factor
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

    # ---------- リソースロード ----------
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

        def playbgm(factor: float):
            self._bgm_fade.set_immediate(factor)
            self._apply_bgm_gain()
            for ch_no in BGM_CHANNELS:
                px.channels[ch_no].play(self.sounds[ch_no], loop=True)

        if fade_in_frames > 0:
            playbgm(0.0)
            self._bgm_fade.begin(target_factor=1.0, duration_frames=fade_in_frames)
        else:
            playbgm(1.0)

    def _build_bgm(self, tracks: list[str]):
        """楽曲を構成するMMLトラックデータを再生用独自Soundオブジェクトに割り付け"""
        for i, ch_idx in enumerate(BGM_CHANNELS):
            mml = "R1"
            if i < len(tracks):
                mml = tracks[i]
            self.sounds[ch_idx].mml(mml)

    # ---------- BGM停止 ----------
    def stop_music(self):
        for ch in BGM_CHANNELS:
            px.channels[ch].stop()
        self._bgm_fade.set_immediate(1.0)  # 次回再生に備えて基準へ戻す

    def stop_music_fadeout(self, fade_frames: int, on_complete: Callable | None = None):
        if self._bgm_fade.state != FadeState.NONE:
            return  # フェード中の重複要求は無視
        self._bgm_fade.begin(target_factor=0.0, duration_frames=fade_frames, on_complete=on_complete)

    def get_fade_state(self) -> bool:
        """フェード中判定"""
        return self._bgm_fade.state is not FadeState.NONE

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

    def stop_se_sustain(self):
        px.stop(SE_SUSTAIN_CH)

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
