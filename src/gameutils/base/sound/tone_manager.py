from dataclasses import dataclass, asdict
from enum import IntEnum
from .. import check_file, read_json, write_json
import pyxel as px


class ToneNameIndex(IntEnum):
    """トーン名に対応するトーン番号"""

    TRIANGLE = 0
    SQUARE = 1
    PULSE = 2
    NOISE = 3
    SIGN = 4
    SAW = 5
    PULSE2 = 6
    NOISE2 = 7
    CUSTOM1 = 8
    CUSTOM2 = 9
    CUSTOM3 = 10


#  0 for wavetable, 1 for short-period noise, 2 for long-period noise.
# トーンモード
MODE_WAVETABLE = 0
MODE_NOISE_SHORT = 1
MODE_NOISE_LONG = 2

# 系統別のgain値
GAIN_WAVES = 1.0
GAIN_ONOFF = 0.3
GAIN_NOISE = 0.6

# 系統別のsample_bits値
BITS_WAVES = 4
BITS_ONOFF = 1
BITS_NOISE = 0


@dataclass
class ToneParam:
    mode: int
    gain: float
    sample_bits: int
    wavetable: list[int]


class ToneManager:
    """toneオブジェクト用パラメタの管理と制御
    - 波形データの保持
    - pyxel.tonesの拡張
    -
    """

    _tone_params: dict[ToneNameIndex, ToneParam]

    def __init__(self):
        ToneManager._tone_params = {}
        # Pyxelデフォルトのtone設定を取得
        # ToneManager._tone_params[ToneName.TRIANGLE] = ToneParam(
        #     mode=WAVETABLE,
        #     gain=GAIN_WAVES,
        #     sample_bits=BITS_WAVES,
        #     wavetable=[8,9,10,11,12,13,14,15,15,14,13,12,11,10,9,8,7,6,5,4,3,2,1,0,0,1,2,3,4,5,6,7]
        # )
        # ToneManager._tone_params[ToneName.SQUARE] = ToneParam(
        #     mode=WAVETABLE,
        #     gain=GAIN_ONOFF,
        #     sample_bits=BITS_ONOFF,
        #     wavetable=[1,0]
        # )
        # ToneManager._tone_params[ToneName.PULSE] = ToneParam(
        #     mode=WAVETABLE,
        #     gain=GAIN_ONOFF,
        #     sample_bits=BITS_ONOFF,
        #     wavetable=[1,0,0,0]
        # )
        # ToneManager._tone_params[ToneName.NOISE] = ToneParam(
        #     mode=NOISE_LONG,
        #     gain=GAIN_NOISE,
        #     sample_bits=BITS_NOISE,
        #     wavetable=[]
        # )
        tone = px.tones[ToneNameIndex.TRIANGLE]
        ToneManager._tone_params[ToneNameIndex.TRIANGLE] = ToneParam(
            mode=tone.mode,
            gain=tone.gain,
            sample_bits=tone.sample_bits,
            wavetable=tone.wavetable[:],
        )
        tone = px.tones[ToneNameIndex.SQUARE]
        ToneManager._tone_params[ToneNameIndex.SQUARE] = ToneParam(
            mode=tone.mode,
            gain=tone.gain,
            sample_bits=tone.sample_bits,
            wavetable=tone.wavetable[:],
        )
        tone = px.tones[ToneNameIndex.PULSE]
        ToneManager._tone_params[ToneNameIndex.PULSE] = ToneParam(
            mode=tone.mode,
            gain=tone.gain,
            sample_bits=tone.sample_bits,
            wavetable=tone.wavetable[:],
        )
        tone = px.tones[ToneNameIndex.NOISE]
        ToneManager._tone_params[ToneNameIndex.NOISE] = ToneParam(
            mode=tone.mode,
            gain=tone.gain,
            sample_bits=tone.sample_bits,
            wavetable=tone.wavetable[:],
        )

        # オリジナルのtone設定パラメタ
        ToneManager._tone_params[ToneNameIndex.SIGN] = ToneParam(
            mode=MODE_WAVETABLE,
            gain=GAIN_WAVES,
            sample_bits=BITS_WAVES,
            wavetable=[
                8,
                9,
                10,
                12,
                13,
                14,
                14,
                15,
                15,
                15,
                14,
                14,
                13,
                12,
                10,
                9,
                8,
                6,
                5,
                3,
                2,
                1,
                1,
                0,
                0,
                0,
                1,
                1,
                2,
                3,
                5,
                6,
            ],
        )
        ToneManager._tone_params[ToneNameIndex.SAW] = ToneParam(
            mode=MODE_WAVETABLE,
            gain=GAIN_WAVES,
            sample_bits=BITS_WAVES,
            wavetable=[
                0,
                0,
                1,
                1,
                2,
                2,
                3,
                3,
                4,
                4,
                5,
                5,
                6,
                6,
                7,
                7,
                8,
                8,
                9,
                9,
                10,
                10,
                11,
                11,
                12,
                12,
                13,
                13,
                14,
                14,
                15,
                15,
            ],
        )
        ToneManager._tone_params[ToneNameIndex.PULSE2] = ToneParam(
            mode=MODE_WAVETABLE,
            gain=GAIN_ONOFF,
            sample_bits=BITS_ONOFF,
            wavetable=[1, 0, 0, 0, 0],
        )
        ToneManager._tone_params[ToneNameIndex.NOISE2] = ToneParam(
            mode=MODE_NOISE_SHORT, gain=GAIN_NOISE, sample_bits=BITS_NOISE, wavetable=[]
        )

        # pyxel.tonesの拡張とトーンパラメタの反映
        ch_max = 8
        self.reset_tone(ch_max)

    def reset_tone(self, ch_max: int = 4) -> None:
        """pyxel.tonesの拡張および初期トーンパラメタ設定"""
        px.tones[:] = [px.Tone() for _ in range(ch_max)]
        for i, tone in enumerate(px.tones):
            param = ToneManager._tone_params[ToneNameIndex(i)]
            tone.mode = param.mode
            tone.gain = param.gain
            tone.sample_bits = param.sample_bits
            tone.wavetable[:] = param.wavetable

    def edit_tone(
        self,
        tone_index: ToneNameIndex,
        mode: int,
        gain: float,
        sample_bits: int,
        wavetable: list[int],
    ) -> None:
        """カスタムパラメタtoneの定義追加/修正"""
        if tone_index < ToneNameIndex.TRIANGLE or tone_index > ToneNameIndex.CUSTOM3:
            raise IndexError("tone_indexの指定値が許容範囲外です")
        # wavetableのデータチェック
        max_vol = (1 << sample_bits) - 1
        for vol in wavetable:
            if vol > max_vol:
                raise ValueError(
                    "wavetableにsample_bitsの許容範囲を超えた値が指定されています"
                )
        # toneパラメタの反映（既存インデックス指定時はオブジェクト上書き）
        ToneManager._tone_params[tone_index] = ToneParam(
            mode=mode, gain=gain, sample_bits=sample_bits, wavetable=wavetable
        )

    def load_tone(self, filename: str, tone_index: ToneNameIndex):
        """jsonファイルの読み込み"""
        # with open(filename, "r", encoding = "UTF-8") as f:
        #     data = json.load(f)
        # return data
        path = check_file(filename)
        if path is None:
            raise FileNotFoundError(f"ファイルが見つかりません：{filename}")
        tone_param = read_json(path)
        target = ToneManager._tone_params.get(tone_index, ToneParam(0, 0, 0, [0]))
        target.mode = tone_param.get("mode", MODE_WAVETABLE)
        target.gain = tone_param.get("gain", GAIN_WAVES)
        target.sample_bits = tone_param.get("sample_bits", BITS_WAVES)
        target.wavetable = tone_param.get("wavetable", [1, 0])

    def save_tone(self, filename: str, tone_index: ToneNameIndex):
        """jsonファイルの書き込み"""
        path = check_file(filename, "w")
        if path is None:
            raise IOError(f"ファイル出力に失敗しました：{filename}")
        tone_data = ToneManager._tone_params[tone_index]
        write_json(path, asdict(tone_data))
