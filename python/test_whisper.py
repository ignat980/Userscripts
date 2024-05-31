import torch
import whisper

# Verify PyTorch installation
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

# Verify Whisper installation and model loading
model = whisper.load_model("large")
print("Whisper model loaded successfully")

# Optionally, transcribe an example audio file
# result = model.transcribe("path/to/your/audio/file.wav")
# print(result["text"])