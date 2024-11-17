import whisper
import torch
from pyannote.audio import Pipeline
import argparse
import os
import logging
from datetime import datetime
import time
import ffmpeg
import numpy as np

# Configure logging to include timestamps
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def check_gpu():
    if torch.cuda.is_available():
        logger.info(f"GPU is available: {torch.cuda.get_device_name(0)}")
    else:
        logger.warning("GPU is not available. Using CPU instead.")

def transcribe_audio(file_path):
    logger.info("Starting transcription...")
    model = whisper.load_model("large-v3").to(torch.device("cuda"))
    logger.info("Model loaded to GPU.")

    # Load audio using Whisper's load_audio function
    audio = whisper.load_audio(file_path)
    logger.info(f"Audio loaded. Shape: {audio.shape}")

    
    # Move audio to GPU
    audio_tensor = torch.from_numpy(audio).to(torch.device("cuda"))
    logger.info("Audio moved to GPU.")

    # Transcribe audio
    logger.info("Transcribing audio...")
    result = model.transcribe(audio_tensor)
    transcription = result["text"]
    segments = result["segments"]
    logger.info("Transcription completed.")
    return transcription, segments

def transcribe_audio(file_path):
    logger.info("Starting transcription...")
    model = whisper.load_model("large-v3").to(torch.device("cuda"))
    logger.info("Model loaded to GPU.")

    # Transcribe audio from file path
    logger.info("Transcribing audio from file...")
    result = model.transcribe(
        file_path,
        temperature=0.2,
        best_of=3,
        beam_size=5,
        language="en",
        verbose=True,
        no_speech_threshold=0.3,  # Lowered from default
        logprob_threshold=-1.0,   # Allow low-confidence predictions
        condition_on_previous_text=False  # Prevent conditioning on previous text
    )

    transcription = result["text"]
    segments = result["segments"]
    logger.info("Transcription completed.")
    return transcription, segments

def convert_to_wav(input_file, output_file, downsample):
    logger.info(f"Converting {input_file} to {output_file}...")
    try:
        if downsample:
            # Use precise resampling without introducing artifacts
            (
                ffmpeg
                .input(input_file)
                .output(
                    output_file,
                    ac=1,  # Mono
                    ar=16000,  # 16kHz
                    af='aresample=resampler=soxr',
                    compression_level=0,  # Highest quality
                )
                .run(overwrite_output=True)
            )
        else:
            # Convert to WAV without changing channels or sample rate
            ffmpeg.input(input_file).output(output_file).run(overwrite_output=True)
        logger.info("Conversion completed.")
    except ffmpeg.Error as e:
        logger.error(f"An error occurred during conversion: {e}")
        raise

def diarize_audio(file_path, token, num_speakers):
    logger.info("Starting diarization...")
    retries = 3
    for i in range(retries):
        try:
            # Load the pretrained pipeline
            pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=token)
            # Print available parameters
            logger.info(f"Pipeline parameters: {pipeline.parameters()}")
            
            # Adjust chunking parameters
            pipeline.segmentation.duration = 30.0  # Chunk duration in seconds
            pipeline.segmentation.step = 5.0       # Step size in seconds (overlap)

            # Move pipeline to GPU
            pipeline.to(torch.device("cuda"))

            # Run diarization
            diarization = pipeline(file_path, num_speakers=num_speakers)

            logger.info("Diarization completed.")
            return diarization

        except Exception as e:
            logger.error(f"An error occurred during diarization attempt {i+1}: {e}")
            if i < retries - 1:
                logger.info("Retrying...")
                time.sleep(5)  # Wait before retrying
            else:
                raise
from pyannote.core import Segment

def align_timestamps(transcription_segments, diarization_result):
    logger.info("Aligning transcription with diarization...")
    aligned_results = []

    for t_segment in transcription_segments:
        t_start = t_segment['start']
        t_end = t_segment['end']
        t_text = t_segment['text'].strip()
        t_segment_obj = Segment(t_start, t_end)

        # Find overlapping diarization segments
        overlapping_speakers = []
        for track in diarization_result.itertracks(yield_label=True):
            d_segment, _, speaker = track
            if d_segment.intersects(t_segment_obj):
                # Calculate overlap duration
                overlap = d_segment & t_segment_obj
                overlapping_speakers.append((overlap.duration, speaker))

        if overlapping_speakers:
            # Choose the speaker with the longest overlap duration
            selected_speaker = max(overlapping_speakers, key=lambda x: x[0])[1]
        else:
            selected_speaker = "Unknown"

        aligned_results.append({
            'start': t_start,
            'end': t_end,
            'speaker': selected_speaker,
            'text': t_text
        })

    logger.info("Alignment completed.")
    return aligned_results

