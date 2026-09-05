from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
import torch
import whisper
import numpy as np
import librosa
import soundfile as sf
import gc
from pathlib import Path
import json
import traceback
from werkzeug.utils import secure_filename
import logging
from dotenv import load_dotenv
import openai
import time

# Import the core classes from the original application
from models.audio_processor import AudioProcessor
from models.speaker_diarization import transcribe_with_diarization
from models.voice_sample_manager import VoiceSampleManager
from models.text_preprocessor import TextPreprocessor, PreprocessingConfig
from models.text_summarizer import TextSummarizer, SummaryPostProcessor
from models.pdf_generator import PDFGenerator

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables for AI refining
BASE_URL = os.getenv('BASE_URL', 'https://models.inference.ai.azure.com')
MODEL = os.getenv('MODEL', 'gpt-4o')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

# Global instances
audio_processor = None
voice_manager = None
text_preprocessor = None
text_summarizer = None
pdf_generator = None
summary_post_processor = None

# Initialize models on startup
def initialize_models():
    global audio_processor, voice_manager, text_preprocessor, text_summarizer, pdf_generator, summary_post_processor
    
    try:
        logger.info("Initializing models...")
        audio_processor = AudioProcessor()
        voice_manager = VoiceSampleManager()
        
        # Initialize text preprocessor with custom config
        preprocessing_config = PreprocessingConfig(
            remove_timestamps=True,
            remove_fillers=True,
            fix_contractions=True,
            remove_duplicates=True,
            fix_punctuation=True,
            segment_sentences=True,
            remove_stopwords=False,
            chunk_size=512,
            chunk_overlap=50
        )
        text_preprocessor = TextPreprocessor(preprocessing_config)
        
        text_summarizer = TextSummarizer()
        summary_post_processor = SummaryPostProcessor()
        pdf_generator = PDFGenerator()
        
        # Load preloaded voice samples
        voice_manager.load_predefined_samples("sample")
        
        logger.info("Models initialized successfully")
        
        # Check if AI refining is available
        if GITHUB_TOKEN:
            logger.info("AI refining available with token")
        else:
            logger.info("AI refining not available - no token provided")
            
        return True
    except Exception as e:
        logger.error(f"Failed to initialize models: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def refine_summary_with_ai(markdown_content, enable_diarization=True):
    """Refine the summary using AI if token is available"""
    if not GITHUB_TOKEN:
        logger.info("No AI token available, returning original summary")
        return markdown_content
    
    try:
        logger.info("Refining summary with AI...")
        
        client = openai.OpenAI(
            api_key=GITHUB_TOKEN,
            base_url=BASE_URL
        )

        # Adjust system prompt based on whether speaker diarization was used
        if enable_diarization:
            system_prompt = """You are an expert meeting summary editor. Transform raw meeting summaries into professional, well-structured documents that preserve speaker identity and provide actionable insights using a clean, bullet-point format.

## CRITICAL REQUIREMENTS:

### 1. **Speaker Attribution**:
- ALWAYS include speaker references naturally within bullet points
- Speaker references will already appear in the form: "Speaker_1 shared that...", "Speaker_2 explained that..."
- PRESERVE these speaker references exactly as written — do not remove, reword, or paraphrase them
- Use real names only when they are explicitly mentioned in the transcript
- Do NOT hallucinate or invent speaker names
- NEVER use prefix format like "**Speaker_1:**" or "Speaker_1:" at the start of lines

### 2. **Content Organization & Format**:
- Include a **"Meeting Agenda"** section near the top, right after "Meeting Duration"
- List the main topic headers from your key discussion points (e.g., Academic Research & Education, General Discussion, Music & Performing Arts)
- Use clean section headers like "Key Discussion Points", "Academic Research & Education", "General Discussion", etc.
- Group related discussions into logical topic sections under these headers
- **Use bullet points exclusively** — no dense paragraphs or unbroken text blocks
- Each bullet point should contain one key insight or contribution with speaker attribution
- Format: "• Speaker_1 shared that..." or "• khushi noted that..."
- Remove redundant or repeated information
- Preserve all unique insights and speaker contributions
- Maintain professional spacing and minimal structure

### 3. **Required Summary Structure**:
Your summary MUST end with these four sections:

**## Meeting Agenda Points**
- List the main topics discussed (with speaker attribution when relevant)

**## Action Items**
- Specific tasks mentioned during the meeting
- Include responsible person/speaker when mentioned
- Format: "Task description (Assigned: Speaker_X or Name)"

**## Required Follow-Ups**
- Items that need follow-up in future meetings
- Include who should follow up when mentioned

**## Suggested Topics for Future Meetings**
- Topics that were mentioned for future discussion
- Include who suggested them when mentioned

### 4. **Tone and Style**:
- Professional but readable
- Clean, minimal formatting with clear section breaks
- Suitable for stakeholders who weren't present
- Each bullet point should be concise but complete
- Include speaker perspectives and different viewpoints

**Remember**: The goal is a comprehensive, actionable summary that clearly shows who contributed what, organized in a clean bullet-point format for easy reference and follow-up. Think professional meeting minutes, not narrative paragraphs.

**Note**:You may reduce content length, but only by removing duplicated information. Do not remove unique details.**"""
        else:
            system_prompt = """You are an expert meeting summary editor. Transform raw meeting summaries into well-structured, clear documents. Focus on:
1. Enhancing readability and logical flow
2. Eliminating redundancies - remove repeated information and consolidate similar points
3. Organizing content into clearly defined sections
4. Extracting and highlighting:
  - Meeting agenda points
  - Action items with owners and deadlines
  - Required follow-ups
  - Suggested topics for future meetings
5. Preserving meeting duration and all unique, non-redundant information
You may reduce content length, but only by removing duplicated information. Do not remove unique details."""

        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": f"Refine this meeting summary to improve clarity and organization. Remove any repeated information while keeping all unique content.\n\nSUMMARY:\n{markdown_content}"
                }
            ],
            model=MODEL,
            temperature=0.5,
            max_tokens=10000
        )
        
        refined_summary = response.choices[0].message.content.strip()
        logger.info("Summary refined successfully with AI")
        return refined_summary
        
    except Exception as e:
        logger.warning(f"Could not refine summary with AI: {str(e)}. Using original summary.")
        return markdown_content

