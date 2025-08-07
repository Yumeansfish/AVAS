import os
import json
import time
from pathlib import Path
from typing import Dict, Set, List, Optional
from watchdog.events import FileCreatedEvent

from .config import PROJECT_ROOT


class OfflineHandler:
    
    def __init__(self, watch_dir: str):
        self.watch_dir = watch_dir
        self.state_file = PROJECT_ROOT / "data" / "directory_state.json"
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
    def check_and_process_offline_files(self, video_handler) -> List[str]:
        print("Checking for offline files...")
        
        last_state = self._load_state()
        current_files = self._scan_video_files()
        new_files = self._find_new_files(last_state, current_files)
        
        if new_files:
            print(f"Found {len(new_files)} offline files to process:")
            for filename in new_files:
                print(f"  - {filename}")
            
            self._trigger_processing(new_files, video_handler)
        else:
            print("No offline files found")
        
        self._save_state(current_files)
        
        return list(new_files)
    
    def update_state(self) -> None:
        current_files = self._scan_video_files()
        self._save_state(current_files)
        print("Directory state updated")
    
    def _scan_video_files(self) -> Dict[str, float]:
        video_files = {}
        video_extensions = ('.mov', '.avi', '.mp4')
        
        try:
            for filename in os.listdir(self.watch_dir):
                filepath = os.path.join(self.watch_dir, filename)
                
                if os.path.isfile(filepath) and filename.lower().endswith(video_extensions):
                    video_files[filename] = os.path.getmtime(filepath)
                    
        except Exception as e:
            print(f"Error scanning directory: {e}")
            
        return video_files
    
    def _find_new_files(self, last_state: Optional[Dict], current_files: Dict[str, float]) -> Set[str]:
        if not last_state or 'files' not in last_state:
            print("No previous state found, treating as first run")
            return set()
        
        last_files = set(last_state['files'].keys())
        current_filenames = set(current_files.keys())
        
        # Simply find files that exist now but didn't exist in last state
        new_files = current_filenames - last_files
        
        return new_files
    
    def _trigger_processing(self, filenames: Set[str], video_handler) -> None:
        for filename in filenames:
            filepath = os.path.join(self.watch_dir, filename)
            
            if not os.path.exists(filepath):
                print(f"File no longer exists: {filename}")
                continue
            
            event = FileCreatedEvent(filepath)
            
            print(f"Processing offline file: {filename}")
            video_handler.on_created(event)
            
            time.sleep(0.1)
    
    def _load_state(self) -> Optional[Dict]:
        if not self.state_file.exists():
            return None
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading state file: {e}")
            return None
    
    def _save_state(self, files: Dict[str, float]) -> None:
        state = {
            'files': files,
            'last_update': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        }
        
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving state file: {e}")
    
    def get_state_info(self) -> Optional[Dict]:
        state = self._load_state()
        if state:
            file_count = len(state.get('files', {}))
            last_update = state.get('last_update', 'Unknown')
            print(f"State info: {file_count} files tracked, last update: {last_update}")
        return state