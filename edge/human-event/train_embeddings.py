import os
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
import librosa

# ===========================================================
# CONFIG
# ===========================================================

YAMNET_MODEL = "https://tfhub.dev/google/yamnet/1"

# datasets/
#   positive/
#       cough/*.wav
#       sneeze/*.wav
#       snore/*.wav
#   negative/*.wav
DATASET_DIR = "./datasets"

OUTPUT_X = "X.npy"
OUTPUT_Y = "y.npy"

POSITIVE_LABEL = 1
NEGATIVE_LABEL = 0


# ===========================================================
# LOAD YAMNET
# ===========================================================

print("Loading YAMNet...")
yamnet = hub.load(YAMNET_MODEL)
print("YAMNet loaded.")


# ===========================================================
# HELPER: Extract embedding from WAV
# ===========================================================

def extract_embedding(path: str) -> np.ndarray:
    """Load WAV → Resample → YAMNet → 1024-dim average embedding."""
    try:
        waveform, sr = librosa.load(path, sr=16000, mono=True)
    except Exception as e:
        print(f"[WARN] Failed to load {path}: {e}")
        return None

    try:
        scores, embeddings, spectrogram = yamnet(waveform)
        emb = embeddings.numpy()
        return np.mean(emb, axis=0)  # 1024 vector
    except Exception as e:
        print(f"[WARN] Failed embedding extract for {path}: {e}")
        return None


# ===========================================================
# MAIN: Build Dataset
# ===========================================================

def process_folder(folder_path: str, label: int, X_list, y_list):
    """Walk through folder and extract embeddings."""
    for root, _, files in os.walk(folder_path):
        for f in files:
            if not f.lower().endswith(".wav"):
                continue

            file_path = os.path.join(root, f)
            emb = extract_embedding(file_path)

            if emb is None:
                continue

            X_list.append(emb)
            y_list.append(label)

            print(f"[OK] {file_path} → emb.shape={emb.shape}, label={label}")


def main():
    X_list = []
    y_list = []

    # ---------------------------------------------------------
    # 1) Positive classes
    # ---------------------------------------------------------
    positive_dir = os.path.join(DATASET_DIR, "positive")
    if os.path.isdir(positive_dir):
        for cls in ["cough", "sneeze", "snore"]:
            folder = os.path.join(positive_dir, cls)
            if os.path.isdir(folder):
                print(f"\n[LOAD POSITIVE] {folder}")
                process_folder(folder, POSITIVE_LABEL, X_list, y_list)
    else:
        print("[WARN] No positive dataset found.")

    # ---------------------------------------------------------
    # 2) Negative class
    # ---------------------------------------------------------
    negative_dir = os.path.join(DATASET_DIR, "negative")
    if os.path.isdir(negative_dir):
        print(f"\n[LOAD NEGATIVE] {negative_dir}")
        process_folder(negative_dir, NEGATIVE_LABEL, X_list, y_list)
    else:
        print("[WARN] No negative dataset found.")

    # ---------------------------------------------------------
    # Save embedding matrix
    # ---------------------------------------------------------
    X = np.vstack(X_list)
    y = np.array(y_list)

    np.save(OUTPUT_X, X)
    np.save(OUTPUT_Y, y)

    print("\n==============================")
    print("Embedding Extraction Complete!")
    print(f"X shape: {X.shape}")
    print(f"y shape: {y.shape}")
    print(f"Saved: {OUTPUT_X}, {OUTPUT_Y}")
    print("==============================\n")


if __name__ == "__main__":
    main()