def simple_transcription_pipeline(audio_file_path, whisper_model="small"):
    """Simple transcription without diarization"""
    temp_file_path = None
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = whisper.load_model(whisper_model, device=device)
        
        # Preprocess audio
        audio, sr = audio_processor.load_audio(audio_file_path)
        processed_audio = audio_processor.preprocess_audio(
            audio, sr,
            normalize_method='peak',
            apply_highpass=True,
            denoise_method='spectral_subtraction'
        )
        
        # Create temp file and close it properly
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_file_path = temp_file.name
        temp_file.close()  # Close the file handle before writing
        
        # Write audio data to the closed temp file
        sf.write(temp_file_path, processed_audio, audio_processor.target_sr)
        
        # Transcribe
        result = model.transcribe(temp_file_path, task="translate")
        
        # Cleanup
        os.unlink(temp_file_path)
        
        return {
            'success': True,
            'transcript': result['text'],
            'speakers_detected': 0,
            'error_message': ''
        }
        
    except Exception as e:
        # Cleanup temp file if it exists
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except:
                pass  # Ignore cleanup errors
                
        return {
            'success': False,
            'transcript': '',
            'speakers_detected': 0,
            'error_message': str(e)
        }

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'models_loaded': all([
            audio_processor is not None,
            voice_manager is not None,
            text_preprocessor is not None,
            text_summarizer is not None,
            pdf_generator is not None,
            summary_post_processor is not None
        ]),
        'ai_refining_available': GITHUB_TOKEN is not None
    })

