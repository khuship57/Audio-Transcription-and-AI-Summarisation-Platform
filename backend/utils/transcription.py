import tempfile
import os
import torch
import whisper
import numpy as np
import librosa
import soundfile as sf
from pathlib import Path
from typing import Dict
import gc

def integrated_transcription_pipeline(audio_file_path: str,
                                    enable_diarization: bool = False,
                                    enable_speaker_recognition: bool = False,
                                    whisper_model: str = "small",
                                    min_speakers: int = 2,
                                    max_speakers: int = 8,
                                    voice_manager=None) -> Dict:
    """
    Integrated transcription pipeline for the meeting summary app
    """
    
    try:
        if enable_diarization:
            from ..models.speaker_diarization import transcribe_with_diarization
            result = transcribe_with_diarization(
                audio_file_path=audio_file_path,
                whisper_model=whisper_model,
                min_speakers=min_speakers,
                max_speakers=max_speakers,
                voice_manager=voice_manager if enable_speaker_recognition else None
            )
        else:
            result = transcribe_without_diarization(
                audio_file_path=audio_file_path,
                whisper_model=whisper_model
            )

        return result

    except Exception as e:
        return {
            'success': False,
            'transcript': '',
            'speakers_detected': 0,
            'error_message': str(e)
        }

def transcribe_without_diarization(audio_file_path: str,
                                  whisper_model: str = "small") -> Dict:
    """Simple transcription without speaker diarization"""
    
    try:
        # Load Whisper model
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = whisper.load_model(whisper_model, device=device)

        # Transcribe the entire audio
        result = model.transcribe(audio_file_path, task="translate")
        transcript = result['text'].strip()

        return {
            'success': True,
            'transcript': transcript,
            'speakers_detected': 1,
            'error_message': ''
        }

    except Exception as e:
        return {
            'success': False,
            'transcript': '',
            'speakers_detected': 0,
            'error_message': f"Transcription failed: {str(e)}"
        }
