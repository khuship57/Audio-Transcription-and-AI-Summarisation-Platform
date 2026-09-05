import torch
import torchaudio
import numpy as np
import tempfile
import librosa
import soundfile as sf
from pathlib import Path
from typing import Dict
import whisper
import re
from datetime import timedelta

try:
    from speechbrain.pretrained import VAD, EncoderClassifier
    SPEECHBRAIN_AVAILABLE = True
except ImportError:
    SPEECHBRAIN_AVAILABLE = False

class SpeakerDiarization:
    def __init__(self):
        if not SPEECHBRAIN_AVAILABLE:
            raise ImportError("SpeechBrain is required for speaker diarization")
            
        self.vad_device = "cpu"
        self.speaker_device = "cuda" if torch.cuda.is_available() else "cpu"
        self.sample_rate = 16000

    def load_models(self) -> bool:
        """Load both VAD and speaker recognition models"""
        try:
            # Load VAD model (CPU only)
            self.vad = VAD.from_hparams(
                source="speechbrain/vad-crdnn-libriparty",
                run_opts={"device": self.vad_device}
            )

            # Load speaker model
            self.classifier = EncoderClassifier.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb",
                savedir="pretrained_models/spkrec-ecapa-voxceleb",
                run_opts={"device": self.speaker_device}
            )

            return True
        except Exception as e:
            print(f"Failed to load diarization models: {str(e)}")
            return False

    def load_speaker_model(self):
        """Load Speaker Recognition model"""
        try:
            self.classifier = EncoderClassifier.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb",
                savedir="pretrained_models/spkrec-ecapa-voxceleb",
                run_opts={"device": self.speaker_device}
            )
            return True
        except Exception as e:
            print(f"Failed to load speaker model: {str(e)}")
            return False

    def get_speech_segments(self, audio_path, threshold=0.5, min_duration=0.25):
        """Detect speech segments using VAD"""
        try:
            # Load audio
            waveform, sr = torchaudio.load(audio_path)
            waveform = waveform.float().contiguous()

            # Resample if needed
            if sr != self.sample_rate:
                waveform = torchaudio.functional.resample(
                    waveform, sr, self.sample_rate
                ).float().contiguous()

            signal = waveform[0].cpu().float().contiguous()

            with torch.no_grad():
                input_tensor = signal.unsqueeze(0).cpu().float().contiguous()
                probs = self.vad.forward(input_tensor)

            # Process results
            probs = probs.squeeze().cpu().numpy()
            frame_duration = 0.01
            segments = []
            start = None

            for i, p in enumerate(probs):
                t = i * frame_duration
                if p > threshold:
                    if start is None:
                        start = t
                else:
                    if start is not None:
                        end = t
                        if end - start >= min_duration:
                            segments.append((start, end))
                        start = None

            if start is not None:
                end = len(probs) * frame_duration
                if end - start >= min_duration:
                    segments.append((start, end))

            return segments

        except Exception as e:
            print(f"Error in VAD processing: {e}")
            raise

    def extract_speaker_embedding(self, audio_path):
        """Extract speaker embedding"""
        try:
            # Load audio
            signal, fs = torchaudio.load(audio_path)

            # Resample if needed
            if fs != 16000:
                resampler = torchaudio.transforms.Resample(fs, 16000)
                signal = resampler(signal)

            # Convert to mono if needed
            if signal.shape[0] > 1:
                signal = torch.mean(signal, dim=0, keepdim=True)

            # Apply preprocessing
            audio_np = signal.squeeze().numpy()
            from .audio_processor import AudioProcessor
            processor = AudioProcessor()
            processed_audio = processor.preprocess_audio(
                audio_np, 16000,
                normalize_method="peak",
                apply_highpass=True,
                denoise_method='spectral_subtraction'
            )

            signal = torch.from_numpy(processed_audio).unsqueeze(0).float()

            # Check minimum length
            min_samples = 16000 * 1.0
            if signal.shape[1] < min_samples:
                padding_needed = min_samples - signal.shape[1]
                signal = torch.nn.functional.pad(signal, (0, padding_needed))

            signal = signal.to(self.speaker_device)

            with torch.no_grad():
                try:
                    embedding = self.classifier.encode_batch(signal)
                    embedding = embedding.squeeze().cpu().numpy()
                except Exception as model_error:
                    signal_cpu = signal.cpu()
                    embedding = self.classifier.encode_batch(signal_cpu)
                    embedding = embedding.squeeze().cpu().numpy()

            # Validate embedding
            if embedding.size == 0 or np.any(np.isnan(embedding)) or np.any(np.isinf(embedding)):
                return None

            # Normalize embedding
            embedding = embedding / (np.linalg.norm(embedding) + 1e-8)

            return embedding

        except Exception as e:
            print(f"Error extracting embedding: {str(e)}")
            return None

