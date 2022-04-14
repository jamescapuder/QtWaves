import sys
import numpy as np
from scipy import signal
from dataclasses import dataclass
import pathlib


@dataclass
class WaveInfo:
    shape: str
    duration: int
    freq: float
    amplitude: float
    
    def gen_wave(self, rate):
        waveGens = {'sine': genSine, 'sawtooth': genSawtooth, 'square':  genSquare, 'triangle':  genTriangle}
        t = np.linspace(0, self.duration, self.duration*rate, endpoint=False)
        return np.multiply(waveGens[self.shape](self.freq, t), self.amplitude)
    
    def get_kv_dict(self):
        return {'shape': self.shape, 'duration': self.duration, 'freq': self.freq, 'amplitude': self.amplitude}

def genSine(freq, t):
    return np.sin(2*np.pi*freq*t)


def genTriangle(freq, t):
    return signal.sawtooth(2 * np.pi * freq * t, 0.5)


def genSawtooth(freq, t):
    return signal.sawtooth(2 * np.pi * freq * t)


def genSquare(freq, t):
    return signal.square(2 * np.pi * freq * t)

def get_fft(sampFreq, sound):
    sound = sound / 2.0**31
    length_in_s = sound.shape[0] / sampFreq
    time = np.arange(sound.shape[0]) / sound.shape[0] * length_in_s
    signal = sound[:]
    fft_spectrum = np.fft.rfft(signal)
    freq = np.fft.rfftfreq(signal.size, d=1./sampFreq)
    fft_spectrum_abs = np.abs(fft_spectrum)
    return freq, fft_spectrum_abs

def get_datadir() -> pathlib.Path:

    """
    Returns a parent directory path
    where persistent application data can be stored.

    # linux: ~/.local/share
    # macOS: ~/Library/Application Support
    # windows: C:/Users/<USER>/AppData/Roaming
    """

    home = pathlib.Path.home()

    if sys.platform == "win32":
        return home / "AppData/Roaming/WavePlayground"
    elif sys.platform == "linux":
        return home / ".local/share/WavePlayground"
    elif sys.platform == "darwin":
        return home / "Library/Application Support/WavePlayground"