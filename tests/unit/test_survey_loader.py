import unittest
import json
import os
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock, PropertyMock
from datetime import datetime
import tempfile
import shutil

# Import the functions to test
from core.survey_loader import load_survey_mapping, get_survey_for_time, load_survey_data


class TestSurveyLoader(unittest.TestCase):
    """Test cases for survey_loader module."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Since intervals feature is deprecated, using simple mapping
        self.test_mapping = {
            "intervals": [
                {"start": "00:00", "end": "23:59", "survey_file": "questions.json"}
            ]
        }
        
        self.test_survey_data = {
            "title": "Test Survey",
            "questions": [
                {"id": 1, "text": "Question 1"},
                {"id": 2, "text": "Question 2"}
            ]
        }
    
    @patch('core.survey_loader.PROJECT_ROOT', '/mock/project/root')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_survey_mapping_success(self, mock_file, mock_exists):
        """Test successful loading of survey mapping."""
        # Setup
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(self.test_mapping)
        
        # Execute
        with patch('json.load', return_value=self.test_mapping):
            result = load_survey_mapping()
        
        # Assert
        self.assertEqual(result, self.test_mapping)
        mock_exists.assert_called_once()
        expected_path = Path('/mock/project/root') / "data" / "surveys" / "survey_mapping.json"
        mock_exists.assert_called_with(expected_path)
    
    @patch('core.survey_loader.PROJECT_ROOT', '/mock/project/root')
    @patch('os.path.exists')
    def test_load_survey_mapping_file_not_exists(self, mock_exists):
        """Test loading survey mapping when file doesn't exist."""
        # Setup
        mock_exists.return_value = False
        
        # Execute
        result = load_survey_mapping()
        
        # Assert
        self.assertEqual(result, {})
        mock_exists.assert_called_once()
    
    @patch('core.survey_loader.PROJECT_ROOT', '/mock/project/root')
    @patch('os.path.exists')
    @patch('builtins.open')
    def test_load_survey_mapping_read_error(self, mock_file, mock_exists):
        """Test loading survey mapping with read error."""
        # Setup
        mock_exists.return_value = True
        mock_file.side_effect = Exception("Read error")
        
        # Execute
        result = load_survey_mapping()
        
        # Assert
        self.assertEqual(result, {})
    
    def test_get_survey_for_time_basic(self):
        """Test getting survey for any time (since it's deprecated, always returns questions.json)."""
        result = get_survey_for_time("10:00", self.test_mapping)
        self.assertEqual(result, "questions.json")
    
    def test_get_survey_for_time_no_intervals(self):
        """Test getting survey when no intervals defined."""
        empty_mapping = {"intervals": []}
        result = get_survey_for_time("10:00", empty_mapping)
        self.assertIsNone(result)
    
    def test_get_survey_for_time_missing_intervals_key(self):
        """Test getting survey when intervals key is missing."""
        result = get_survey_for_time("10:00", {})
        self.assertIsNone(result)
    
    @patch('core.survey_loader.PROJECT_ROOT', '/mock/project/root')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_survey_data_success(self, mock_file, mock_exists):
        """Test successful loading of survey data."""
        # Setup
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(self.test_survey_data)
        
        # Execute
        with patch('json.load', return_value=self.test_survey_data):
            result = load_survey_data("test.json")
        
        # Assert
        self.assertEqual(result["title"], "Test Survey")
        self.assertEqual(result["_survey_file"], "test.json")
        self.assertEqual(len(result["questions"]), 2)
    
    @patch('core.survey_loader.PROJECT_ROOT', '/mock/project/root')
    @patch('core.survey_loader.SURVEY_JSON_PATH', '/mock/default/survey.json')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_survey_data_fallback_to_default(self, mock_file, mock_exists):
        """Test loading survey data falls back to default path."""
        # Setup
        mock_exists.side_effect = [False, True]  # First path doesn't exist, fallback does
        mock_file.return_value.read.return_value = json.dumps(self.test_survey_data)
        
        # Execute
        with patch('json.load', return_value=self.test_survey_data):
            result = load_survey_data("nonexistent.json")
        
        # Assert
        self.assertEqual(result["title"], "Test Survey")
        self.assertNotIn("_survey_file", result)  # Should not have this key for fallback
    
    @patch('core.survey_loader.PROJECT_ROOT', '/mock/project/root')
    @patch('os.path.exists')
    def test_load_survey_data_no_files_exist(self, mock_exists):
        """Test loading survey data when no files exist."""
        # Setup
        mock_exists.return_value = False
        
        # Execute
        result = load_survey_data("nonexistent.json")
        
        # Assert
        self.assertEqual(result, {})
    
    @patch('core.survey_loader.PROJECT_ROOT', '/mock/project/root')
    @patch('os.path.exists')
    @patch('builtins.open')
    def test_load_survey_data_read_error(self, mock_file, mock_exists):
        """Test loading survey data with read error."""
        # Setup
        mock_exists.return_value = True
        mock_file.side_effect = Exception("Read error")
        
        # Execute
        result = load_survey_data("error.json")
        
        # Assert
        self.assertEqual(result, {})
    
    def test_get_survey_for_time_invalid_format(self):
        """Test getting survey with invalid time format."""
        with self.assertRaises(ValueError):
            get_survey_for_time("25:00", self.test_mapping)
    
    def test_get_survey_for_time_malformed_interval(self):
        """Test getting survey with malformed interval data."""
        bad_mapping = {
            "intervals": [
                {"start": "00:00", "end": "23:59"}  # Missing survey_file
            ]
        }
        result = get_survey_for_time("05:00", bad_mapping)
        self.assertIsNone(result)