def transcribe_with_diarization(audio_file_path: str,
                               whisper_model: str = "base",
                               min_speakers: int = 2,
                               max_speakers: int = 8,
                               voice_manager=None) -> Dict:
    """Main function to transcribe audio with speaker diarization"""
    
    if not SPEECHBRAIN_AVAILABLE:
        return {
            'success': False,
            'transcript': '',
            'speakers_detected': 0,
            'error_message': 'SpeechBrain is not installed.'
        }

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Convert to WAV
            from .audio_processor import AudioProcessor
            processor = AudioProcessor()
            wav_file = temp_path / "converted.wav"

            success, message = processor.convert_to_wav(audio_file_path, wav_file)
            if not success:
                return {
                    'success': False,
                    'transcript': '',
                    'speakers_detected': 0,
                    'error_message': f"Audio conversion failed: {message}"
                }

            # Preprocess audio
            audio, sr = processor.load_audio(str(wav_file))
            processed_audio = processor.preprocess_audio(
                audio, sr,
                normalize_method='peak',
                apply_highpass=True,
                denoise_method='spectral_subtraction'
            )

            preprocessed_file = temp_path / "preprocessed.wav"
            sf.write(preprocessed_file, processed_audio, processor.target_sr)

            # Initialize diarization
            diarizer = SpeakerDiarization()
            if not diarizer.load_models():
                return {
                    'success': False,
                    'transcript': '',
                    'speakers_detected': 0,
                    'error_message': "Failed to load speaker diarization models"
                }

            # Detect speech segments
            speech_segments = diarizer.get_speech_segments(str(preprocessed_file))
            if not speech_segments:
                return {
                    'success': False,
                    'transcript': '',
                    'speakers_detected': 0,
                    'error_message': "No speech segments detected in audio"
                }

            # Create overlapping segments
            segments_dir = temp_path / "segments"
            segments_dir.mkdir(exist_ok=True)

            segment_files = create_overlapping_segments(
                str(preprocessed_file), segments_dir, speech_segments
            )

            # Extract speaker embeddings
            embeddings, filenames = extract_embeddings(segment_files, diarizer)
            if len(embeddings) == 0:
                return {
                    'success': False,
                    'transcript': '',
                    'speakers_detected': 0,
                    'error_message': "No valid speaker embeddings could be extracted"
                }

            # Cluster speakers
            from sklearn.cluster import AgglomerativeClustering
            from sklearn.metrics import silhouette_score
            
            speaker_labels_list = cluster_speakers(
                embeddings, filenames, min_speakers, max_speakers
            )

            speaker_labels = {}
            for filename, cluster_id in speaker_labels_list:
                speaker_labels[filename] = f"Speaker_{cluster_id}"

            speakers_detected = len(set(speaker_labels.values()))

            # Map cluster IDs to known speaker names if voice_manager is provided
            cluster_to_name = {}
            if voice_manager and voice_manager.get_speaker_names():
                segment_cluster_pairs = []
                for filename, speaker in speaker_labels.items():
                    cluster_id = int(speaker.split('_')[1])
                    segment_cluster_pairs.append((filename, cluster_id))

                cluster_to_name = identify_known_speakers_integrated(embeddings, segment_cluster_pairs, voice_manager)
            else:
                unique_speakers = set(speaker_labels.values())
                for speaker_id in unique_speakers:
                    cluster_id = int(speaker_id.split('_')[1])
                    cluster_to_name[cluster_id] = speaker_id

            # Transcribe with speaker labels
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model = whisper.load_model(whisper_model, device=device)

            # Parse segments and merge by speaker
            segments = []
            for filename, speaker in speaker_labels.items():
                match = re.search(r'_(\d+\.\d+)_(\d+\.\d+)\.wav', filename)
                if match:
                    start_time = float(match.group(1))
                    end_time = float(match.group(2))
                    cluster_id = int(speaker.split('_')[1])
                    real_speaker_name = cluster_to_name.get(cluster_id, speaker)
                    segments.append({
                        'filename': filename,
                        'start': start_time,
                        'end': end_time,
                        'speaker': real_speaker_name
                    })

            # Sort by time and merge consecutive segments of same speaker
            segments.sort(key=lambda x: x['start'])
            merged_segments = merge_speaker_segments(segments)

            # Transcribe merged segments
            transcripts = []
            y, sr = librosa.load(str(preprocessed_file), sr=16000)

            for i, seg in enumerate(merged_segments):
                # Extract audio segment
                start_sample = int(seg['start'] * sr)
                end_sample = int(seg['end'] * sr)
                segment_audio = y[start_sample:end_sample]

                # Save temporary segment
                temp_segment = temp_path / f"temp_segment_{i}.wav"
                sf.write(temp_segment, segment_audio, sr)

                # Transcribe
                try:
                    result = model.transcribe(str(temp_segment), task="translate")
                    text = result['text'].strip()

                    if text:
                        transcripts.append({
                            'speaker': seg['speaker'],
                            'text': text
                        })
                except Exception as e:
                    print(f"Failed to transcribe segment {i}: {str(e)}")

            # Format transcript with speaker labels
            formatted_transcript = ""
            for t in transcripts:
                formatted_transcript += f"**{t['speaker']}:** {t['text']}\n\n"

            return {
                'success': True,
                'transcript': formatted_transcript.strip(),
                'speakers_detected': speakers_detected,
                'error_message': ''
            }

    except Exception as e:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        return {
            'success': False,
            'transcript': '',
            'speakers_detected': 0,
            'error_message': f"Processing failed: {str(e)}"
        }

