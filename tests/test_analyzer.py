"""
PyLogStream - Unit Tests for Analyzer Module

Tests cover:
- LogStreamer initialization
- Lazy file reading (generator behavior)
- Log parsing with regex
- Filtering with various conditions
- Decorator timing functionality
"""

import os
import tempfile
import pytest
from typing import Generator, Dict, Any
from io import StringIO
from unittest.mock import patch

from src.analyzer import LogStreamer, time_execution, create_filter


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_log_content() -> str:
    """Sample log content for testing."""
    return """2024-01-15 10:30:45 [INFO] Application started successfully
2024-01-15 10:30:46 [DEBUG] Loading configuration from config.yaml
2024-01-15 10:30:47 [INFO] Database connection established
2024-01-15 10:31:00 [WARNING] Memory usage above 80%
2024-01-15 10:31:15 [ERROR] Connection timeout to external API
2024-01-15 10:31:20 [ERROR] Failed to process request: timeout exceeded
2024-01-15 10:31:30 [INFO] Retrying connection...
2024-01-15 10:31:45 [INFO] Connection restored
2024-01-15 10:32:00 [DEBUG] Cache invalidated
2024-01-15 10:32:30 [CRITICAL] System shutdown initiated
"""


@pytest.fixture
def temp_log_file(sample_log_content: str) -> Generator[str, None, None]:
    """Create a temporary log file for testing."""
    with tempfile.NamedTemporaryFile(
        mode='w', 
        suffix='.log', 
        delete=False,
        encoding='utf-8'
    ) as f:
        f.write(sample_log_content)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    os.unlink(temp_path)


@pytest.fixture
def log_streamer(temp_log_file: str) -> LogStreamer:
    """Create a LogStreamer instance for testing."""
    return LogStreamer(temp_log_file)


# ============================================================================
# Test LogStreamer Initialization
# ============================================================================

class TestLogStreamerInit:
    """Tests for LogStreamer initialization."""
    
    def test_init_with_valid_path(self, temp_log_file: str) -> None:
        """Test initialization with a valid file path."""
        streamer = LogStreamer(temp_log_file)
        assert streamer.file_path == temp_log_file
        assert streamer.log_pattern is not None
    
    def test_init_with_custom_pattern(self, temp_log_file: str) -> None:
        """Test initialization with a custom regex pattern."""
        custom_pattern = r'^(\d{4}-\d{2}-\d{2})\s+\[(\w+)\]\s+(.+)$'
        streamer = LogStreamer(temp_log_file, pattern=custom_pattern)
        assert streamer._pattern_str == custom_pattern
    
    def test_init_with_invalid_pattern(self, temp_log_file: str) -> None:
        """Test initialization with an invalid regex pattern."""
        with pytest.raises(ValueError, match="Invalid regex pattern"):
            LogStreamer(temp_log_file, pattern="[invalid")


# ============================================================================
# Test Lazy File Reading
# ============================================================================

class TestLazyFileReading:
    """Tests for lazy file reading using generators."""
    
    def test_read_file_lazy_returns_generator(self, log_streamer: LogStreamer) -> None:
        """Verify _read_file_lazy returns a generator."""
        result = log_streamer._read_file_lazy()
        assert isinstance(result, Generator)
    
    def test_read_file_lazy_yields_lines(self, log_streamer: LogStreamer) -> None:
        """Verify generator yields lines correctly."""
        lines = list(log_streamer._read_file_lazy())
        assert len(lines) == 10  # 10 log lines in sample content
        assert "Application started" in lines[0]
    
    def test_read_file_lazy_strips_newlines(self, log_streamer: LogStreamer) -> None:
        """Verify lines have trailing newlines stripped."""
        for line in log_streamer._read_file_lazy():
            assert not line.endswith('\n')
            assert not line.endswith('\r')
    
    def test_read_file_lazy_file_not_found(self) -> None:
        """Verify FileNotFoundError for non-existent file."""
        streamer = LogStreamer("/nonexistent/path/file.log")
        with pytest.raises(FileNotFoundError):
            list(streamer._read_file_lazy())


