import json
import os
import threading
import time
import datetime
import requests
from pathlib import Path
from typing import List, Dict, Optional

from .notifier import send_notification_email
from .config import PROJECT_ROOT, RECIPIENT_EMAIL, REMINDER_CHECK_HOUR, REMINDER_CHECK_MINUTE


class SurveyReminder:
    """Handle survey completion checking and reminder notifications."""
    
    def __init__(self, check_hour: int, check_minute: int):
        """
        Initialize the survey reminder.
        
        Args:
            check_hour: Hour to check surveys (0-23)
            check_minute: Minute to check surveys (0-59)
        """
        self.check_hour = check_hour
        self.check_minute = check_minute
        self.data_file = PROJECT_ROOT / "data" / "pending_surveys.json"
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize data file if not exists
        if not self.data_file.exists():
            self._save_data([])
        
        # Start the scheduler
        self._start_scheduler()
    
    def _start_scheduler(self):
        """Start the daily check scheduler."""
        scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        scheduler_thread.start()
        print(f"Survey reminder scheduler started for {self.check_hour:02d}:{self.check_minute:02d} daily")
    
    def _scheduler_loop(self):
        """Check every minute if it's time to send reminders."""
        while True:
            now = datetime.datetime.now()
            
            # Check if it's the scheduled time
            if now.hour == self.check_hour and now.minute == self.check_minute:
                self.check_and_remind()
                # Sleep for 60 seconds to avoid multiple triggers
                time.sleep(60)
            else:
                # Check every 30 seconds
                time.sleep(30)
    
    def add_survey(self, video_name: str, url: str):
        """
        Add a new survey to track.
        
        Args:
            video_name: Name of the video file
            url: URL of the survey page
        """
        surveys = self._load_data()
        
        # Check if already exists
        for survey in surveys:
            if survey['url'] == url:
                return
        
        # Add new survey
        survey_data = {
            'video_name': video_name,
            'url': url,
            'created_at': datetime.datetime.now().isoformat(),
            'reminded_count': 0,
            'last_reminded': None
        }
        
        surveys.append(survey_data)
        self._save_data(surveys)
        print(f"Added survey to track: {video_name}")
    
    def check_and_remind(self):
        """Check all pending surveys and send reminder if needed."""
        print(f"\n=== Checking surveys at {datetime.datetime.now()} ===")
        
        surveys = self._load_data()
        if not surveys:
            print("No pending surveys to check")
            return
        
        pending_surveys = []
        completed_surveys = []
        
        # Check each survey
        for survey in surveys:
            if self._is_survey_completed(survey['url']):
                completed_surveys.append(survey)
                print(f"✓ Survey completed: {survey['video_name']}")
            else:
                pending_surveys.append(survey)
                print(f"✗ Survey pending: {survey['video_name']}")
        
        # Remove completed surveys
        remaining_surveys = [s for s in surveys if s not in completed_surveys]
        self._save_data(remaining_surveys)
        
        # Send reminder if there are pending surveys
        if pending_surveys:
            self._send_reminder_email(pending_surveys)
        
        print(f"=== Check complete: {len(completed_surveys)} completed, {len(pending_surveys)} pending ===\n")
    
    def _is_survey_completed(self, url: str) -> bool:
        """
        Check if a survey has been completed by visiting the URL.
        
        Args:
            url: The survey page URL
            
        Returns:
            True if survey is completed (page is blank), False otherwise
        """
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                content = response.text.strip()
                
                # Check various indicators of blank/destroyed page
                # 1. Very short content
                if len(content) < 200:
                    return True
                
                # 2. Missing key elements that should be in a survey page
                content_lower = content.lower()
                survey_indicators = ['video', 'survey', 'question', 'submit', 'form']
                
                # If none of these keywords exist, likely destroyed
                if not any(indicator in content_lower for indicator in survey_indicators):
                    return True
                
                # 3. Check for specific empty page patterns
                if '<body></body>' in content or '<body>\n</body>' in content:
                    return True
                
                return False
            else:
                # Non-200 status might mean completed
                return response.status_code == 404
                
        except Exception as e:
            print(f"Error checking survey {url}: {e}")
            # On error, assume not completed to avoid false positives
            return False
    
    def _send_reminder_email(self, pending_surveys: List[Dict]):
        """Send reminder email for pending surveys."""
        # Sort by creation time (oldest first)
        pending_surveys.sort(key=lambda x: x['created_at'])
        
        subject = f"[AVAS] Survey Reminder - {len(pending_surveys)} surveys pending"
        
        # Build email body
        lines = ["You have the following video surveys pending:\n"]
        
        for i, survey in enumerate(pending_surveys, 1):
            created_at = datetime.datetime.fromisoformat(survey['created_at'])
            age_days = (datetime.datetime.now() - created_at).days
            
            lines.append(f"{i}. Video: {survey['video_name']}")
            lines.append(f"   Link: {survey['url']}")
            lines.append(f"   Created: {age_days} day{'s' if age_days != 1 else ''} ago")
            
            if survey['reminded_count'] > 0:
                lines.append(f"   Reminders sent: {survey['reminded_count']}")
            
            lines.append("")  # Empty line between entries
        
        lines.append("Please complete the surveys as soon as possible. Thank you!")
        
        body = "\n".join(lines)
        
        # Send email
        try:
            send_notification_email(RECIPIENT_EMAIL, subject, body)
            print(f"Reminder email sent for {len(pending_surveys)} pending surveys")
        except Exception as e:
            print(f"Failed to send reminder email: {e}")
    
    def _load_data(self) -> List[Dict]:
        """Load survey data from file."""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading survey data: {e}")
            return []
    
    def _save_data(self, data: List[Dict]):
        """Save survey data to file."""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving survey data: {e}")
    
    def force_check(self):
        """Manually trigger a check (for testing)."""
        self.check_and_remind()
    
    def get_pending_surveys(self) -> List[Dict]:
        """Get list of all pending surveys."""
        return self._load_data()


# Global instance
_reminder_instance: Optional[SurveyReminder] = None


def get_reminder() -> SurveyReminder:
    """Get or create the global reminder instance."""
    global _reminder_instance
    if _reminder_instance is None:
        _reminder_instance = SurveyReminder(check_hour=REMINDER_CHECK_HOUR, check_minute=REMINDER_CHECK_MINUTE)
    return _reminder_instance


def add_survey_to_track(video_name: str, url: str):
    """Convenience function to add a survey to track."""
    reminder = get_reminder()
    reminder.add_survey(video_name, url)