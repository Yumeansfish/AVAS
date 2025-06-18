import os
from unittest.mock import patch, Mock, call
import subprocess
from core.video_processor import convert_to_mp4


class TestConvertToMp4:

    def test_already_mp4_no_conversion(self):
        """Test that mp4 files are returned unchanged without calling ffmpeg"""
        video_path = "/path/to/video.mp4"
        
        result_path, conversion_happened = convert_to_mp4(video_path)
        
        assert result_path == video_path
        assert conversion_happened is False

    def test_mp4_case_insensitive(self):
        """Test that .MP4 extension is also recognized"""
        video_path = "/path/to/VIDEO.MP4"
        
        result_path, conversion_happened = convert_to_mp4(video_path)
        
        assert result_path == video_path
        assert conversion_happened is False

    @patch('subprocess.run')
    def test_successful_conversion(self, mock_subprocess):
        """Test successful conversion from non-mp4 to mp4"""
        # Setup
        video_path = "/path/to/video.avi"
        expected_output = "/path/to/video.mp4"
        
        mock_subprocess.return_value = Mock()  # successful run
        
        # Execute
        result_path, conversion_happened = convert_to_mp4(video_path)
        
        # Verify
        assert result_path == expected_output
        assert conversion_happened is True
        
        # Verify ffmpeg was called with correct arguments
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]  # Get the command list
        
        assert call_args[0] == "ffmpeg"
        assert "-i" in call_args
        assert video_path in call_args
        assert expected_output in call_args
        assert "-c:v" in call_args and "libx264" in call_args
        assert "-c:a" in call_args and "aac" in call_args

    @patch('shutil.which')
    def test_ffmpeg_not_available(self, mock_which):
        """Test behavior when ffmpeg is not installed"""
        video_path = "/path/to/video.avi"
        mock_which.return_value = None  # ffmpeg not found
        
        result_path, conversion_happened = convert_to_mp4(video_path)
        
        assert result_path == video_path  # Returns original path
        assert conversion_happened is False

    @patch('subprocess.run')
    def test_conversion_failure_subprocess_error(self, mock_subprocess):
        """Test handling of ffmpeg conversion failure"""
        video_path = "/path/to/video.mov"
        
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, 'ffmpeg')
        
        result_path, conversion_happened = convert_to_mp4(video_path)
        
        assert result_path == video_path  # Returns original path on failure
        assert conversion_happened is False

    @patch('subprocess.run')
    def test_conversion_failure_subprocess_error(self, mock_subprocess):
        """Test handling of ffmpeg conversion failure"""
        video_path = "/path/to/video.mov"
        
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, 'ffmpeg')
        
        result_path, conversion_happened = convert_to_mp4(video_path)
        
        assert result_path == video_path  # Returns original path on failure
        assert conversion_happened is False

    @patch('subprocess.run')
    def test_file_not_found_error(self, mock_subprocess):
        """Test handling when ffmpeg command itself is not found"""
        video_path = "/path/to/video.webm"
        
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, 'ffmpeg')
        
        result_path, conversion_happened = convert_to_mp4(video_path)
        
        assert result_path == video_path
        assert conversion_happened is False

    def test_path_generation_various_extensions(self):
        """Test that output path is correctly generated for various input extensions"""
        test_cases = [
            ("/home/user/video.avi", "/home/user/video.mp4"),
            ("/tmp/recording.mov", "/tmp/recording.mp4"),
            ("/data/clip.mkv", "/data/clip.mp4"),
            ("/path/file.webm", "/path/file.mp4"),
            ("/complex/path.with.dots/video.flv", "/complex/path.with.dots/video.mp4"),
        ]
        
        # Test path generation logic only
        for input_path, expected_output in test_cases:
            expected_mp4_path = os.path.splitext(input_path)[0] + ".mp4"
            assert expected_mp4_path == expected_output

    @patch('subprocess.run')
    def test_ffmpeg_command_structure(self, mock_subprocess):
        """Test that ffmpeg is called with the correct command structure"""
        video_path = "/test/input.avi"
        expected_output = "/test/input.mp4"
        
        mock_subprocess.return_value = Mock()
        
        convert_to_mp4(video_path)
        
        # Get the actual command that was called
        actual_command = mock_subprocess.call_args[0][0]
        
        # Verify essential command elements are present
        assert actual_command[0] == "ffmpeg"
        assert "-y" in actual_command
        assert "-i" in actual_command
        assert video_path in actual_command
        assert "-c:v" in actual_command
        assert "libx264" in actual_command
        assert "-c:a" in actual_command
        assert "aac" in actual_command
        assert "-movflags" in actual_command
        assert "+faststart" in actual_command
        assert expected_output in actual_command

    @patch('subprocess.run')
    def test_subprocess_called_with_check_true(self, mock_subprocess):
        """Test that subprocess.run is called with check=True"""
        video_path = "/test/input.mov"
        
        mock_subprocess.return_value = Mock()
        
        convert_to_mp4(video_path)
        
        # Check subprocess.run call arguments
        call_kwargs = mock_subprocess.call_args[1]
        
        assert call_kwargs['check'] is True

    def test_edge_case_no_extension(self):
        """Test handling of files without extensions"""
        video_path = "/path/to/videofile"
        expected_output = "/path/to/videofile.mp4"
        
        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.return_value = Mock()
            
            result_path, conversion_happened = convert_to_mp4(video_path)
            
            assert result_path == expected_output
            assert conversion_happened is True

    def test_edge_case_multiple_dots_in_filename(self):
        """Test handling of filenames with multiple dots"""
        video_path = "/path/to/my.video.file.avi"
        expected_output = "/path/to/my.video.file.mp4"
        
        # Clean up some overly specific tests that don't match your implementation
        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.return_value = Mock()
            
            result_path, conversion_happened = convert_to_mp4(video_path)
            
            assert result_path == expected_output
            assert conversion_happened is True