# ============================================================================
# Test Log Parsing
# ============================================================================

class TestLogParsing:
    """Tests for log parsing functionality."""
    
    def test_parse_logs_returns_generator(self, log_streamer: LogStreamer) -> None:
        """Verify parse_logs returns a generator."""
        result = log_streamer.parse_logs()
        assert isinstance(result, Generator)
    
    def test_parse_logs_yields_dicts(self, log_streamer: LogStreamer) -> None:
        """Verify parse_logs yields dictionaries with correct keys."""
        for log in log_streamer.parse_logs():
            assert isinstance(log, dict)
            assert 'timestamp' in log
            assert 'level' in log
            assert 'message' in log
            assert 'raw' in log
    
    def test_parse_logs_extracts_timestamp(self, log_streamer: LogStreamer) -> None:
        """Verify timestamp extraction."""
        first_log = next(log_streamer.parse_logs())
        assert first_log['timestamp'] == '2024-01-15 10:30:45'
    
    def test_parse_logs_extracts_level(self, log_streamer: LogStreamer) -> None:
        """Verify log level extraction."""
        logs = list(log_streamer.parse_logs())
        levels = [log['level'] for log in logs]
        
        assert 'INFO' in levels
        assert 'DEBUG' in levels
        assert 'ERROR' in levels
        assert 'WARNING' in levels
    
    def test_parse_logs_extracts_message(self, log_streamer: LogStreamer) -> None:
        """Verify message extraction."""
        first_log = next(log_streamer.parse_logs())
        assert first_log['message'] == 'Application started successfully'
    
    def test_parse_logs_preserves_raw(self, log_streamer: LogStreamer) -> None:
        """Verify raw line is preserved."""
        first_log = next(log_streamer.parse_logs())
        assert first_log['raw'] == '2024-01-15 10:30:45 [INFO] Application started successfully'


# ============================================================================
# Test Log Filtering
# ============================================================================

class TestLogFiltering:
    """Tests for log filtering with lambda conditions."""
    
    def test_filter_by_level(self, log_streamer: LogStreamer) -> None:
        """Test filtering by log level."""
        errors = log_streamer.filter_logs(lambda log: log['level'] == 'ERROR')
        assert len(errors) == 2
        for log in errors:
            assert log['level'] == 'ERROR'
    
    def test_filter_by_keyword(self, log_streamer: LogStreamer) -> None:
        """Test filtering by keyword in message."""
        timeout_logs = log_streamer.filter_logs(
            lambda log: 'timeout' in log['message'].lower()
        )
        assert len(timeout_logs) == 2
    
    def test_filter_combined_condition(self, log_streamer: LogStreamer) -> None:
        """Test filtering with combined level and keyword."""
        results = log_streamer.filter_logs(
            lambda log: log['level'] == 'ERROR' and 'timeout' in log['message'].lower()
        )
        assert len(results) == 1
        assert 'timeout' in results[0]['message'].lower()
    
    def test_filter_no_matches(self, log_streamer: LogStreamer) -> None:
        """Test filtering with no matching logs."""
        results = log_streamer.filter_logs(lambda log: log['level'] == 'NONEXISTENT')
        assert len(results) == 0
    
    def test_filter_all_match(self, log_streamer: LogStreamer) -> None:
        """Test filtering where all logs match."""
        results = log_streamer.filter_logs(lambda log: True)
        assert len(results) == 10


# ============================================================================
# Test create_filter Factory
# ============================================================================

