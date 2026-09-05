import numpy as np
import tempfile
import os
import glob
from pathlib import Path
import soundfile as sf
from .audio_processor import AudioProcessor
from .speaker_diarization import SpeakerDiarization

class VoiceSampleManager:
    def __init__(self):
        self.known_speakers = {}  # This was missing but being accessed
        self.speaker_embeddings = {}
        self.speaker_names = []
        self.similarity_threshold = 0.70  # Add default threshold
        self.preloaded_loaded = False  # Track if preloaded samples are loaded
        self.all_known_speakers = {}  # Store all speakers (preloaded + uploaded)
        self.selected_speakers = set()  # Track which speakers are selected for recognition

        # ✅ NEW: Separate tracking for preloaded vs uploaded speakers
        self.preloaded_speakers = {}  # Only preloaded speakers
        self.uploaded_speakers = {}   # Only uploaded speakers

    def load_predefined_samples(self, folder_path="/content/sample"):
        """Load and process voice samples from a predefined folder"""
        if self.preloaded_loaded:
            print("✅ Preloaded samples already loaded, skipping...")
            return

        try:
            # Check if folder exists
            if not os.path.exists(folder_path):
                print(f"📁 Folder '{folder_path}' not found, skipping preloaded samples")
                return

            # Supported audio formats
            audio_extensions = ['*.wav', '*.mp3', '*.flac', '*.ogg', '*.m4a']
            audio_files = []

            # Find all audio files in the folder
            for extension in audio_extensions:
                audio_files.extend(glob.glob(os.path.join(folder_path, extension)))

            if not audio_files:
                print(f"📁 No audio files found in '{folder_path}'")
                return

            print(f"🔄 Loading {len(audio_files)} preloaded voice samples...")

            loaded_count = 0
            failed_count = 0

            for audio_file in audio_files:
                try:
                    # Extract speaker name from filename (without extension)
                    speaker_name = Path(audio_file).stem.title()

                    print(f"🎵 Processing preloaded sample: {speaker_name}")

                    # Process the voice sample using existing method
                    embedding = self.process_voice_sample_segments(audio_file, speaker_name)

                    if embedding is not None:
                        # ✅ FIXED: Add to preloaded_speakers instead of all_known_speakers
                        self.preloaded_speakers[speaker_name] = embedding  # ← Uses title case key

                        # Add to all_known_speakers (master collection)
                        self.all_known_speakers[speaker_name] = embedding  # ← Uses title case key

                        # Also add to current active speakers initially
                        self.add_voice_sample(speaker_name, embedding)

                        loaded_count += 1
                        print(f"✅ Successfully loaded preloaded sample: {speaker_name}")
                    else:
                        failed_count += 1
                        print(f"❌ Failed to process preloaded sample: {speaker_name}")

                except Exception as e:
                    failed_count += 1
                    print(f"❌ Error processing {audio_file}: {e}")

            self.preloaded_loaded = True
            print(f"🎉 Preloaded samples loaded: {loaded_count} successful, {failed_count} failed")

            return loaded_count, failed_count

        except Exception as e:
            print(f"❌ Error loading predefined samples: {e}")
            return 0, 0

    def update_selected_speakers(self, selected_speaker_names):
        """Update which speakers are active for recognition based on selection"""
        try:
            # Clear current active speakers
            self.speaker_embeddings.clear()
            self.speaker_names.clear()
            self.known_speakers.clear()

            # Add selected preloaded speakers back to active recognition
            for speaker_name in selected_speaker_names:
                if speaker_name in self.preloaded_speakers:
                    embedding = self.preloaded_speakers[speaker_name]
                    self.add_voice_sample(speaker_name, embedding)

            # ✅ FIXED: Always re-add uploaded speakers (they should always be active)
            for speaker_name, embedding in self.uploaded_speakers.items():
                self.add_voice_sample(speaker_name, embedding)

            self.selected_speakers = set(selected_speaker_names)
            print(f"🔄 Updated active speakers: {selected_speaker_names}")
            print(f"🔄 Uploaded speakers (always active): {list(self.uploaded_speakers.keys())}")

        except Exception as e:
            print(f"❌ Error updating selected speakers: {e}")

    def get_all_known_speaker_names(self):
        """Get list of all known speaker names (preloaded + uploaded)"""
        return list(self.all_known_speakers.keys())

    # ✅ NEW: Get only preloaded speaker names for selection UI
    def get_preloaded_speaker_names(self):
        """Get list of only preloaded speaker names for selection UI"""
        return list(self.preloaded_speakers.keys())

    # ✅ NEW: Get only uploaded speaker names for display purposes
    def get_uploaded_speaker_names(self):
        """Get list of only uploaded speaker names"""
        return list(self.uploaded_speakers.keys())

    def add_uploaded_voice_sample(self, speaker_name, embedding):
        """Add an uploaded voice sample (separate from preloaded)"""
        try:
            # ✅ FIXED: Add to uploaded_speakers instead of all_known_speakers directly
            self.uploaded_speakers[speaker_name] = embedding

            # Add to master collection
            self.all_known_speakers[speaker_name] = embedding

            # ✅ FIXED: Uploaded speakers should always be active
            # Add to active recognition regardless of selection state
            self.add_voice_sample(speaker_name, embedding)

            # Also add to selected speakers set to maintain consistency
            self.selected_speakers.add(speaker_name)

            return True
        except Exception as e:
            print(f"Error adding uploaded voice sample: {e}")
            return False

    def process_voice_sample_segments(self, audio_path, speaker_name):
        """Split voice sample into segments and average embeddings for better recognition"""
        try:
            # Load and preprocess audio
            processor = AudioProcessor()
            audio, sr = processor.load_audio(audio_path)
            processed_audio = processor.preprocess_audio(
                audio, sr,
                normalize_method="peak",
                apply_highpass=True,
                denoise_method='spectral_subtraction'
            )

            # Enhanced segmentation with quality filtering
            total_duration = len(processed_audio) / sr

            # Adaptive segment parameters based on total duration
            if total_duration >= 30:
                segment_duration = 8.0  # Longer segments for longer samples
                min_segments = 4
            elif total_duration >= 15:
                segment_duration = 6.0
                min_segments = 3
            else:
                segment_duration = max(4.0, total_duration / 3)  # Shorter minimum for short samples
                min_segments = 2

            sr = processor.target_sr
            segment_samples = int(segment_duration * sr)

            # Create overlapping segments for better coverage
            overlap_ratio = 0.3  # 30% overlap
            step_size = int(segment_samples * (1 - overlap_ratio))
            segments = []

            for i in range(0, len(processed_audio) - segment_samples + 1, step_size):
                segment = processed_audio[i:i + segment_samples]
                if len(segment) >= int(sr * 3):  # At least 3 seconds

                    # Quality filtering: check energy and spectral characteristics
                    energy = np.mean(segment ** 2)
                    if energy > 1e-6:  # Filter out very low energy segments

                        # Check for speech activity using simple spectral measures
                        from scipy import signal
                        f, psd = signal.welch(segment, sr, nperseg=1024)
                        speech_band_energy = np.sum(psd[(f >= 300) & (f <= 3400)])  # Typical speech band
                        total_energy = np.sum(psd)

                        if speech_band_energy / (total_energy + 1e-8) > 0.3:  # At least 30% energy in speech band
                            segments.append(segment)

            print(f"📊 Created {len(segments)} quality-filtered segments for {speaker_name}")

            # Extract embeddings with quality assessment
            embeddings = []
            embedding_qualities = []
            diarizer = SpeakerDiarization()

            if diarizer.load_speaker_model():
                for i, segment in enumerate(segments):
                    temp_file = None
                    try:
                        # Create temp file with unique name
                        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                        temp_path = temp_file.name
                        temp_file.close()  # Close file handle immediately
                        
                        # Write segment to temp file
                        sf.write(temp_path, segment, sr)
                        
                        # Process the segment
                        embedding = diarizer.extract_speaker_embedding(temp_path)
                        
                        if embedding is not None:
                            # Normalize embedding
                            embedding_norm = np.linalg.norm(embedding)
                            if embedding_norm > 1e-8:
                                normalized_embedding = embedding / embedding_norm
                                quality_score = min(embedding_norm / 10.0, 1.0)
                                embeddings.append(normalized_embedding)
                                embedding_qualities.append(quality_score)
                    
                    finally:
                        # Clean up temp file
                        if temp_file:
                            try:
                                os.unlink(temp_path)
                            except Exception:
                                pass  # Ignore cleanup errors

            if len(embeddings) >= min_segments:
                # Convert to numpy arrays for easier manipulation
                embeddings = np.array(embeddings)
                embedding_qualities = np.array(embedding_qualities)

                # Outlier removal using cosine similarity clustering
                if len(embeddings) > 3:
                    # Compute pairwise cosine similarities
                    similarities = np.dot(embeddings, embeddings.T)

                    # Find embeddings that are dissimilar to most others (potential outliers)
                    mean_similarities = np.mean(similarities, axis=1)
                    similarity_threshold = np.percentile(mean_similarities, 25)  # Bottom 25%

                    # Keep embeddings above threshold
                    valid_indices = mean_similarities >= similarity_threshold
                    embeddings = embeddings[valid_indices]
                    embedding_qualities = embedding_qualities[valid_indices]

                    print(f"🔍 Filtered out {np.sum(~valid_indices)} outlier embeddings")

                if len(embeddings) > 0:
                    # Weighted average based on quality scores
                    if len(embedding_qualities) > 1:
                        # Enhance quality differences
                        enhanced_qualities = embedding_qualities ** 1.5
                        weights = enhanced_qualities / np.sum(enhanced_qualities)
                        avg_embedding = np.average(embeddings, axis=0, weights=weights)
                    else:
                        avg_embedding = embeddings[0]

                    # Final normalization
                    avg_embedding = avg_embedding / (np.linalg.norm(avg_embedding) + 1e-8)

                    # Additional robustness: create ensemble with median
                    if len(embeddings) >= 3:
                        median_embedding = np.median(embeddings, axis=0)
                        median_embedding = median_embedding / (np.linalg.norm(median_embedding) + 1e-8)

                        # Blend mean and median (70% mean, 30% median)
                        final_embedding = 0.7 * avg_embedding + 0.3 * median_embedding
                        final_embedding = final_embedding / (np.linalg.norm(final_embedding) + 1e-8)
                    else:
                        final_embedding = avg_embedding

                    print(f"✅ Generated robust embedding from {len(embeddings)} segments for {speaker_name}")
                    print(f"📈 Average quality score: {np.mean(embedding_qualities):.3f}")
                    return final_embedding
                else:
                    print(f"❌ No valid embeddings after quality filtering for {speaker_name}")
                    return None
            else:
                print(f"❌ Insufficient segments ({len(embeddings)}/{min_segments}) for {speaker_name}")
                return None

        except Exception as e:
            print(f"❌ Error processing voice sample segments: {e}")
            return None

    def add_voice_sample(self, speaker_name, embedding):
        """Add a voice sample embedding for a speaker"""
        try:
            self.speaker_embeddings[speaker_name] = embedding
            self.known_speakers[speaker_name] = embedding  # Add to known_speakers as well
            if speaker_name not in self.speaker_names:
                self.speaker_names.append(speaker_name)
            return True
        except Exception as e:
            print(f"Error adding voice sample: {e}")
            return False

    def identify_speaker(self, input_embedding):
        """
        Identify a speaker from an input embedding with adaptive fallback logic
        Returns (speaker_name, confidence) or (fallback_label, confidence) or (None, confidence)
        """
        if not self.speaker_embeddings:
            return None, 0.0

        # Normalize input embedding
        input_embedding = input_embedding / (np.linalg.norm(input_embedding) + 1e-8)

        # Collect all similarities with enhanced scoring
        speaker_scores = {}
        all_similarities = []

        for speaker_name, known_embedding in self.speaker_embeddings.items():
            # Handle both single embeddings and multiple embeddings per speaker
            if isinstance(known_embedding, list):
                # Multiple embeddings per speaker - use best match approach
                similarities = []
                for emb in known_embedding:
                    emb_norm = emb / (np.linalg.norm(emb) + 1e-8)
                    sim = np.dot(input_embedding, emb_norm)
                    similarities.append(sim)

                # Use weighted combination: 60% best match + 40% average of top matches
                similarities = sorted(similarities, reverse=True)
                if len(similarities) >= 3:
                    top_sims = similarities[:3]
                    final_similarity = 0.6 * similarities[0] + 0.4 * np.mean(top_sims)
                else:
                    final_similarity = 0.7 * similarities[0] + 0.3 * np.mean(similarities)

            else:
                # Single embedding per speaker
                known_embedding = known_embedding / (np.linalg.norm(known_embedding) + 1e-8)
                final_similarity = np.dot(input_embedding, known_embedding)

            speaker_scores[speaker_name] = final_similarity
            all_similarities.append(final_similarity)

        if not speaker_scores:
            return None, 0.0

        # Find best match
        best_speaker = max(speaker_scores.keys(), key=lambda x: speaker_scores[x])
        best_similarity = speaker_scores[best_speaker]

        # Enhanced confidence scoring for borderline cases
        enhanced_confidence = self._calculate_enhanced_confidence(
            best_similarity, speaker_scores, all_similarities
        )

        # Calculate dynamic thresholds based on user-defined similarity_threshold
        main_threshold = self.similarity_threshold

        # FALLBACK THRESHOLD: Set fallback range as percentage below main threshold
        fallback_range = max(0.08, main_threshold * 0.12)  # 12% of threshold, minimum 0.08
        fallback_threshold = main_threshold - fallback_range

        # Ensure fallback threshold is reasonable (not too low)
        fallback_threshold = max(fallback_threshold, 0.60)

        # DECISION LOGIC WITH ADAPTIVE FALLBACK

        # 1. CONFIDENT MATCH: Above main threshold
        if enhanced_confidence >= main_threshold:
            return best_speaker, enhanced_confidence

        # 2. FALLBACK RANGE: Close to threshold but not quite there
        elif enhanced_confidence >= fallback_threshold:
            # Additional validation for fallback cases
            is_clear_winner = True

            # Check if this is clearly the best match among multiple speakers
            if len(speaker_scores) > 1:
                sorted_scores = sorted(speaker_scores.values(), reverse=True)
                margin = sorted_scores[0] - sorted_scores[1]

                # Require minimum margin for fallback (stricter than confident match)
                min_margin = max(0.03, (main_threshold - fallback_threshold) * 0.4)
                if margin < min_margin:
                    is_clear_winner = False

            # Apply fallback label if it's a clear winner
            if is_clear_winner:
                # ✅ INSERT FALLBACK LABEL HERE
                fallback_label = f"likely to be {best_speaker}"
                return fallback_label, enhanced_confidence

        # 3. UNCERTAIN MATCH: Below fallback threshold
        return None, enhanced_confidence

    def _calculate_enhanced_confidence(self, raw_similarity, speaker_scores, all_similarities):
        """Calculate enhanced confidence score with dynamic adaptation"""

        similarity_threshold = 0.70  # Hardcoded here
        confidence = raw_similarity

        # Enhancement 1: Relative ranking boost
        if len(speaker_scores) > 1:
            sorted_scores = sorted(speaker_scores.values(), reverse=True)
            margin = sorted_scores[0] - sorted_scores[1]

            max_boost = min(0.06, similarity_threshold * 0.08)
            margin_boost = min(max_boost, margin * 0.6)
            confidence += margin_boost

        # Enhancement 2: Score distribution analysis
        if len(all_similarities) > 1:
            mean_sim = np.mean(all_similarities)
            std_sim = np.std(all_similarities)

            if std_sim > 0.01:
                z_score = (raw_similarity - mean_sim) / std_sim
                if z_score > 1.0:
                    max_dist_boost = min(0.04, similarity_threshold * 0.05)
                    distribution_boost = min(max_dist_boost, (z_score - 1.0) * 0.025)
                    confidence += distribution_boost

        # Enhancement 3: Uncertainty penalty
        uncertain_lower = similarity_threshold - 0.15
        uncertain_upper = similarity_threshold - 0.05

        if uncertain_lower <= raw_similarity <= uncertain_upper:
            penalty_factor = (uncertain_upper - raw_similarity) / (uncertain_upper - uncertain_lower)
            uncertainty_penalty = 0.02 * penalty_factor
            confidence -= uncertainty_penalty

        # Clamp the confidence value
        confidence = min(confidence, min(0.95, similarity_threshold + 0.10))
        confidence = max(confidence, raw_similarity)

        return confidence

    def _get_adaptive_threshold(self, all_similarities):
        """Calculate adaptive threshold based on similarity score distribution"""

        similarity_threshold = 0.70  # Hardcoded here

        if len(all_similarities) <= 1:
            return similarity_threshold

        mean_sim = np.mean(all_similarities)
        max_sim = np.max(all_similarities)

        if mean_sim < 0.65:
            adaptive_threshold = max(0.72, similarity_threshold - 0.05)
        elif mean_sim > 0.75:
            adaptive_threshold = similarity_threshold
        else:
            if max_sim >= 0.85:
                adaptive_threshold = similarity_threshold
            elif max_sim >= 0.75:
                adaptive_threshold = similarity_threshold - 0.02
            else:
                adaptive_threshold = max(0.73, similarity_threshold - 0.04)

        return adaptive_threshold

    def get_speaker_names(self):
        """Get list of known speaker names"""
        return self.speaker_names.copy()

    def clear_all(self):
        """Clear all voice samples"""
        self.speaker_embeddings.clear()
        self.speaker_names.clear()
        self.known_speakers.clear()