def save_results_to_file(transcription, aligned_results, output_file_path):
    logger.info(f"Saving results to {output_file_path}...")
    with open(output_file_path, 'w', encoding='utf-8') as file:
        file.write("Transcription:\n")
        file.write(transcription + "\n\n")
        file.write("Speaker Diarization:\n")
        for result in aligned_results:
            file.write(f"Speaker {result['speaker']} from {result['start']} to {result['end']}: {result['text']}\n")
    logger.info("Results saved.")

def main():
    parser = argparse.ArgumentParser(description="Transcribe audio and identify speakers.")
    parser.add_argument("filepath", type=str, help="Path to the audio file")
    parser.add_argument("token", type=str, help="Hugging Face access token")
    parser.add_argument("num_speakers", type=int, help="Number of speakers")
    parser.add_argument("--use_downsampled_audio", action="store_true", default=False, help="Use downsampled audio (16kHz mono) for transcription to improve speed")

    args = parser.parse_args()
    audio_file_path = args.filepath
    hf_token = args.token
    num_speakers = args.num_speakers
    use_downsampled_audio = args.use_downsampled_audio

    check_gpu()

    # Get the base filename and file extension
    base_filename = os.path.basename(audio_file_path)
    file_root, file_extension = os.path.splitext(audio_file_path)
    file_extension = file_extension.lower()

    # Paths for the audio files
    transcription_audio_path = audio_file_path  # Default to original file
    diarization_audio_path = file_root + "_diarization.wav"

    # Step 1: Convert video file to audio WAV file if necessary
    if file_extension in [".mp4", ".mkv", ".avi", ".mov"]:
        logger.info(f"Input file is a video. Extracting audio to WAV.")
        audio_wav_path = file_root + ".wav"
        if not os.path.exists(audio_wav_path):
            convert_to_wav(audio_file_path, audio_wav_path, downsample=False)
        else:
            logger.info(f"WAV file already exists: {audio_wav_path}")
        transcription_audio_path = audio_wav_path
    else:
        # If the file is an audio file but not WAV, convert to WAV without downsampling
        if file_extension != ".wav":
            logger.info(f"Converting {audio_file_path} to WAV format without downsampling.")
            audio_wav_path = file_root + ".wav"
            if not os.path.exists(audio_wav_path):
                convert_to_wav(audio_file_path, audio_wav_path, downsample=False)
            else:
                logger.info(f"WAV file already exists: {audio_wav_path}")
            transcription_audio_path = audio_wav_path

    # Prepare the downsampled audio file for diarization
    if not os.path.exists(diarization_audio_path):
        convert_to_wav(transcription_audio_path, diarization_audio_path, downsample=True)
    else:
        logger.info(f"Diarization WAV file already exists: {diarization_audio_path}")

    # If the user wants to use downsampled audio for transcription
    if use_downsampled_audio:
        transcription_audio_path = diarization_audio_path

    try:
        # Step 2: Transcribe audio
        start_time = datetime.now()
        transcription, transcription_segments = transcribe_audio(transcription_audio_path)
        end_time = datetime.now()
        logger.info(f"Transcription took {end_time - start_time}")

        # Save transcription to prevent work loss
        transcription_file_path = os.path.splitext(base_filename)[0] + "_transcription.txt"
        with open(transcription_file_path, 'w', encoding='utf-8') as file:
            file.write(transcription)
        logger.info(f"Transcription saved to {transcription_file_path}")

        # Step 3: Diarize audio
        start_time = datetime.now()
        diarization_result = diarize_audio(diarization_audio_path, hf_token, num_speakers)
        end_time = datetime.now()
        logger.info(f"Diarization took {end_time - start_time}")
        
        # Step 4: Align transcription with diarization
        start_time = datetime.now()
        aligned_results = align_timestamps(transcription_segments, diarization_result)
        end_time = datetime.now()
        logger.info(f"Alignment took {end_time - start_time}")
        
        # Step 5: Save results to a .txt file
        output_file_path = os.path.splitext(base_filename)[0] + "_aligned_transcription.txt"
        save_results_to_file(transcription, aligned_results, output_file_path)
        logger.info(f"Results saved to {output_file_path}")
    
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        logger.info("Intermediate results have been saved.")

if __name__ == "__main__":
    main()
