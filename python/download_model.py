from huggingface_hub import snapshot_download

# Replace 'pyannote/speaker-diarization-3.1' with the appropriate model ID
model_id = 'pyannote/speaker-diarization-3.1'
local_dir = './pyannote_speaker_diarization_3.1'

# Your Hugging Face access token
token = ''

# Download the model and save it to the specified directory
snapshot_download(repo_id=model_id, cache_dir=local_dir, use_auth_token=token)
