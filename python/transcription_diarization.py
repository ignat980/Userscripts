import whisper
import torch
from pyannote.audio import Pipeline
import argparse
import os
import logging
from datetime import datetime
import time
import ffmpeg

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
    model = whisper.load_model("large").to(torch.device("cuda"))
    logger.info("Model loaded to GPU.")

    # Load audio and move it to GPU
    audio = whisper.load_audio(file_path)
    logger.info(f"Audio loaded. Shape: {audio.shape}")

    # Ensure audio is in correct format for GPU processing
    audio_tensor = torch.from_numpy(audio).to(torch.device("cuda"))
    logger.info("Audio moved to GPU.")

    # Check if model and data are on GPU
    if next(model.parameters()).is_cuda:
        logger.info("Model is on GPU.")
    else:
        logger.warning("Model is not on GPU.")

    logger.info("Transcribing audio...")
    result = model.transcribe(audio_tensor)
    transcription = result["text"]
    segments = result["segments"]
    logger.info("Transcription completed.")
    return transcription, segments

def convert_to_wav(input_file, output_file):
    logger.info(f"Converting {input_file} to {output_file}...")
    try:
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
            pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=token)
            pipeline.to(torch.device("cuda"))
            diarization = pipeline(file_path, num_speakers=num_speakers)
            logger.info("Diarization completed.")
            return diarization
        except Exception as e:
            logger.error(f"An error occurred during diarization attempt {i+1}: {e}")
            if i < retries - 1:
                logger.info("Retrying...")
                time.sleep(5)  # Wait for 5 seconds before retrying
            else:
                raise

def align_timestamps(transcription_segments, diarization_result):
    logger.info("Aligning transcription with diarization...")
    aligned_results = []

    for segment, _, label in diarization_result.itertracks(yield_label=True):
        start = segment.start
        end = segment.end
        transcribed_text = ""
        for seg in transcription_segments:
            if seg["start"] >= start and seg["end"] <= end:
                transcribed_text += seg["text"] + " "
        
        aligned_results.append({
            "speaker": label,
            "start": start,
            "end": end,
            "text": transcribed_text.strip()
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

    args = parser.parse_args()
    audio_file_path = args.filepath
    hf_token = args.token
    num_speakers = args.num_speakers

    check_gpu()

    # Step 1: Convert input file to wav format if it is mp4 and the wav file does not exist
    base_filename = os.path.basename(audio_file_path)
    file_extension = os.path.splitext(base_filename)[1].lower()
    if file_extension == ".mp4":
        wav_file_path = os.path.splitext(audio_file_path)[0] + ".wav"
        if not os.path.exists(wav_file_path):
            convert_to_wav(audio_file_path, wav_file_path)
        else:
            logger.info(f"WAV file already exists: {wav_file_path}")
    else:
        wav_file_path = audio_file_path

    # Step 2: Transcribe audio
    start_time = datetime.now()
    transcription, transcription_segments = transcribe_audio(wav_file_path)
    end_time = datetime.now()
    logger.info(f"Transcription took {end_time - start_time}")

    # Save transcription to prevent data loss
    transcription_file_path = os.path.splitext(base_filename)[0] + "_transcription.txt"
    with open(transcription_file_path, 'w', encoding='utf-8') as file:
        file.write(transcription)
    logger.info(f"Transcription saved to {transcription_file_path}")
    
    try:
        # Step 3: Diarize audio
        start_time = datetime.now()
        diarization_result = diarize_audio(wav_file_path, hf_token, num_speakers)
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
