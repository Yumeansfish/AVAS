import pytest
import datetime
from core.video_metadata import extract_timestamp_from_filename, calculate_end_time


class TestExtractTimestampFromFilename:
    """Test extract_timestamp_from_filename function"""
    
    # standard format tests
    def test_colleague_format_standard(self):
        """Test colleague's standard YYYY-MM-DD$HH-MM-SS-ffffff format"""
        filename = "video_2024-03-15$14-30-45-123456.mov"
        iso_ts, video_time = extract_timestamp_from_filename(filename)
        
        assert iso_ts == "2024-03-15T14:30:45.123456"
        assert video_time == "14:30"
    
    def test_colleague_format_boundary_times(self):
        """Test colleague's format with boundary time values"""
        # Midnight
        filename = "capture_2024-03-15$00-00-00-000000.avi"
        iso_ts, video_time = extract_timestamp_from_filename(filename)
        assert iso_ts == "2024-03-15T00:00:00.000000"
        assert video_time == "00:00"
        
        # Late night
        filename = "recording_2024-03-15$23-59-59-999999.mp4"
        iso_ts, video_time = extract_timestamp_from_filename(filename)
        assert iso_ts == "2024-03-15T23:59:59.999999"
        assert video_time == "23:59"
    
    def test_colleague_format_with_complex_filename(self):
        """Test colleague's format in complex filename"""
        filename = "camera1_front_2024-03-15$15-45-55-995201_backup.mp4"
        iso_ts, video_time = extract_timestamp_from_filename(filename)
        
        assert iso_ts == "2024-03-15T15:45:55.995201"
        assert video_time == "15:45"
    
    # fallback tests
    def test_format_t_with_microseconds(self):
        """Test YYYY-MM-DDTHH-MM-SS-ffffff format (fallback when $ not found)"""
        filename = "video_2024-03-15T14-30-45-123456.mov"
        iso_ts, video_time = extract_timestamp_from_filename(filename)
        
        assert iso_ts == "2024-03-15T14:30:45.123456"
        assert video_time == "14:30"
    
    def test_format_t_without_microseconds(self):
        """Test YYYY-MM-DDTHH-MM-SS format"""
        filename = "recording_2024-03-15T14-30-45.mp4"
        iso_ts, video_time = extract_timestamp_from_filename(filename)
        
        assert iso_ts == "2024-03-15T14:30:45.000000"
        assert video_time == "14:30"
    
    def test_format_t_short_microseconds(self):
        """Test microseconds less than 6 digits"""
        filename = "test_2024-03-15T14-30-45-123.mp4"
        iso_ts, video_time = extract_timestamp_from_filename(filename)
        
        assert iso_ts == "2024-03-15T14:30:45.123000"
        assert video_time == "14:30"
    
    def test_priority_order(self):
        """Test that $ format takes priority over T format"""
        # This hypothetical filename has both formats - $ should win
        filename = "video_2024-03-15$10-20-30-111111_copy_2024-03-15T14-30-45.mp4"
        iso_ts, video_time = extract_timestamp_from_filename(filename)
        
        # Should match the $ format (first priority)
        assert iso_ts == "2024-03-15T10:20:30.111111"
        assert video_time == "10:20"
    
    def test_t_format_when_dollar_absent(self):
        """Test that T format works when $ format is not present"""
        filename = "video_2024-03-15T14-30-45-123456.mp4"  # Only T format
        iso_ts, video_time = extract_timestamp_from_filename(filename)
        
        assert iso_ts == "2024-03-15T14:30:45.123456"
        assert video_time == "14:30"
    
    def test_no_match_cases(self):
        """Test cases that should return None, None"""
        test_cases = [
            "random_video.mp4",
            "2024-03-15_14-30-45.mp4",  # underscore instead of T or $
            "video_2024/03/15T14-30-45.mp4",  # wrong date format
            "",  # empty string
            "just_text.mov",
            "2024-03-15$14-30-45.mp4",  # $ format missing microseconds
            "2024-03-15$14-30-45-12345.mp4",  # $ format with 5-digit microseconds
        ]
        
        for filename in test_cases:
            iso_ts, video_time = extract_timestamp_from_filename(filename)
            assert iso_ts is None, f"Expected None for {filename}, got {iso_ts}"
            assert video_time is None, f"Expected None for {filename}, got {video_time}"
    
    def test_multiple_timestamps_in_filename(self):
        """Test filename with multiple timestamp patterns - should match first $ format"""
        filename = "video_2024-03-15$10-20-30-555555_backup_2024-03-16$11-21-31-666666.mp4"
        iso_ts, video_time = extract_timestamp_from_filename(filename)
        
        # Should match the first $ timestamp
        assert iso_ts == "2024-03-15T10:20:30.555555"
        assert video_time == "10:20"
    
    def test_real_world_colleague_format(self):
        """Test real-world examples of colleague's format"""
        test_cases = [
            ("cam1_2024-12-25$09-15-30-123456.mp4", "2024-12-25T09:15:30.123456", "09:15"),
            ("front_door_2024-01-01$00-00-01-000001.avi", "2024-01-01T00:00:01.000001", "00:00"),
            ("recording_2024-06-15$18-45-22-987654.mov", "2024-06-15T18:45:22.987654", "18:45"),
        ]
        
        for filename, expected_iso, expected_time in test_cases:
            iso_ts, video_time = extract_timestamp_from_filename(filename)
            assert iso_ts == expected_iso, f"For {filename}: expected {expected_iso}, got {iso_ts}"
            assert video_time == expected_time, f"For {filename}: expected {expected_time}, got {video_time}"
    
    def test_leap_year_date(self):
        """Test leap year date"""
        filename = "video_2024-02-29T12-30-45.mp4"
        iso_ts, video_time = extract_timestamp_from_filename(filename)
        
        assert iso_ts == "2024-02-29T12:30:45.000000"
        assert video_time == "12:30"


