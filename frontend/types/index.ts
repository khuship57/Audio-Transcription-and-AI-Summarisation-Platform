export interface ProcessingOptions {
  enable_diarization: boolean
  enable_speaker_recognition: boolean
  whisper_model: string
  min_speakers: number
  max_speakers: number
}

export interface ProcessingResult {
  success: boolean
  transcript: string
  summary: string
  speakers_detected: number
  duration: string
  processing_stats: {
    original_chunks: number
    unique_chunks: number
    topics_identified: number
  }
}

export interface VoiceSampleResult {
  success: boolean
  speaker_name: string
  message: string
}

export interface SpeakersData {
  preloaded_speakers: string[]
  uploaded_speakers: string[]
  active_speakers: string[]
}

export interface SpeakerSelectionResult {
  success: boolean
  active_speakers: string[]
}