class TestSurveyLoaderIntegration(unittest.TestCase):
    """Integration tests for survey_loader module."""
    
    def setUp(self):
        """Set up test directory structure."""
        self.test_dir = tempfile.mkdtemp()
        self.surveys_dir = Path(self.test_dir) / "data" / "surveys"
        self.surveys_dir.mkdir(parents=True)
        
        # Create test files - simplified for deprecated feature
        self.mapping_data = {
            "intervals": [
                {"start": "00:00", "end": "23:59", "survey_file": "questions.json"}
            ]
        }
        
        self.questions_survey = {
            "title": "Default Survey",
            "questions": [{"id": 1, "text": "How are you?"}]
        }
        
        # Write test files
        with open(self.surveys_dir / "survey_mapping.json", "w") as f:
            json.dump(self.mapping_data, f)
        
        with open(self.surveys_dir / "questions.json", "w") as f:
            json.dump(self.questions_survey, f)
    
    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)
    
    @patch('core.survey_loader.PROJECT_ROOT')
    def test_full_workflow(self, mock_root):
        """Test the complete workflow of loading mapping and survey data."""
        mock_root.__str__.return_value = self.test_dir
        mock_root.__truediv__ = lambda self, other: Path(str(self)) / other
        
        # Since PROJECT_ROOT is used in Path(PROJECT_ROOT), we need to make it work with Path
        type(mock_root).return_value = PropertyMock(return_value=self.test_dir)
        
        # Actually, let's use a simpler approach
        with patch('core.survey_loader.PROJECT_ROOT', self.test_dir):
            # Load mapping
            mapping = load_survey_mapping()
            self.assertIn("intervals", mapping)
            
            # Get survey for any time (always returns questions.json now)
            survey_file = get_survey_for_time("08:00", mapping)
            self.assertEqual(survey_file, "questions.json")
            
            # Load survey data
            survey_data = load_survey_data(survey_file)
            self.assertEqual(survey_data["title"], "Default Survey")
            self.assertEqual(survey_data["_survey_file"], "questions.json")


if __name__ == '__main__':
    unittest.main()