import re
from typing import List, Dict
from nltk.tokenize import sent_tokenize
import nltk
nltk.download('punkt_tab')

class SpeakerAwareChunker:
    """
    Chunker that respects speaker boundaries for diarized transcripts.
    Each chunk maintains speaker coherence and includes existing speaker labels.
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.sentences_per_subchunk = 3

    def split_into_speaker_chunks(self, text: str) -> List[str]:
        """
        Split speaker-labeled text into chunks that respect speaker boundaries.
        Groups consecutive sentences by the same speaker.

        Args:
            text: Speaker-labeled text with existing labels like "**jay:** content **alice:** content"

        Returns:
            List of chunks, each maintaining speaker coherence
        """
        speaker_segments = self._parse_speaker_segments(text)

        # Group consecutive segments by the same speaker
        grouped_segments = self._group_consecutive_speakers(speaker_segments)

        chunks = []
        for segment in grouped_segments:
            speaker_chunks = self._chunk_speaker_segment(segment)
            chunks.extend(speaker_chunks)

        return chunks

    def _parse_speaker_segments(self, text: str) -> List[Dict[str, str]]:
        """
        Parse text into speaker segments using existing speaker labels.

        Returns:
            List of dicts with 'speaker' and 'text' keys
        """
        segments = []

        # Updated pattern to capture any speaker name, not just Speaker_X
        speaker_pattern = r'\*\*([^*:]+):\*\*'

        matches = list(re.finditer(speaker_pattern, text))

        if not matches:
            # If no speaker labels found, return the entire text without adding fallback labels
            return [{'speaker': '', 'text': text.strip()}]

        for i, match in enumerate(matches):
            speaker = match.group(1).strip()  # Extract the actual speaker name
            start_pos = match.end()

            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(text)

            speaker_text = text[start_pos:end_pos].strip()

            if speaker_text:
                segments.append({
                    'speaker': speaker,
                    'text': speaker_text
                })

        return segments

    def _group_consecutive_speakers(self, segments: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Group consecutive segments by the same speaker to avoid speaker overlap in chunks.

        Args:
            segments: List of individual speaker segments

        Returns:
            List of grouped segments where consecutive same-speaker segments are merged
        """
        if not segments:
            return []

        grouped = []
        current_speaker = segments[0]['speaker']
        current_text = segments[0]['text']

        for i in range(1, len(segments)):
            segment = segments[i]

            if segment['speaker'] == current_speaker:
                # Same speaker, merge the text
                current_text += ' ' + segment['text']
            else:
                # Different speaker, save current group and start new one
                grouped.append({
                    'speaker': current_speaker,
                    'text': current_text
                })
                current_speaker = segment['speaker']
                current_text = segment['text']

        # Add the last group
        grouped.append({
            'speaker': current_speaker,
            'text': current_text
        })

        return grouped

    def _chunk_speaker_segment(self, segment: Dict[str, str]) -> List[str]:
        """
        Chunk a single speaker's segment, maintaining existing speaker label.

        Args:
            segment: Dict with 'speaker' and 'text' keys

        Returns:
            List of chunks for this speaker
        """
        speaker = segment['speaker']
        text = segment['text']

        sentences = sent_tokenize(text)
        estimated_tokens = len(text) // 4

        chunks = []

        if estimated_tokens <= self.chunk_size:
            # Small segment, create single chunk
            if speaker:
                chunk_text = f"**{speaker}:** {text}"
            else:
                chunk_text = text
            chunks.append(chunk_text)
        else:
            # Large segment, create sub-chunks
            sub_chunks = self._create_sub_chunks(sentences, speaker)
            chunks.extend(sub_chunks)

        return chunks

    def _create_sub_chunks(self, sentences: List[str], speaker: str) -> List[str]:
        """
        Create sub-chunks from sentences, maintaining existing speaker label.

        Args:
            sentences: List of sentences from the speaker
            speaker: Speaker identifier (could be name like 'jay' or empty)

        Returns:
            List of sub-chunks
        """
        chunks = []
        current_chunk_sentences = []
        current_chunk_tokens = 0

        for sentence in sentences:
            sentence_tokens = len(sentence) // 4

            # Check if adding this sentence would exceed chunk size
            if (current_chunk_tokens + sentence_tokens > self.chunk_size and
                current_chunk_sentences):

                # Create chunk with current sentences
                if speaker:
                    chunk_text = f"**{speaker}:** {' '.join(current_chunk_sentences)}"
                else:
                    chunk_text = ' '.join(current_chunk_sentences)
                chunks.append(chunk_text)

                # Handle overlap: keep last sentence if we have multiple sentences
                if len(current_chunk_sentences) > 1:
                    current_chunk_sentences = [current_chunk_sentences[-1]]
                    current_chunk_tokens = len(current_chunk_sentences[0]) // 4
                else:
                    current_chunk_sentences = []
                    current_chunk_tokens = 0

            current_chunk_sentences.append(sentence)
            current_chunk_tokens += sentence_tokens

            # Create chunk if we've reached the target sentences per subchunk
            if len(current_chunk_sentences) >= self.sentences_per_subchunk:
                if speaker:
                    chunk_text = f"**{speaker}:** {' '.join(current_chunk_sentences)}"
                else:
                    chunk_text = ' '.join(current_chunk_sentences)
                chunks.append(chunk_text)

                # Handle overlap
                if len(current_chunk_sentences) > 1:
                    current_chunk_sentences = [current_chunk_sentences[-1]]
                    current_chunk_tokens = len(current_chunk_sentences[0]) // 4
                else:
                    current_chunk_sentences = []
                    current_chunk_tokens = 0

        # Add remaining sentences as final chunk
        if current_chunk_sentences:
            if speaker:
                chunk_text = f"**{speaker}:** {' '.join(current_chunk_sentences)}"
            else:
                chunk_text = ' '.join(current_chunk_sentences)
            chunks.append(chunk_text)

        return chunks