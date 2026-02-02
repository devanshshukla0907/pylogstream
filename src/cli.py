#!/usr/bin/env python3
"""
PyLogStream - Command Line Interface

A high-performance, memory-efficient CLI tool for parsing and filtering
massive log files using lazy evaluation.

Usage:
    python -m src.cli <file_path> [--level LEVEL] [--keyword KEYWORD]
    
Examples:
    python -m src.cli logs/app.log --level ERROR
    python -m src.cli logs/app.log --keyword "connection failed"
    python -m src.cli logs/app.log --level ERROR --keyword timeout
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .analyzer import LogStreamer, create_filter


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser for PyLogStream CLI.
    
    Returns:
        argparse.ArgumentParser: Configured parser with all arguments.
    """
    parser = argparse.ArgumentParser(
        prog='pylogstream',
        description='''
╔═══════════════════════════════════════════════════════════════════╗
║  PyLogStream - High-Performance Log Parser                        ║
║  Parse massive log files without crashing your RAM!               ║
╚═══════════════════════════════════════════════════════════════════╝
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s logs/app.log                          Parse all logs
  %(prog)s logs/app.log --level ERROR            Filter by ERROR level
  %(prog)s logs/app.log --keyword "timeout"      Filter by keyword
  %(prog)s logs/app.log --level ERROR --keyword "db"  Combined filter
        '''
    )
    
    parser.add_argument(
        'file_path',
        type=str,
        help='Path to the log file to parse'
    )
    
    parser.add_argument(
        '--level', '-l',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Filter logs by level (DEBUG, INFO, WARNING, ERROR, CRITICAL)'
    )
    
    parser.add_argument(
        '--keyword', '-k',
        type=str,
        help='Filter logs by keyword in message (case-insensitive)'
    )
    
    parser.add_argument(
        '--count', '-c',
        action='store_true',
        help='Show count of logs by level instead of log entries'
    )
    
    parser.add_argument(
        '--limit', '-n',
        type=int,
        default=None,
        help='Limit the number of results displayed'
    )
    
    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored output'
    )
    
    return parser


def colorize(text: str, color: str, no_color: bool = False) -> str:
    """
    Apply ANSI color codes to text.
    
    Args:
        text: The text to colorize.
        color: Color name (red, yellow, green, blue, magenta, cyan).
        no_color: If True, return text without color codes.
        
    Returns:
        str: Colorized text (or plain text if no_color is True).
    """
    if no_color:
        return text
    
    colors = {
        'red': '\033[91m',
        'yellow': '\033[93m',
        'green': '\033[92m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'reset': '\033[0m',
        'bold': '\033[1m',
        'dim': '\033[2m'
    }
    
    return f"{colors.get(color, '')}{text}{colors['reset']}"


def get_level_color(level: str) -> str:
    """Map log level to display color."""
    level_colors = {
        'ERROR': 'red',
        'CRITICAL': 'red',
        'WARNING': 'yellow',
        'INFO': 'green',
        'DEBUG': 'blue'
    }
    return level_colors.get(level.upper(), 'cyan')


def format_log_entry(log: dict, no_color: bool = False) -> str:
    """
    Format a log entry for display.
    
    Args:
        log: Dictionary containing timestamp, level, and message.
        no_color: If True, output without colors.
        
    Returns:
        str: Formatted log entry string.
    """
    level = log['level']
    level_color = get_level_color(level)
    
    timestamp = colorize(log['timestamp'], 'dim', no_color)
    level_str = colorize(f"[{level:^8}]", level_color, no_color)
    message = log['message']
    
    return f"{timestamp} {level_str} {message}"


def print_header(title: str, no_color: bool = False) -> None:
    """Print a formatted header."""
    line = "═" * 60
    print(colorize(f"\n╔{line}╗", 'cyan', no_color))
    print(colorize(f"║  {title:<57}║", 'cyan', no_color))
    print(colorize(f"╚{line}╝\n", 'cyan', no_color))


def print_stats(count: int, elapsed_info: str, no_color: bool = False) -> None:
    """Print result statistics."""
    print(colorize(f"\n📊 Found {count} matching log entries", 'bold', no_color))


def main(argv: Optional[list] = None) -> int:
    """
    Main entry point for the PyLogStream CLI.
    
    Args:
        argv: Command line arguments (defaults to sys.argv[1:]).
        
    Returns:
        int: Exit code (0 for success, 1 for errors).
    """
    parser = create_parser()
    args = parser.parse_args(argv)
    
    # Validate file exists
    file_path = Path(args.file_path)
    if not file_path.exists():
        print(f"❌ Error: File not found: {args.file_path}", file=sys.stderr)
        return 1
    
    if not file_path.is_file():
        print(f"❌ Error: Not a file: {args.file_path}", file=sys.stderr)
        return 1
    
    try:
        # Initialize the log streamer
        streamer = LogStreamer(str(file_path))
        
        # Handle count mode
        if args.count:
            print_header("Log Level Statistics", args.no_color)
            counts = streamer.count_by_level()
            
            total = sum(counts.values())
            for level, count in sorted(counts.items()):
                color = get_level_color(level)
                bar_length = int((count / total) * 40) if total > 0 else 0
                bar = "█" * bar_length
                percentage = (count / total * 100) if total > 0 else 0
                
                level_str = colorize(f"{level:>8}", color, args.no_color)
                print(f"  {level_str}: {count:>6} ({percentage:5.1f}%) {bar}")
            
            print(colorize(f"\n  {'TOTAL':>8}: {total:>6}", 'bold', args.no_color))
            return 0
        
        # Create filter based on arguments
        log_filter = create_filter(level=args.level, keyword=args.keyword)
        
        # Build filter description for header
        filter_desc = "All Logs"
        if args.level and args.keyword:
            filter_desc = f"Level={args.level}, Keyword='{args.keyword}'"
        elif args.level:
            filter_desc = f"Level={args.level}"
        elif args.keyword:
            filter_desc = f"Keyword='{args.keyword}'"
        
        print_header(f"PyLogStream Results: {filter_desc}", args.no_color)
        
        # Filter and display logs
        results = streamer.filter_logs(log_filter)
        
        # Apply limit if specified
        display_results = results[:args.limit] if args.limit else results
        
        if not display_results:
            print(colorize("  No matching logs found.", 'yellow', args.no_color))
        else:
            for log in display_results:
                print(f"  {format_log_entry(log, args.no_color)}")
            
            if args.limit and len(results) > args.limit:
                remaining = len(results) - args.limit
                print(colorize(
                    f"\n  ... and {remaining} more entries (use --limit to see more)",
                    'dim', 
                    args.no_color
                ))
        
        print_stats(len(results), "", args.no_color)
        return 0
        
    except FileNotFoundError:
        print(f"❌ Error: File not found: {args.file_path}", file=sys.stderr)
        return 1
    except PermissionError:
        print(f"❌ Error: Permission denied: {args.file_path}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