def create_overlapping_segments(audio_file, output_dir, speech_segments,
                               window_duration=2.0, overlap=0.5):
    """Create overlapping segments from speech regions"""
    y, sr = librosa.load(audio_file, sr=16000)
    window_samples = int(window_duration * sr)
    hop_samples = int((window_duration - overlap) * sr)

    segment_files = []
    segment_id = 0

    for start_time, end_time in speech_segments:
        start_sample = int(start_time * sr)
        end_sample = int(end_time * sr)
        segment_audio = y[start_sample:end_sample]

        for i in range(0, len(segment_audio) - window_samples + 1, hop_samples):
            chunk = segment_audio[i:i + window_samples]
            if len(chunk) == window_samples:
                chunk_start_time = start_time + (i / sr)
                chunk_end_time = start_time + ((i + window_samples) / sr)

                filename = f"segment{segment_id:03d}_{chunk_start_time:.2f}_{chunk_end_time:.2f}.wav"
                filepath = output_dir / filename
                sf.write(filepath, chunk, sr)
                segment_files.append(str(filepath))
                segment_id += 1

    return segment_files

def extract_embeddings(segment_files, diarizer):
    """Extract speaker embeddings from segment files"""
    embeddings = []
    filenames = []

    for file_path in segment_files:
        embedding = diarizer.extract_speaker_embedding(file_path)
        if embedding is not None:
            embeddings.append(embedding)
            filenames.append(Path(file_path).name)

    return np.array(embeddings) if embeddings else np.array([]), filenames

