<div align="center">

# 🚀 PyLogStream

**High-Performance, Memory-Efficient Log Parser CLI**

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Code Style](https://img.shields.io/badge/Code%20Style-Black-000000?style=for-the-badge)](https://github.com/psf/black)

*Parse massive log files without crashing your RAM!*

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Under the Hood](#-under-the-hood) • [Contributing](#-contributing)

</div>

---

## 🎯 Why PyLogStream?

Ever tried opening a 10GB log file and watched your system grind to a halt? **PyLogStream** solves this by using **lazy evaluation** - a technique that processes data on-demand rather than loading everything into memory at once.

### 📊 Lazy Evaluation vs Eager Loading

| Approach | Memory Usage | Speed | Scalability |
|----------|-------------|-------|-------------|
| **Eager Loading** 😰 | Loads entire file into RAM | Fast initial load, but... | ❌ Crashes on large files |
| **Lazy Evaluation** 🚀 | O(1) - Only one line at a time | Streams continuously | ✅ Handles ANY file size |

```
Traditional Approach (Eager):          PyLogStream (Lazy):
┌─────────────────────────┐           ┌──────────────────────┐
│  Load entire 10GB file  │           │  Read line 1 → Process
│  into memory            │           │  Read line 2 → Process
│  💥 OUT OF MEMORY 💥    │           │  Read line 3 → Process
└─────────────────────────┘           │  ...continues forever
                                      └──────────────────────┘
```

---

## ✨ Features

- 🧠 **Memory Efficient**: Process GB-sized files with minimal RAM
- ⚡ **Fast Filtering**: Lambda-powered dynamic filtering
- 🎨 **Beautiful Output**: Colored, formatted console output
- 📊 **Statistics Mode**: Get log level distribution at a glance
- 🔧 **Extensible**: Custom regex patterns for any log format
- 🐍 **Pure Python**: No external dependencies for core functionality

---

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/pylogstream.git
cd pylogstream

# Install dependencies (optional, for testing)
pip install -r requirements.txt
```

---

## 🚀 Usage

### Basic Commands

```bash
# Parse all logs from a file
python -m src.cli logs/app.log

# Filter by log level
python -m src.cli logs/app.log --level ERROR

# Filter by keyword
python -m src.cli logs/app.log --keyword "connection failed"

# Combined filtering (level AND keyword)
python -m src.cli logs/app.log --level ERROR --keyword timeout

# Show log level statistics
python -m src.cli logs/app.log --count

# Limit output
python -m src.cli logs/app.log --level INFO --limit 10
```

### Generate Test Logs

```bash
# Generate 1,000 sample log lines
python generate_logs.py --lines 1000 --output logs/sample.log

# Generate 1 million lines for stress testing
python generate_logs.py --lines 1000000 --output logs/massive.log
```

### CLI Options

| Option | Short | Description |
|--------|-------|-------------|
| `file_path` | - | Path to the log file (required) |
| `--level` | `-l` | Filter by level: DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `--keyword` | `-k` | Filter by keyword in message (case-insensitive) |
| `--count` | `-c` | Show statistics instead of log entries |
| `--limit` | `-n` | Limit number of results displayed |
| `--no-color` | - | Disable colored output |

---

## 🧠 Under the Hood

PyLogStream demonstrates several advanced Python concepts:

### 1. Generators (Lazy Evaluation)

```python
def _read_file_lazy(self) -> Generator[str, None, None]:
    """Yields one line at a time - O(1) memory!"""
    with open(self.file_path, 'r') as file:
        for line in file:
            yield line.rstrip('\n')
```

The `yield` keyword transforms this into a **generator function**. Instead of returning all lines at once, it pauses after each line, waiting until the next value is requested.

### 2. Decorators (@wraps)

```python
def time_execution(func: Callable) -> Callable:
    """Measures execution time of any function."""
    @wraps(func)  # Preserves function metadata
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"⏱️  {func.__name__} executed in {elapsed:.4f}s")
        return result
    return wrapper
```

Decorators wrap functions to add behavior without modifying the original code. The `@wraps` decorator from `functools` preserves the original function's name and docstring.

### 3. Lambda Functions

```python
# Filter for ERROR logs containing "timeout"
errors = streamer.filter_logs(
    lambda log: log['level'] == 'ERROR' and 'timeout' in log['message'].lower()
)
```

Lambda functions enable dynamic, user-defined filtering conditions without requiring predefined filter methods.

### 4. Type Hints

```python
def filter_logs(
    self, 
    condition: Callable[[Dict[str, Any]], bool]
) -> List[Dict[str, Any]]:
```

Full type annotations using the `typing` module for better code documentation and IDE support.

### 5. Context Managers

```python
with open(self.file_path, 'r', encoding='utf-8') as file:
    # File is automatically closed, even if an error occurs
```

The `with` statement ensures proper resource cleanup.

---

## 📁 Project Structure

```
pylogstream/
├── src/
│   ├── __init__.py       # Package initialization
│   ├── analyzer.py       # Core logic: LogStreamer, decorators
│   └── cli.py            # CLI entry point with argparse
├── tests/
│   ├── __init__.py
│   └── test_analyzer.py  # Comprehensive pytest test suite
├── logs/
│   └── .gitkeep          # Placeholder for user logs
├── generate_logs.py      # Test log generator
├── requirements.txt      # Dependencies
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

---

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run specific test class
python -m pytest tests/test_analyzer.py::TestLogFiltering -v
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with ❤️ and Python**

*Star ⭐ this repo if you find it useful!*

</div>
