import os
import json
from pathlib import Path
from typing import Dict, Optional

from .config import SURVEY_JSON_PATH, PROJECT_ROOT


def load_survey_mapping() -> Dict:
    """Load survey mapping configuration from JSON file."""
    survey_mapping = {}
    mapping_path = Path(PROJECT_ROOT) / "data" / "surveys" / "survey_mapping.json"
    
    if os.path.exists(mapping_path):
        try:
            with open(mapping_path, "r", encoding="utf-8") as f:
                survey_mapping = json.load(f)
        except:
            pass
    
    return survey_mapping


def get_survey_for_time(video_time: str, survey_mapping: Dict) -> str:
    """Return the selected survey file based on video time."""
    time_points = survey_mapping.get('time_points', [])
    selected_survey = survey_mapping.get('default_survey', 'questions.json')
    
    for point in sorted(time_points, key=lambda x: x['time'], reverse=True):
        if point['time'] <= video_time:
            selected_survey = point.get('survey_file', 'questions.json')
            break
    
    return selected_survey


def load_survey_data(survey_file: str) -> Dict:
    """Load survey data from the specified file."""
    survey_path = Path(PROJECT_ROOT) / "data" / "surveys" / survey_file
    video_survey_data = {}
    
    if os.path.exists(survey_path):
        try:
            with open(survey_path, "r", encoding="utf-8") as f:
                video_survey_data = json.load(f)
            video_survey_data["_survey_file"] = survey_file
        except:
            pass
    else:
        # Fallback to default survey path
        if os.path.exists(SURVEY_JSON_PATH):
            try:
                with open(SURVEY_JSON_PATH, "r", encoding="utf-8") as f:
                    video_survey_data = json.load(f)
            except:
                pass
    
    return video_survey_data