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


from datetime import datetime
from typing import Dict, Optional

def get_survey_for_time(video_time: str, survey_mapping: Dict) -> Optional[str]:
    """
    Return the selected survey file based on video time and explicit intervals.
    Expects survey_mapping to have an 'intervals' list like:
      [
        {"start":"00:00","end":"09:00","survey_file":"questions.json"},
        {"start":"09:00","end":"11:00","survey_file":"test09.json"},
        …
      ]
    """
    intervals = survey_mapping.get("intervals", [])
    vt = datetime.strptime(video_time, "%H:%M").time()
    
    for iv in intervals:
        start = datetime.strptime(iv["start"], "%H:%M").time()
        end   = datetime.strptime(iv["end"],   "%H:%M").time()
        if start <= vt < end:
            return iv.get("survey_file")
    return None



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