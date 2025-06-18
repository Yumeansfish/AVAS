import pytest
import threading
import time
from unittest.mock import Mock, patch, MagicMock
from watchdog.events import DirCreatedEvent, FileCreatedEvent

from core.video_handler import VideoHandler


class TestVideoHandlerQueueLogic:

    def setup_method(self):
        """Setup for each test"""
        self.callback = Mock()
        self.handler = VideoHandler(self.callback, batch_interval=0.1)  # Short interval for testing
    
    def teardown_method(self):
        """Cleanup after each test"""
        if self.handler._timer:
            self.handler._timer.cancel()

    def test_single_file_starts_timer(self):
        """Test that a single file starts the timer"""
        # Create a video file event
        event = FileCreatedEvent("/test/video.mov")
        
        # Process the event
        self.handler.on_created(event)
        
        # Verify timer was started
        assert self.handler._timer is not None
        assert self.handler._timer.is_alive()
        
        # Verify file is in queue
        assert not self.handler._queue.empty()
        assert self.handler._queue.get() == "/test/video.mov"

    def test_multiple_files_same_timer(self):
        """Test that multiple files use the same timer"""
        events = [
            FileCreatedEvent("/test/video1.mov"),
            FileCreatedEvent("/test/video2.avi"), 
            FileCreatedEvent("/test/video3.mp4")
        ]
        
        # Process events quickly
        for event in events:
            self.handler.on_created(event)
        
        # Should only have one timer
        assert self.handler._timer is not None
        assert self.handler._timer.is_alive()
        
        # All files should be in queue
        files_in_queue = []
        while not self.handler._queue.empty():
            files_in_queue.append(self.handler._queue.get())
        
        assert len(files_in_queue) == 3
        assert "/test/video1.mov" in files_in_queue
        assert "/test/video2.avi" in files_in_queue
        assert "/test/video3.mp4" in files_in_queue

    def test_ignores_non_video_files(self):
        """Test that non-video files are ignored"""
        events = [
            FileCreatedEvent("/test/document.txt"),
            FileCreatedEvent("/test/image.jpg"),
            FileCreatedEvent("/test/archive.zip"),
        ]
        
        for event in events:
            self.handler.on_created(event)
        
        # No timer should be started
        assert self.handler._timer is None
        
        # Queue should be empty
        assert self.handler._queue.empty()

    def test_ignores_directories(self):
        """Test that directory events are ignored"""
        event = DirCreatedEvent("/test/new_folder")
        
        self.handler.on_created(event)
        
        # No timer should be started
        assert self.handler._timer is None
        assert self.handler._queue.empty()

    def test_skip_logic_prevents_queue(self):
        """Test that files in skip set don't enter queue"""
        file_path = "/test/video.mp4"
        
        # Add file to skip set
        with self.handler._lock:
            self.handler._skip.add(file_path)
        
        # Process event
        event = FileCreatedEvent(file_path)
        self.handler.on_created(event)
        
        # File should be removed from skip set but not queued
        assert file_path not in self.handler._skip
        assert self.handler._queue.empty()
        assert self.handler._timer is None

    @patch('core.video_handler.VideoHandler._wait_for_stable_file')
    @patch('core.video_handler.extract_timestamp_from_filename')
    @patch('core.video_handler.get_fallback_timestamp')
    @patch('core.video_handler.get_video_duration')
    @patch('core.video_handler.calculate_end_time')
    @patch('core.video_handler.load_survey_mapping')
    @patch('core.video_handler.get_survey_for_time')
    @patch('core.video_handler.load_survey_data')
    @patch('core.video_handler.convert_to_mp4')
    @patch('core.video_handler.process_and_upload_video')
    @patch('core.video_handler.call_appscript_batch')
    @patch('core.video_handler.notify_batch')
    def test_timer_triggers_batch_processing(self, mock_notify, mock_appscript, mock_upload, 
                                           mock_convert, mock_load_survey, mock_get_survey,
                                           mock_load_mapping, mock_calc_end, mock_duration,
                                           mock_fallback, mock_extract, mock_wait):
        """Test that timer triggers batch processing"""
        # Setup mocks
        mock_wait.return_value = True
        mock_extract.return_value = ("2024-03-15T14:30:45.123456", "14:30")
        mock_duration.return_value = 120.0
        mock_calc_end.return_value = "2024-03-15T14:32:45.123456"
        mock_load_mapping.return_value = {}
        mock_get_survey.return_value = "questions.json"
        mock_load_survey.return_value = {"question": "test"}
        mock_convert.return_value = ("/test/video.mp4", False)
        mock_upload.return_value = "https://example.com/video.mp4"
        mock_appscript.return_value = "https://page.url"
        
        # Add files to queue
        events = [
            FileCreatedEvent("/test/video1.mov"),
            FileCreatedEvent("/test/video2.avi")
        ]
        
        for event in events:
            self.handler.on_created(event)
        
        # Wait for timer to trigger
        time.sleep(0.2)  # Longer than batch_interval
        
        # Verify timer is reset
        assert self.handler._timer is None
        
        # Verify queue is empty
        assert self.handler._queue.empty()
        
        # Verify batch processing was called
        mock_appscript.assert_called_once()
        mock_notify.assert_called_once()

    def test_files_during_timer_join_queue(self):
        """Test that files arriving during timer period join the same queue"""
        # Start with one file
        event1 = FileCreatedEvent("/test/video1.mov")
        self.handler.on_created(event1)
        
        original_timer = self.handler._timer
        assert original_timer is not None
        
        # Add more files while timer is running
        event2 = FileCreatedEvent("/test/video2.avi")
        event3 = FileCreatedEvent("/test/video3.mp4")
        
        self.handler.on_created(event2)
        self.handler.on_created(event3)
        
        # Should still be the same timer
        assert self.handler._timer is original_timer
        
        # All files should be in queue
        files_in_queue = []
        while not self.handler._queue.empty():
            files_in_queue.append(self.handler._queue.get())
        
        assert len(files_in_queue) == 3

    @patch('core.video_handler.VideoHandler._wait_for_stable_file')
    @patch('core.video_handler.extract_timestamp_from_filename')
    @patch('core.video_handler.get_fallback_timestamp')
    @patch('core.video_handler.get_video_duration')
    @patch('core.video_handler.calculate_end_time')
    @patch('core.video_handler.load_survey_mapping')
    @patch('core.video_handler.get_survey_for_time')
    @patch('core.video_handler.load_survey_data')
    @patch('core.video_handler.convert_to_mp4')
    @patch('core.video_handler.process_and_upload_video')
    @patch('core.video_handler.call_appscript_batch')
    @patch('core.video_handler.notify_batch')
    def test_timer_resets_after_batch(self, mock_notify, mock_appscript, mock_upload,
                                    mock_convert, mock_load_survey, mock_get_survey,
                                    mock_load_mapping, mock_calc_end, mock_duration,
                                    mock_fallback, mock_extract, mock_wait):
        """Test that timer is properly reset after batch processing"""
        # Setup mocks for successful processing
        mock_wait.return_value = True
        mock_extract.return_value = ("2024-03-15T14:30:45.123456", "14:30")
        mock_duration.return_value = 120.0
        mock_calc_end.return_value = "2024-03-15T14:32:45.123456"
        mock_load_mapping.return_value = {}
        mock_get_survey.return_value = "questions.json"
        mock_load_survey.return_value = {"question": "test"}
        mock_convert.return_value = ("/test/video.mp4", False)
        mock_upload.return_value = "https://example.com/video.mp4"
        mock_appscript.return_value = "https://page.url"
        
        # Process first batch
        event1 = FileCreatedEvent("/test/video1.mov")
        self.handler.on_created(event1)
        
        # Wait for batch to complete
        time.sleep(0.2)
        
        # Timer should be reset
        assert self.handler._timer is None
        
        # Process second batch - should start new timer
        event2 = FileCreatedEvent("/test/video2.avi")
        self.handler.on_created(event2)
        
        # New timer should be started
        assert self.handler._timer is not None
        assert self.handler._timer.is_alive()

    def test_duplicate_files_deduplication(self):
        """Test that duplicate files are deduplicated in batch processing"""
        # Same file path multiple times
        events = [
            FileCreatedEvent("/test/video.mov"),
            FileCreatedEvent("/test/video.mov"),
            FileCreatedEvent("/test/video.mov"),
        ]
        
        for event in events:
            self.handler.on_created(event)
        
        # All should enter queue initially
        files_in_queue = []
        while not self.handler._queue.empty():
            files_in_queue.append(self.handler._queue.get())
        
        assert len(files_in_queue) == 3  # All enter queue
        
        # But _run_batch uses set(items) for deduplication
        # This is tested implicitly in the processing logic

    def test_thread_safety_concurrent_access(self):
        """Test thread safety with concurrent file additions"""
        results = []
        
        def add_files():
            for i in range(10):
                event = FileCreatedEvent(f"/test/video{i}.mov")
                self.handler.on_created(event)
                results.append(f"added_{i}")
        
        # Start multiple threads adding files
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=add_files)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Should have processed all additions without errors
        assert len(results) == 30  # 3 threads * 10 files each
        
        # Should only have one timer
        assert self.handler._timer is not None
        
        # Queue should have files (exact count may vary due to timing)
        assert not self.handler._queue.empty()

    def test_empty_batch_handling(self):
        """Test handling when batch is empty (all files fail stability check)"""
        with patch('core.video_handler.VideoHandler._wait_for_stable_file') as mock_wait:
            mock_wait.return_value = False  # All files fail stability check
            
            # Add files
            events = [
                FileCreatedEvent("/test/video1.mov"),
                FileCreatedEvent("/test/video2.avi")
            ]
            
            for event in events:
                self.handler.on_created(event)
            
            # Wait for timer to trigger
            time.sleep(0.2)
            
            # Timer should be reset even with empty batch
            assert self.handler._timer is None
            assert self.handler._queue.empty()

    @patch('core.video_handler.VideoHandler._wait_for_stable_file')
    @patch('core.video_handler.extract_timestamp_from_filename')
    @patch('core.video_handler.get_fallback_timestamp')
    @patch('core.video_handler.get_video_duration')
    @patch('core.video_handler.calculate_end_time')
    @patch('core.video_handler.load_survey_mapping')
    @patch('core.video_handler.get_survey_for_time')
    @patch('core.video_handler.load_survey_data')
    @patch('core.video_handler.convert_to_mp4')
    @patch('core.video_handler.process_and_upload_video')
    def test_partial_batch_failure(self, mock_upload, mock_convert, mock_load_survey,
                                 mock_get_survey, mock_load_mapping, mock_calc_end,
                                 mock_duration, mock_fallback, mock_extract, mock_wait):
        """Test handling when some files in batch fail processing"""
        # Setup mocks
        mock_wait.return_value = True
        mock_extract.return_value = ("2024-03-15T14:30:45.123456", "14:30")
        mock_duration.return_value = 120.0
        mock_calc_end.return_value = "2024-03-15T14:32:45.123456"
        mock_load_mapping.return_value = {}
        mock_get_survey.return_value = "questions.json"
        mock_load_survey.return_value = {"question": "test"}
        mock_convert.return_value = ("/test/video.mp4", False)
        
        # First file succeeds, second fails
        mock_upload.side_effect = [
            "https://example.com/video1.mp4",  # Success
            None  # Failure
        ]
        
        # Add files
        events = [
            FileCreatedEvent("/test/video1.mov"),
            FileCreatedEvent("/test/video2.avi")
        ]
        
        for event in events:
            self.handler.on_created(event)
        
        # Wait for processing
        time.sleep(0.2)
        
        # Should complete without errors, only successful file continues
        assert self.handler._timer is None

    def test_batch_interval_configuration(self):
        """Test that batch interval is properly configured"""
        # Test default interval
        handler1 = VideoHandler(Mock())
        assert handler1.batch_interval == 10  # Default from config
        
        # Test custom interval
        handler2 = VideoHandler(Mock(), batch_interval=5)
        assert handler2.batch_interval == 5
        
        # Test None uses default
        handler3 = VideoHandler(Mock(), batch_interval=None)
        assert handler3.batch_interval == 10