class TestCalculateEndTime:
    """Test calculate_end_time function"""
    
    def test_with_duration(self):
        """Test end time calculation with valid duration"""
        iso_timestamp = "2024-03-15T14:30:45.123456"
        duration_seconds = 120.5  # 2 minutes 0.5 seconds
        
        end_time = calculate_end_time(iso_timestamp, duration_seconds)
        expected = "2024-03-15T14:32:45.623456"
        
        assert end_time == expected
    
    def test_with_zero_duration(self):
        """Test with zero duration"""
        iso_timestamp = "2024-03-15T14:30:45.000000"
        duration_seconds = 0.0
        
        end_time = calculate_end_time(iso_timestamp, duration_seconds)
        # Should still be the same time since duration is 0
        assert end_time == "2024-03-15T14:30:45"
    
    def test_with_none_duration(self):
        """Test with None duration - should default to 1 minute"""
        iso_timestamp = "2024-03-15T14:30:45.123456"
        duration_seconds = None
        
        end_time = calculate_end_time(iso_timestamp, duration_seconds)
        expected = "2024-03-15T14:31:45.123456"  # +1 minute
        
        assert end_time == expected
    
    def test_with_fractional_seconds(self):
        """Test with fractional seconds duration"""
        iso_timestamp = "2024-03-15T14:30:45.000000"
        duration_seconds = 30.75  # 30.75 seconds
        
        end_time = calculate_end_time(iso_timestamp, duration_seconds)
        expected = "2024-03-15T14:31:15.750000"
        
        assert end_time == expected
    
    def test_cross_hour_boundary(self):
        """Test duration that crosses hour boundary"""
        iso_timestamp = "2024-03-15T14:58:30.000000"
        duration_seconds = 3600  # 1 hour
        
        end_time = calculate_end_time(iso_timestamp, duration_seconds)
        expected = "2024-03-15T15:58:30"
        
        assert end_time == expected
    
    def test_cross_day_boundary(self):
        """Test duration that crosses day boundary"""
        iso_timestamp = "2024-03-15T23:30:00.000000"
        duration_seconds = 3600  # 1 hour
        
        end_time = calculate_end_time(iso_timestamp, duration_seconds)
        expected = "2024-03-16T00:30:00"  # Next day
        
        assert end_time == expected
    
    def test_large_duration(self):
        """Test with very large duration"""
        iso_timestamp = "2024-03-15T14:30:45.000000"
        duration_seconds = 86400 * 2  # 2 days
        
        end_time = calculate_end_time(iso_timestamp, duration_seconds)
        expected = "2024-03-17T14:30:45"
        
        assert end_time == expected
    
    def test_invalid_iso_timestamp(self):
        """Test with invalid ISO timestamp - should raise exception"""
        with pytest.raises(ValueError):
            calculate_end_time("invalid-timestamp", 60.0)
    
    def test_edge_case_microseconds(self):
        """Test that microseconds are preserved correctly"""
        iso_timestamp = "2024-03-15T14:30:45.999999"
        duration_seconds = 0.000001  # 1 microsecond
        
        end_time = calculate_end_time(iso_timestamp, duration_seconds)
        expected = "2024-03-15T14:30:46"  # Should roll over to next second
        
        assert end_time == expected

class TestIntegration:
    """Test integration between functions"""
    
    def test_extract_and_calculate_workflow(self):
        """Test typical workflow: extract timestamp then calculate end time"""
        filename = "video_2024-03-15T14-30-45-123456.mov"
        
        # Extract timestamp
        iso_ts, video_time = extract_timestamp_from_filename(filename)
        
        # Calculate end time
        end_time = calculate_end_time(iso_ts, 120.0)  # 2 minutes
        
        assert iso_ts == "2024-03-15T14:30:45.123456"
        assert video_time == "14:30"
        assert end_time == "2024-03-15T14:32:45.123456"
    
    def test_colleague_format_workflow(self):
        """Test typical workflow with colleague's $ format"""
        filename = "camera_2024-03-15$14-30-45-123456.mp4"
        
        # Extract timestamp  
        iso_ts, video_time = extract_timestamp_from_filename(filename)
        
        # Calculate end time
        end_time = calculate_end_time(iso_ts, 90.5)  # 1.5 minutes
        
        assert iso_ts == "2024-03-15T14:30:45.123456"
        assert video_time == "14:30"
        assert end_time == "2024-03-15T14:32:15.623456"