@app.route('/api/upload-audio', methods=['POST'])
def upload_audio():
    try:
        logger.info("=== AUDIO UPLOAD DEBUG START ===")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request content type: {request.content_type}")
        logger.info(f"Request files keys: {list(request.files.keys())}")
        logger.info(f"Request form keys: {list(request.form.keys())}")
        
        # Check if audio file exists in request
        if 'audio' not in request.files:
            logger.error("No 'audio' key in request.files")
            logger.error(f"Available keys: {list(request.files.keys())}")
            return jsonify({'error': 'No audio file provided', 'debug_info': {'files_keys': list(request.files.keys())}}), 400
        
        file = request.files['audio']
        logger.info(f"File object: {file}")
        logger.info(f"File filename: {file.filename}")
        logger.info(f"File content type: {file.content_type}")
        
        # Check if file is empty or invalid
        if not file or not file.filename:
            logger.error(f"Invalid file object - file: {file}, filename: {getattr(file, 'filename', 'NO_FILENAME')}")
            return jsonify({'error': 'Invalid or empty audio file'}), 400
        
        # Log processing options
        form_data = dict(request.form)
        logger.info(f"Form data received: {form_data}")
        
        # Get processing options with default values and validation
        try:
            enable_diarization = request.form.get('enable_diarization', 'true').lower() == 'true'
            enable_speaker_recognition = request.form.get('enable_speaker_recognition', 'true').lower() == 'true'
            enable_ai_refining = request.form.get('enable_ai_refining', 'true').lower() == 'true'
            whisper_model = request.form.get('whisper_model', 'small')
            min_speakers = int(request.form.get('min_speakers', 2))
            max_speakers = int(request.form.get('max_speakers', 8))
            
            logger.info(f"Parsed options - diarization: {enable_diarization}, speaker_rec: {enable_speaker_recognition}, ai_refining: {enable_ai_refining}")
            logger.info(f"Model: {whisper_model}, speakers: {min_speakers}-{max_speakers}")
            
        except Exception as parse_error:
            logger.error(f"Error parsing form options: {str(parse_error)}")
            return jsonify({'error': f'Invalid form parameters: {str(parse_error)}'}), 400

        # Save uploaded file with enhanced error handling
        try:
            filename = secure_filename(file.filename)
            if not filename:
                # Generate filename if secure_filename returns empty
                filename = f"audio_{int(time.time())}.wav"
                logger.warning(f"Generated filename: {filename}")
            
            temp_path = os.path.join(tempfile.gettempdir(), filename)
            logger.info(f"Attempting to save file to: {temp_path}")
            
            # Check if file stream is at the beginning
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)     # Seek back to beginning
            
            logger.info(f"File size: {file_size} bytes")
            
            if file_size == 0:
                logger.error("File is empty (0 bytes)")
                return jsonify({'error': 'Uploaded file is empty'}), 400
            
            file.save(temp_path)
            actual_size = os.path.getsize(temp_path) if os.path.exists(temp_path) else 0
            logger.info(f"File saved successfully. Actual size on disk: {actual_size} bytes")
            
        except Exception as save_error:
            logger.error(f"Failed to save uploaded file: {str(save_error)}")
            logger.error(f"Error type: {type(save_error).__name__}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({'error': f'Failed to save uploaded file: {str(save_error)}'}), 500

        # Verify file exists and is readable
        if not os.path.exists(temp_path):
            logger.error(f"File does not exist after save: {temp_path}")
            return jsonify({'error': 'Failed to save file - file not found after save'}), 500
        
        # Check file permissions and size
        try:
            file_stats = os.stat(temp_path)
            logger.info(f"File stats - size: {file_stats.st_size}, permissions: {oct(file_stats.st_mode)}")
            
            # Try to read a small portion to verify accessibility
            with open(temp_path, 'rb') as test_file:
                test_read = test_file.read(1024)
                logger.info(f"File is readable, read {len(test_read)} bytes for test")
                
        except Exception as verify_error:
            logger.error(f"File verification failed: {str(verify_error)}")
            return jsonify({'error': f'File verification failed: {str(verify_error)}'}), 500

        try:
            # Verify audio processor is initialized
            if audio_processor is None:
                logger.error("Audio processor is not initialized")
                return jsonify({'error': 'Audio processor not available'}), 500
            
            logger.info("Getting audio duration...")
            # Get audio duration with error handling
            try:
                duration = audio_processor.get_audio_duration(temp_path)
                formatted_duration = audio_processor.format_duration(duration)
                logger.info(f"Audio duration: {duration}s ({formatted_duration})")
            except Exception as duration_error:
                logger.error(f"Failed to get audio duration: {str(duration_error)}")
                # Continue processing even if duration fails
                duration = 0
                formatted_duration = "Unknown"
            
            # Process audio based on diarization setting
            if enable_diarization:
                logger.info("Processing with speaker diarization enabled")
                try:
                    result = transcribe_with_diarization(
                        audio_file_path=temp_path,
                        whisper_model=whisper_model,
                        min_speakers=min_speakers,
                        max_speakers=max_speakers,
                        voice_manager=voice_manager if enable_speaker_recognition else None
                    )
                    logger.info(f"Diarization result success: {result.get('success', False)}")
                except Exception as diarization_error:
                    logger.error(f"Diarization failed: {str(diarization_error)}")
                    logger.error(f"Diarization traceback: {traceback.format_exc()}")
                    result = {
                        'success': False,
                        'transcript': '',
                        'speakers_detected': 0,
                        'error_message': f'Diarization failed: {str(diarization_error)}'
                    }
            else:
                logger.info("Processing with simple transcription (no diarization)")
                try:
                    result = simple_transcription_pipeline(
                        audio_file_path=temp_path,
                        whisper_model=whisper_model
                    )
                    logger.info(f"Simple transcription result success: {result.get('success', False)}")
                except Exception as transcription_error:
                    logger.error(f"Simple transcription failed: {str(transcription_error)}")
                    logger.error(f"Transcription traceback: {traceback.format_exc()}")
                    result = {
                        'success': False,
                        'transcript': '',
                        'speakers_detected': 0,
                        'error_message': f'Transcription failed: {str(transcription_error)}'
                    }
            
            if not result['success']:
                logger.error(f"Processing failed: {result['error_message']}")
                return jsonify({'error': result['error_message']}), 500
            
            logger.info(f"Transcription successful, transcript length: {len(result.get('transcript', ''))}")

            # Continue with text processing...
            logger.info("Starting text preprocessing...")
            processed_text = text_preprocessor.preprocess(result['transcript'])
            
            # Get name standardization report
            name_report = text_preprocessor.get_name_standardization_report()
            logger.info(f"Name standardization applied: {len(name_report) > 0 if name_report else False}")
            
            # Generate summary with improved chunking
            logger.info("Starting summarization process...")
            if enable_diarization and result['transcript']:
                try:
                    from models.speaker_aware_chunker import SpeakerAwareChunker
                    chunker = SpeakerAwareChunker(chunk_size=512, chunk_overlap=50)
                    chunks = chunker.split_into_speaker_chunks(processed_text)
                    logger.info("Using speaker-aware chunking")
                except ImportError:
                    logger.warning("SpeakerAwareChunker not available, using default chunking")
                    chunks = text_preprocessor.split_into_chunks(processed_text)
            else:
                chunks = text_preprocessor.split_into_chunks(processed_text)
            
            logger.info(f"Created {len(chunks)} chunks")
            
            # Remove redundancies
            unique_chunks = text_summarizer.remove_redundancies(chunks)
            logger.info(f"After removing redundancies: {len(unique_chunks)} unique chunks")
            
            # Create progress bar placeholder
            class DummyProgressBar:
                def update(self, n=1):
                    pass
            
            progress_bar = DummyProgressBar()
            
            # Process chunks
            grouped_chunks = text_summarizer.process_chunks(unique_chunks, progress_bar)
            logger.info(f"Processed into {len(grouped_chunks)} grouped chunks")
            
            # Format markdown
            markdown_content = text_summarizer.format_markdown(
                grouped_chunks,
                meeting_duration=formatted_duration,
                name_standardization_report=name_report if name_report else None
            )
            logger.info(f"Generated markdown content, length: {len(markdown_content)}")

            # Refine summary with AI if enabled and token is available
            final_summary = markdown_content
            refined_with_ai = False
            
            if enable_ai_refining and GITHUB_TOKEN:
                logger.info("Refining summary with AI...")
                try:
                    refined_summary = refine_summary_with_ai(markdown_content, enable_diarization)
                    if refined_summary != markdown_content:
                        final_summary = refined_summary
                        refined_with_ai = True
                        logger.info("AI refinement completed successfully")
                    else:
                        logger.info("AI refinement returned unchanged content")
                except Exception as ai_error:
                    logger.error(f"AI refinement failed: {str(ai_error)}")
                    # Continue with original summary
            else:
                logger.info(f"AI refinement skipped - enabled: {enable_ai_refining}, token available: {GITHUB_TOKEN is not None}")

            response_data = {
                'success': True,
                'transcript': result['transcript'],
                'summary': final_summary,
                'original_summary': markdown_content if refined_with_ai else None,
                'speakers_detected': result.get('speakers_detected', 0),
                'duration': formatted_duration,
                'processing_stats': {
                    'original_chunks': len(chunks),
                    'unique_chunks': len(unique_chunks),
                    'topics_identified': len(grouped_chunks),
                    'ai_refined': refined_with_ai,
                    'ai_refining_available': GITHUB_TOKEN is not None
                },
                'name_standardization': {
                    'applied': len(name_report) > 0 if name_report else False,
                    'report': name_report if name_report else []
                }
            }
            
            logger.info("=== AUDIO UPLOAD SUCCESS ===")
            return jsonify(response_data)

        except Exception as processing_error:
            logger.error(f"Error during audio processing: {str(processing_error)}")
            logger.error(f"Processing error traceback: {traceback.format_exc()}")
            return jsonify({'error': f'Processing error: {str(processing_error)}'}), 500
        
        finally:
            # Cleanup temp file
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    logger.info("Temp file cleaned up successfully")
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup temp file: {str(cleanup_error)}")
            
            # Clear GPU cache if using CUDA
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    except Exception as outer_error:
        logger.error(f"=== OUTER EXCEPTION IN UPLOAD_AUDIO ===")
        logger.error(f"Outer error: {str(outer_error)}")
        logger.error(f"Outer error type: {type(outer_error).__name__}")
        logger.error(f"Outer traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Internal server error: {str(outer_error)}'}), 500

@app.route('/api/refine-summary', methods=['POST'])
def refine_summary():
    """Separate endpoint to refine an existing summary"""
    try:
        data = request.get_json()
        markdown_content = data.get('markdown_content', '')
        enable_diarization = data.get('enable_diarization', True)
        
        if not markdown_content:
            return jsonify({'error': 'No content provided'}), 400
        
        if not GITHUB_TOKEN:
            return jsonify({'error': 'AI refining not available - no token configured'}), 400
        
        refined_summary = refine_summary_with_ai(markdown_content, enable_diarization)
        
        return jsonify({
            'success': True,
            'original_summary': markdown_content,
            'refined_summary': refined_summary,
            'was_refined': refined_summary != markdown_content
        })
        
    except Exception as e:
        logger.error(f"Error refining summary: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload-voice-sample', methods=['POST'])
def upload_voice_sample():
    try:
        if 'voice_sample' not in request.files:
            return jsonify({'error': 'No voice sample provided'}), 400
        
        file = request.files['voice_sample']
        speaker_name = request.form.get('speaker_name')
        
        if not speaker_name:
            # Extract from filename
            speaker_name = Path(file.filename).stem.title()
        
        # Save and process voice sample
        filename = secure_filename(file.filename)
        temp_path = os.path.join(tempfile.gettempdir(), filename)
        file.save(temp_path)
        
        try:
            # Process voice sample
            embedding = voice_manager.process_voice_sample_segments(temp_path, speaker_name)
            
            if embedding is not None:
                success = voice_manager.add_uploaded_voice_sample(speaker_name, embedding)
                
                if success:
                    return jsonify({
                        'success': True,
                        'speaker_name': speaker_name,
                        'message': f'Voice sample for {speaker_name} added successfully'
                    })
                else:
                    return jsonify({'error': 'Failed to add voice sample'}), 500
            else:
                return jsonify({'error': 'Failed to process voice sample'}), 500
                
        finally:
            # Always cleanup temp file
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup voice sample temp file: {str(cleanup_error)}")
            
    except Exception as e:
        logger.error(f"Error uploading voice sample: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/speakers', methods=['GET'])
def get_speakers():
    try:
        return jsonify({
            'preloaded_speakers': voice_manager.get_preloaded_speaker_names(),
            'uploaded_speakers': voice_manager.get_uploaded_speaker_names(),
            'active_speakers': voice_manager.get_speaker_names()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/speakers/select', methods=['POST'])
def select_speakers():
    try:
        data = request.get_json()
        selected_speakers = data.get('selected_speakers', [])
        
        voice_manager.update_selected_speakers(selected_speakers)
        
        return jsonify({
            'success': True,
            'active_speakers': voice_manager.get_speaker_names()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-pdf', methods=['POST'])
def download_pdf():
    try:
        data = request.get_json()
        markdown_content = data.get('markdown_content', '')
        
        if not markdown_content:
            return jsonify({'error': 'No content provided'}), 400
        
        # Use the updated PDF generation method
        pdf_bytes = pdf_generator.markdown_to_pdf(markdown_content)
        
        # Save to temporary file
        temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_pdf.write(pdf_bytes)
        temp_pdf.close()
        
        return send_file(
            temp_pdf.name,
            as_attachment=True,
            download_name='meeting_summary.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        # Cleanup temp PDF file
        try:
            if 'temp_pdf' in locals() and os.path.exists(temp_pdf.name):
                os.remove(temp_pdf.name)
        except Exception as cleanup_error:
            logger.error(f"Failed to cleanup PDF temp file: {str(cleanup_error)}")

@app.route('/api/processing-config', methods=['GET', 'POST'])
def handle_processing_config():
    """Handle getting and setting preprocessing configuration"""
    try:
        if request.method == 'GET':
            # Return current configuration
            config = text_preprocessor.config
            return jsonify({
                'remove_timestamps': config.remove_timestamps,
                'remove_fillers': config.remove_fillers,
                'fix_contractions': config.fix_contractions,
                'remove_duplicates': config.remove_duplicates,
                'fix_punctuation': config.fix_punctuation,
                'segment_sentences': config.segment_sentences,
                'remove_stopwords': config.remove_stopwords,
                'chunk_size': config.chunk_size,
                'chunk_overlap': config.chunk_overlap
            })
        
        elif request.method == 'POST':
            # Update configuration
            data = request.get_json()
            
            # Create new config with updated values
            new_config = PreprocessingConfig(
                remove_timestamps=data.get('remove_timestamps', True),
                remove_fillers=data.get('remove_fillers', True),
                fix_contractions=data.get('fix_contractions', True),
                remove_duplicates=data.get('remove_duplicates', True),
                fix_punctuation=data.get('fix_punctuation', True),
                segment_sentences=data.get('segment_sentences', True),
                remove_stopwords=data.get('remove_stopwords', False),
                chunk_size=data.get('chunk_size', 512),
                chunk_overlap=data.get('chunk_overlap', 50)
            )
            
            # Update the preprocessor config
            text_preprocessor.config = new_config
            
            return jsonify({
                'success': True,
                'message': 'Configuration updated successfully'
            })
            
    except Exception as e:
        logger.error(f"Error handling processing config: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    if initialize_models():
        app.run(host='0.0.0.0', port=5328, debug=True)
    else:
        logger.error("Failed to initialize models. Exiting.")
        exit(1)