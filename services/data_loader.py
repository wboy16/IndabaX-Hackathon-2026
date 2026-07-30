import pandas as pd
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Processed_Data")

def _load(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Could not find {path}. Make sure Processed_Data/ exists relative to the project root."
        )
    return pd.read_csv(path, low_memory=False)

all_cover = _load("cover.csv")
all_standing = _load("standing.csv")
all_quant = _load("quant.csv")
all_grazing = _load("grazing.csv")

def load_cover():
    return all_cover

def load_standing():
    return all_standing

def load_quant():
    return all_quant

def load_grazing():
    return all_grazing