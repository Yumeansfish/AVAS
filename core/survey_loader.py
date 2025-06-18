import os
import json
from pathlib import Path
from typing import Dict
from .config import SURVEY_JSON_PATH

def load_survey_data() -> Dict:
    """Load default survey data."""
    video_survey_data = {}
    if os.path.exists(SURVEY_JSON_PATH):
        try:
            with open(SURVEY_JSON_PATH, "r", encoding="utf-8") as f:
                video_survey_data = json.load(f)
            video_survey_data["_survey_file"] = "questions.json"
        except:
            pass
    return video_survey_data