def cluster_speakers(embeddings, filenames, min_speakers, max_speakers):
    """Cluster speaker embeddings to identify different speakers"""
    if len(embeddings) < min_speakers:
        return [(info, 0) for info in filenames]

    embeddings_array = np.array(embeddings)

    best_score = -1
    best_labels = None
    best_n_clusters = min_speakers

    from sklearn.cluster import AgglomerativeClustering
    from sklearn.metrics import silhouette_score

    for n_clusters in range(min_speakers, min(max_speakers + 1, len(embeddings) + 1)):
        try:
            clustering = AgglomerativeClustering(
                n_clusters=n_clusters,
                linkage='ward',
                metric='euclidean'
            )
            labels = clustering.fit_predict(embeddings_array)

            if len(set(labels)) > 1:
                score = silhouette_score(embeddings_array, labels)
                if score > best_score:
                    best_score = score
                    best_labels = labels
                    best_n_clusters = n_clusters
        except Exception as e:
            print(f"Clustering failed for {n_clusters} clusters: {e}")
            continue

    if best_labels is None:
        best_labels = [0] * len(filenames)

    return list(zip(filenames, best_labels))

def merge_speaker_segments(segments, max_gap=1.0):
    """Merge consecutive segments from the same speaker"""
    if not segments:
        return []

    merged = []
    current = segments[0].copy()

    for seg in segments[1:]:
        if (seg['speaker'] == current['speaker'] and
            seg['start'] - current['end'] <= max_gap):
            current['end'] = seg['end']
        else:
            merged.append(current)
            current = seg.copy()

    merged.append(current)
    return merged

def identify_known_speakers_integrated(embeddings, speaker_labels, voice_manager):
    """Identify known speakers by comparing cluster embeddings with known voice samples"""
    if not voice_manager or not voice_manager.get_speaker_names():
        unique_speakers = set(label[1] for label in speaker_labels)
        cluster_to_name = {}
        for speaker_id in unique_speakers:
            cluster_to_name[speaker_id] = f"Speaker_{speaker_id}"
        return cluster_to_name

    # Group embeddings by cluster ID
    cluster_embeddings = {}
    for i, (segment_info, cluster_id) in enumerate(speaker_labels):
        if cluster_id not in cluster_embeddings:
            cluster_embeddings[cluster_id] = []
        cluster_embeddings[cluster_id].append(embeddings[i])

    cluster_matches = []
    for cluster_id, cluster_embs in cluster_embeddings.items():
        avg_embedding = np.mean(cluster_embs, axis=0)
        speaker_name, confidence = voice_manager.identify_speaker(avg_embedding)

        if speaker_name and confidence > 0.5:
            cluster_matches.append((cluster_id, speaker_name, confidence))

    cluster_matches.sort(key=lambda x: x[2], reverse=True)

    assigned_names = set()
    cluster_to_name = {}
    unknown_counter = 1 

    all_confidences = [match[2] for match in cluster_matches]
    adaptive_threshold = voice_manager._get_adaptive_threshold(all_confidences) if all_confidences else 0.8
    fallback_threshold = adaptive_threshold - 0.05

    for cluster_id, speaker_name, confidence in cluster_matches:
        base_name = speaker_name.replace("likely to be ", "")

        if base_name in assigned_names:
            cluster_to_name[cluster_id] = f"Unknown_{unknown_counter}"
            unknown_counter += 1
            continue

        if confidence >= adaptive_threshold:
            cluster_to_name[cluster_id] = base_name
            assigned_names.add(base_name)
        elif confidence >= fallback_threshold:
            likely_label = f"Likely to be {base_name}"
            cluster_to_name[cluster_id] = likely_label
            assigned_names.add(base_name)
        else:
            cluster_to_name[cluster_id] = f"Unknown_{unknown_counter}"
            unknown_counter += 1

    for cluster_id in cluster_embeddings.keys():
        if cluster_id not in cluster_to_name:
            cluster_to_name[cluster_id] = f"Unknown_{unknown_counter}"
            unknown_counter += 1

    return cluster_to_name