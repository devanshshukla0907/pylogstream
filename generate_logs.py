#!/usr/bin/env python3
"""
Log Generator Script for PyLogStream Testing

Generates realistic log files for testing PyLogStream's memory efficiency
and filtering capabilities.

Usage:
    python generate_logs.py --lines 1000 --output logs/sample.log
    python generate_logs.py --lines 1000000 --output logs/massive.log
"""

import argparse
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple


# Log level weights (INFO is most common, CRITICAL is rare)
LOG_LEVELS: List[Tuple[str, int]] = [
    ('DEBUG', 15),
    ('INFO', 50),
    ('WARNING', 20),
    ('ERROR', 12),
    ('CRITICAL', 3)
]

# Sample log messages by category
LOG_MESSAGES = {
    'DEBUG': [
        "Loading configuration from config.yaml",
        "Cache hit for key: user_session_{}",
        "Database query executed in {}ms",
        "Parsing request body: {} bytes",
        "Memory usage: {}MB",
        "Thread pool size: {}",
        "Garbage collection triggered",
        "Socket buffer size: {} bytes",
        "SSL handshake completed",
        "Request headers validated"
    ],
    'INFO': [
        "Application started successfully",
        "Server listening on port {}",
        "User {} logged in successfully",
        "Database connection established",
        "Processing batch job: {}",
        "Email sent to {}",
        "File uploaded: {}",
        "Cache cleared for namespace: {}",
        "Scheduled task completed: {}",
        "Health check passed",
        "Connection restored",
        "Session created for user {}",
        "API request completed in {}ms",
        "Backup completed successfully",
        "Configuration reloaded"
    ],
    'WARNING': [
        "Memory usage above 80%",
        "Slow query detected: {}ms",
        "Rate limit approaching for IP: {}",
        "Deprecated API endpoint called: {}",
        "Certificate expires in {} days",
        "Connection pool nearly exhausted",
        "Retry attempt {} of 3",
        "Cache miss rate above threshold",
        "Disk usage at {}%",
        "Response time degraded"
    ],
    'ERROR': [
        "Connection timeout to external API",
        "Failed to process request: timeout exceeded",
        "Database connection failed: {}",
        "Authentication failed for user: {}",
        "File not found: {}",
        "Invalid JSON payload received",
        "Maximum retries exceeded",
        "API rate limit exceeded",
        "Socket connection refused",
        "Transaction rollback: {}"
    ],
    'CRITICAL': [
        "System shutdown initiated",
        "Out of memory error",
        "Database corruption detected",
        "Security breach detected from IP: {}",
        "Disk failure on volume: {}",
        "Cluster node {} unreachable",
        "Data integrity check failed",
        "Emergency shutdown triggered"
    ]
}


def get_weighted_level() -> str:
    """Get a random log level based on weights."""
    levels = [level for level, _ in LOG_LEVELS]
    weights = [weight for _, weight in LOG_LEVELS]
    return random.choices(levels, weights=weights, k=1)[0]


def get_random_message(level: str) -> str:
    """Get a random message for the given log level."""
    template = random.choice(LOG_MESSAGES[level])
    
    # Fill in placeholder values
    if '{}' in template:
        placeholders = template.count('{}')
        values = []
        for _ in range(placeholders):
            # Generate appropriate random values
            value_type = random.choice(['int', 'str', 'ip', 'file'])
            if value_type == 'int':
                values.append(str(random.randint(1, 10000)))
            elif value_type == 'str':
                values.append(random.choice([
                    'user_123', 'admin', 'service_worker', 'batch_001',
                    'cache_main', 'session_abc', 'job_xyz', 'task_daily'
                ]))
            elif value_type == 'ip':
                values.append(f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}")
            else:
                values.append(random.choice([
                    '/var/log/app.log', 'config.yaml', 'data.json',
                    '/tmp/upload_123.txt', 'backup_20240115.tar.gz'
                ]))
        
        return template.format(*values)
    
    return template


def generate_timestamp(base: datetime, offset_seconds: int) -> str:
    """Generate a formatted timestamp."""
    ts = base + timedelta(seconds=offset_seconds)
    return ts.strftime('%Y-%m-%d %H:%M:%S')


def generate_log_line(base_time: datetime, offset: int) -> str:
    """Generate a single log line."""
    timestamp = generate_timestamp(base_time, offset)
    level = get_weighted_level()
    message = get_random_message(level)
    
    return f"{timestamp} [{level}] {message}"


def generate_logs(
    output_path: str,
    num_lines: int,
    show_progress: bool = True
) -> None:
    """
    Generate a log file with the specified number of lines.
    
    Args:
        output_path: Path to the output log file.
        num_lines: Number of log lines to generate.
        show_progress: Whether to show progress indicator.
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    
    base_time = datetime.now() - timedelta(days=1)
    
    print(f"🔄 Generating {num_lines:,} log lines...")
    
    with open(output, 'w', encoding='utf-8') as f:
        for i in range(num_lines):
            # Offset increases by 0-5 seconds per line
            offset = i * random.randint(0, 5)
            line = generate_log_line(base_time, offset)
            f.write(line + '\n')
            
            # Progress indicator
            if show_progress and (i + 1) % 10000 == 0:
                progress = (i + 1) / num_lines * 100
                print(f"  Progress: {progress:.1f}% ({i + 1:,} lines)", end='\r')
    
    # Calculate file size
    size_bytes = output.stat().st_size
    if size_bytes >= 1024 * 1024:
        size_str = f"{size_bytes / (1024 * 1024):.2f} MB"
    elif size_bytes >= 1024:
        size_str = f"{size_bytes / 1024:.2f} KB"
    else:
        size_str = f"{size_bytes} bytes"
    
    print(f"\n✅ Generated {num_lines:,} log lines ({size_str})")
    print(f"📁 Output: {output.absolute()}")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate sample log files for PyLogStream testing.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python generate_logs.py --lines 1000 --output logs/sample.log
  python generate_logs.py --lines 100000 --output logs/medium.log
  python generate_logs.py --lines 1000000 --output logs/large.log

The generated logs will have a realistic distribution of log levels:
  - INFO: 50%
  - WARNING: 20%
  - DEBUG: 15%
  - ERROR: 12%
  - CRITICAL: 3%
        '''
    )
    
    parser.add_argument(
        '--lines', '-n',
        type=int,
        default=1000,
        help='Number of log lines to generate (default: 1000)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='logs/sample.log',
        help='Output file path (default: logs/sample.log)'
    )
    
    parser.add_argument(
        '--seed', '-s',
        type=int,
        default=None,
        help='Random seed for reproducible output'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress progress output'
    )
    
    args = parser.parse_args()
    
    if args.seed is not None:
        random.seed(args.seed)
    
    try:
        generate_logs(
            output_path=args.output,
            num_lines=args.lines,
            show_progress=not args.quiet
        )
        return 0
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
