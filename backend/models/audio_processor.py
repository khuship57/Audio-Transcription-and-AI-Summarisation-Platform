import librosa
import scipy.signal
import numpy as np
import torch
import soundfile as sf
from datetime import timedelta
from typing import Tuple
from pydub import AudioSegment

class AudioProcessor:
    def __init__(self, target_sr: int = 16000):
        self.target_sr = target_sr
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def get_audio_duration(self, audio_path: str) -> float:
        """Get the duration of an audio file in seconds"""
        try:
            duration = librosa.get_duration(path=audio_path)
            return duration
        except Exception as e:
            print(f"Could not determine audio duration: {e}")
            return 0

    def format_duration(self, duration_seconds: float) -> str:
        """Format duration in seconds to HH:MM:SS format"""
        td = timedelta(seconds=int(duration_seconds))
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours > 0:
            return f"{hours} hour{'s' if hours > 1 else ''}, {minutes} minute{'s' if minutes > 1 else ''}"
        else:
            return f"{minutes} minute{'s' if minutes > 1 else ''}, {seconds} second{'s' if seconds > 1 else ''}"

    def convert_to_wav(self, input_file, output_path):
        """Convert audio file to WAV format"""
        try:
            audio = AudioSegment.from_file(input_file)
            audio.export(output_path, format="wav")
            return True, "Conversion successful"
        except Exception as e:
            return False, f"Conversion failed: {str(e)}"

    def load_audio(self, path: str) -> Tuple[np.ndarray, int]:
        """Load audio from a file."""
        try:
            audio, sr = librosa.load(path, sr=None)
        except Exception:
            audio, sr = sf.read(path)
            if len(audio.shape) > 1:
                audio = np.mean(audio, axis=1)
        return audio, sr

    def resample(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Resample audio to the target sample rate."""
        if sr != self.target_sr:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=self.target_sr)
        return audio

    def normalize(self, audio: np.ndarray, method: str = 'peak') -> np.ndarray:
        """Normalize audio signal."""
        if method == 'peak':
            peak = np.max(np.abs(audio))
            if peak > 0:
                audio = 0.95 * audio / peak
        elif method == 'rms':
            rms = np.sqrt(np.mean(audio**2))
            if rms > 0:
                audio = audio * (0.1 / rms)
        elif method == 'lufs':
            loudness = np.mean(np.abs(audio))
            if loudness > 0:
                audio = audio * (0.1 / loudness)
        return np.clip(audio, -1.0, 1.0)

    def highpass_filter(self, audio: np.ndarray, cutoff: float = 80.0) -> np.ndarray:
        """Apply high-pass filter to remove low-frequency noise."""
        nyquist = self.target_sr / 2
        b, a = scipy.signal.butter(4, cutoff / nyquist, btype='high')
        return scipy.signal.filtfilt(b, a, audio)

    def spectral_subtraction(self, audio: np.ndarray) -> np.ndarray:
        """Reduce noise via spectral subtraction."""
        stft = librosa.stft(audio, n_fft=2048, hop_length=512)
        mag, phase = np.abs(stft), np.angle(stft)
        noise_est = np.mean(mag[:, :min(10, mag.shape[1] // 4)], axis=1, keepdims=True)
        cleaned_mag = np.maximum(mag - 2.0 * noise_est, 0.1 * mag)
        enhanced = librosa.istft(cleaned_mag * np.exp(1j * phase), hop_length=512)
        return enhanced

    def preprocess_audio(self, audio: np.ndarray, sr: int, **kwargs) -> np.ndarray:
        """Apply full preprocessing pipeline to audio."""
        audio = self.resample(audio, sr)

        if kwargs.get('apply_highpass', True):
            audio = self.highpass_filter(audio)
        if kwargs.get('denoise_method') == 'spectral_subtraction':
            audio = self.spectral_subtraction(audio)

        audio = self.normalize(audio, method=kwargs.get('normalize_method', 'peak'))
        return audio
