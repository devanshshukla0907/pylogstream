"""
PyLogStream - Core Analyzer Module

This module provides the core functionality for lazy log file parsing
using generators and functional programming concepts.

Features:
    - Memory-efficient file reading using generators (lazy evaluation)
    - Regex-based log parsing
    - Lambda-powered filtering
    - Execution time measurement via decorators
"""

import re
import time
from functools import wraps
from typing import Generator, Dict, Any, Callable, List, Optional


def time_execution(func: Callable) -> Callable:
    """
    Decorator to measure and log the execution time of a function.
    
    Uses @wraps to preserve the original function's metadata (name, docstring, etc.)
    
    Args:
        func: The function to be wrapped and timed.
        
    Returns:
        Callable: The wrapped function with timing capability.
        
    Example:
        >>> @time_execution
        ... def slow_function():
        ...     time.sleep(1)
        ...     return "done"
        >>> result = slow_function()
        ⏱️  slow_function executed in 1.0012s
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        elapsed = end_time - start_time
        print(f"⏱️  {func.__name__} executed in {elapsed:.4f}s")
        return result
    return wrapper


class LogStreamer:
    """
    A memory-efficient log file parser using lazy evaluation.
    
    This class reads and parses log files line-by-line using Python generators,
    allowing it to process files of any size without exhausting system memory.
    
    Attributes:
        file_path (str): Path to the log file to be processed.
        log_pattern (re.Pattern): Compiled regex pattern for parsing log lines.
        
    Example:
        >>> streamer = LogStreamer("logs/app.log")
        >>> for log in streamer.parse_logs():
        ...     print(log['level'], log['message'])
    """
    
    # Standard log format: 2024-01-15 10:30:45 [ERROR] Connection failed
    DEFAULT_PATTERN = r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+\[(\w+)\]\s+(.+)$'
    
    def __init__(
        self, 
        file_path: str, 
        pattern: Optional[str] = None
    ) -> None:
        """
        Initialize the LogStreamer with a file path and optional custom pattern.
        
        Args:
            file_path: Path to the log file to process.
            pattern: Optional custom regex pattern for parsing logs.
                     Must have 3 capture groups: (timestamp, level, message)
                     
        Raises:
            FileNotFoundError: If the specified file does not exist.
            ValueError: If the custom pattern is invalid.
        """
        self.file_path: str = file_path
        self._pattern_str: str = pattern or self.DEFAULT_PATTERN
        
        try:
            self.log_pattern: re.Pattern = re.compile(self._pattern_str)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")
    
    def _read_file_lazy(self) -> Generator[str, None, None]:
        """
        Read the log file line-by-line using lazy evaluation.
        
        This generator yields one line at a time, ensuring that only a single
        line is held in memory at any given moment. This is the key to handling
        files that are larger than available RAM.
        
        Yields:
            str: A single line from the file (with trailing newline stripped).
            
        Raises:
            FileNotFoundError: If the file does not exist.
            PermissionError: If the file cannot be read.
            
        Note:
            Uses a context manager (with statement) for safe file handling,
            ensuring the file is properly closed even if an error occurs.
        """
        with open(self.file_path, 'r', encoding='utf-8', errors='replace') as file:
            for line in file:
                yield line.rstrip('\n\r')
    
    def parse_logs(self) -> Generator[Dict[str, Any], None, None]:
        """
        Parse log lines into structured dictionaries.
        
        This generator reads lines lazily and parses each one using the
        configured regex pattern. Lines that don't match the pattern are
        silently skipped.
        
        Yields:
            Dict[str, Any]: A dictionary containing:
                - 'timestamp' (str): The log entry timestamp
                - 'level' (str): The log level (INFO, ERROR, DEBUG, WARNING)
                - 'message' (str): The log message content
                - 'raw' (str): The original unparsed line
                
        Example:
            >>> streamer = LogStreamer("app.log")
            >>> for entry in streamer.parse_logs():
            ...     if entry['level'] == 'ERROR':
            ...         print(f"Error at {entry['timestamp']}: {entry['message']}")
        """
        for line in self._read_file_lazy():
            match = self.log_pattern.match(line)
            if match:
                yield {
                    'timestamp': match.group(1),
                    'level': match.group(2).upper(),
                    'message': match.group(3),
                    'raw': line
                }
    
    @time_execution
    def filter_logs(
        self, 
        condition: Callable[[Dict[str, Any]], bool]
    ) -> List[Dict[str, Any]]:
        """
        Filter parsed logs based on a user-defined condition.
        
        This method applies a lambda or function to each parsed log entry
        and returns a list of entries that satisfy the condition. The
        @time_execution decorator measures and prints the filtering duration.
        
        Args:
            condition: A callable (typically a lambda) that takes a log
                      dictionary and returns True if the entry should be
                      included in the results.
                      
        Returns:
            List[Dict[str, Any]]: A list of log entries matching the condition.
            
        Example:
            >>> streamer = LogStreamer("app.log")
            >>> # Filter for ERROR level logs
            >>> errors = streamer.filter_logs(lambda log: log['level'] == 'ERROR')
            ⏱️  filter_logs executed in 0.0234s
            
            >>> # Filter for logs containing 'database' keyword
            >>> db_logs = streamer.filter_logs(
            ...     lambda log: 'database' in log['message'].lower()
            ... )
            
            >>> # Combined filter: ERROR logs with 'timeout' keyword
            >>> timeout_errors = streamer.filter_logs(
            ...     lambda log: log['level'] == 'ERROR' and 'timeout' in log['message'].lower()
            ... )
        """
        return [log for log in self.parse_logs() if condition(log)]
    
    def count_by_level(self) -> Dict[str, int]:
        """
        Count log entries grouped by their log level.
        
        Returns:
            Dict[str, int]: A dictionary mapping log levels to their counts.
            
        Example:
            >>> streamer = LogStreamer("app.log")
            >>> counts = streamer.count_by_level()
            >>> print(counts)
            {'INFO': 1234, 'ERROR': 56, 'DEBUG': 789, 'WARNING': 12}
        """
        counts: Dict[str, int] = {}
        for log in self.parse_logs():
            level = log['level']
            counts[level] = counts.get(level, 0) + 1
        return counts


def create_filter(
    level: Optional[str] = None, 
    keyword: Optional[str] = None
) -> Callable[[Dict[str, Any]], bool]:
    """
    Factory function to create a combined filter lambda.
    
    This utility creates a single callable that can filter by log level,
    keyword, or both simultaneously.
    
    Args:
        level: Optional log level to filter by (case-insensitive).
        keyword: Optional keyword to search for in messages (case-insensitive).
        
    Returns:
        Callable[[Dict[str, Any]], bool]: A filter function for use with filter_logs.
        
    Example:
        >>> # Create a filter for ERROR logs containing 'connection'
        >>> my_filter = create_filter(level='ERROR', keyword='connection')
        >>> errors = streamer.filter_logs(my_filter)
    """
    def filter_func(log: Dict[str, Any]) -> bool:
        level_match = True
        keyword_match = True
        
        if level:
            level_match = log['level'].upper() == level.upper()
        
        if keyword:
            keyword_match = keyword.lower() in log['message'].lower()
        
        return level_match and keyword_match
    
    return filter_func