class TestCreateFilter:
    """Tests for the create_filter factory function."""
    
    def test_create_filter_level_only(self, log_streamer: LogStreamer) -> None:
        """Test filter creation with level only."""
        filter_func = create_filter(level='ERROR')
        results = log_streamer.filter_logs(filter_func)
        assert len(results) == 2
    
    def test_create_filter_keyword_only(self, log_streamer: LogStreamer) -> None:
        """Test filter creation with keyword only."""
        filter_func = create_filter(keyword='connection')
        results = log_streamer.filter_logs(filter_func)
        assert len(results) == 3  # timeout, restored, established
    
    def test_create_filter_combined(self, log_streamer: LogStreamer) -> None:
        """Test filter creation with both level and keyword."""
        filter_func = create_filter(level='INFO', keyword='connection')
        results = log_streamer.filter_logs(filter_func)
        # Should match: "Database connection established", "Retrying connection...", "Connection restored"
        assert all(log['level'] == 'INFO' for log in results)
    
    def test_create_filter_no_args(self, log_streamer: LogStreamer) -> None:
        """Test filter creation with no arguments matches all."""
        filter_func = create_filter()
        results = log_streamer.filter_logs(filter_func)
        assert len(results) == 10
    
    def test_create_filter_case_insensitive(self, log_streamer: LogStreamer) -> None:
        """Test filter is case-insensitive."""
        filter_func = create_filter(level='error', keyword='TIMEOUT')
        results = log_streamer.filter_logs(filter_func)
        assert len(results) > 0


# ============================================================================
# Test time_execution Decorator
# ============================================================================

class TestTimeExecutionDecorator:
    """Tests for the time_execution decorator."""
    
    def test_decorator_prints_time(self, capsys) -> None:
        """Test that decorator prints execution time."""
        @time_execution
        def dummy_function():
            return "result"
        
        result = dummy_function()
        captured = capsys.readouterr()
        
        assert result == "result"
        assert "⏱️" in captured.out
        assert "dummy_function" in captured.out
        assert "executed in" in captured.out
    
    def test_decorator_preserves_function_name(self) -> None:
        """Test that decorator preserves function metadata."""
        @time_execution
        def my_named_function():
            """My docstring."""
            pass
        
        assert my_named_function.__name__ == "my_named_function"
        assert my_named_function.__doc__ == "My docstring."
    
    def test_decorator_passes_args(self) -> None:
        """Test that decorator passes arguments correctly."""
        @time_execution
        def add(a: int, b: int) -> int:
            return a + b
        
        result = add(2, 3)
        assert result == 5


# ============================================================================
# Test count_by_level
# ============================================================================

class TestCountByLevel:
    """Tests for count_by_level method."""
    
    def test_count_by_level_returns_dict(self, log_streamer: LogStreamer) -> None:
        """Test that count_by_level returns a dictionary."""
        counts = log_streamer.count_by_level()
        assert isinstance(counts, dict)
    
    def test_count_by_level_correct_counts(self, log_streamer: LogStreamer) -> None:
        """Test that counts are accurate."""
        counts = log_streamer.count_by_level()
        
        assert counts.get('INFO') == 4
        assert counts.get('DEBUG') == 2
        assert counts.get('ERROR') == 2
        assert counts.get('WARNING') == 1
        assert counts.get('CRITICAL') == 1


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for the complete workflow."""
    
    def test_full_workflow(self, temp_log_file: str, capsys) -> None:
        """Test complete workflow from file to filtered results."""
        streamer = LogStreamer(temp_log_file)
        
        # Filter for errors
        errors = streamer.filter_logs(lambda log: log['level'] == 'ERROR')
        
        # Verify results
        assert len(errors) == 2
        
        # Verify timing was printed
        captured = capsys.readouterr()
        assert "filter_logs executed in" in captured.out
    
    def test_large_file_memory_efficiency(self) -> None:
        """
        Test that large files can be processed without loading all into memory.
        
        This test creates a large temporary file and verifies that:
        1. The generator approach works with many lines
        2. We can iterate through results without memory issues
        """
        # Create a larger test file
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.log', 
            delete=False,
            encoding='utf-8'
        ) as f:
            for i in range(10000):
                level = ['INFO', 'DEBUG', 'ERROR', 'WARNING'][i % 4]
                f.write(f"2024-01-15 10:30:{i % 60:02d} [{level}] Log message {i}\n")
            temp_path = f.name
        
        try:
            streamer = LogStreamer(temp_path)
            
            # Count using generator (memory efficient)
            count = 0
            for _ in streamer.parse_logs():
                count += 1
            
            assert count == 10000
        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
