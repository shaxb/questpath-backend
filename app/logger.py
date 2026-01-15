import structlog
import logging
import sys
from pathlib import Path

# Create logs directory
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Create file handler with custom processor
def add_custom_format(logger, method_name, event_dict):
    """Format: 2026-01-11 22:57:35, INFO, test_logger:8, message"""
    timestamp = event_dict.pop("timestamp", "")
    level = event_dict.pop("level", "").upper()
    filename = event_dict.pop("filename", "unknown")
    lineno = event_dict.pop("lineno", "?")
    
    # First item is the event/message
    event = event_dict.pop("event", "")
    
    # Build the log line
    location = f"{filename}:{lineno}"
    
    # Add remaining key-value pairs
    extras = " ".join(f"{k}={v}" for k, v in event_dict.items())
    message = f"{event} {extras}".strip()
    
    # Return formatted string (no colors - plain text)
    return f"{timestamp}, {level}, {location}, {message}"

def add_custom_format_colored(logger, method_name, event_dict):
    """Format with colors for console"""
    timestamp = event_dict.pop("timestamp", "")
    level = event_dict.pop("level", "").upper()
    filename = event_dict.pop("filename", "unknown")
    lineno = event_dict.pop("lineno", "?")
    
    # First item is the event/message
    event = event_dict.pop("event", "")
    
    # Build the log line
    location = f"{filename}:{lineno}"
    
    # Add remaining key-value pairs
    extras = " ".join(f"{k}={v}" for k, v in event_dict.items())
    message = f"{event} {extras}".strip()
    
    # Color codes for console
    COLORS = {
        "DEBUG": "\033[36m",    # Cyan
        "INFO": "\033[32m",     # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",    # Red
        "CRITICAL": "\033[35m", # Magenta
    }
    RESET = "\033[0m"
    GRAY = "\033[90m"
    
    # Return formatted string with colors
    color = COLORS.get(level, "")
    colored_line = f"{GRAY}{timestamp}{RESET}, {color}{level}{RESET}, {GRAY}{location}{RESET}, {message}"
    
    return colored_line

# Processors for file (plain text)
file_processors = [
    structlog.stdlib.add_log_level,
    structlog.processors.CallsiteParameterAdder(
        parameters=[
            structlog.processors.CallsiteParameter.FILENAME,
            structlog.processors.CallsiteParameter.LINENO,
        ],
        additional_ignores=["app.logger"]  # Skip our DualLogger wrapper
    ),
    structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
    add_custom_format,  # Plain text
]

# Processors for console (colored)
console_processors = [
    structlog.stdlib.add_log_level,
    structlog.processors.CallsiteParameterAdder(
        parameters=[
            structlog.processors.CallsiteParameter.FILENAME,
            structlog.processors.CallsiteParameter.LINENO,
        ],
        additional_ignores=["app.logger"]  # Skip our DualLogger wrapper
    ),
    structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
    add_custom_format_colored,  # Colored
]

# Set up file logging (plain format) with its own logger
file_logger = logging.getLogger("file")
file_handler = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter("%(message)s"))
file_logger.addHandler(file_handler)
file_logger.setLevel(logging.INFO)
file_logger.propagate = False

# Set up console logging with its own logger
console_logger = logging.getLogger("console")
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(message)s"))
console_logger.addHandler(console_handler)
console_logger.setLevel(logging.INFO)
console_logger.propagate = False

# Configure structlog with console processors (colored)
structlog.configure(
    processors=console_processors,
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Wrap both loggers
file_log = structlog.wrap_logger(file_logger, processors=file_processors)
console_log = structlog.wrap_logger(console_logger, processors=console_processors)

# Create a logger that writes to both
class DualLogger:
    def __init__(self, file_logger, console_logger):
        self.file = file_logger
        self.console = console_logger
    
    def info(self, event, **kwargs):
        self.file.info(event, **kwargs)
        self.console.info(event, **kwargs)
    
    def warning(self, event, **kwargs):
        self.file.warning(event, **kwargs)
        self.console.warning(event, **kwargs)
    
    def error(self, event, **kwargs):
        self.file.error(event, **kwargs)
        self.console.error(event, **kwargs)
    
    def debug(self, event, **kwargs):
        self.file.debug(event, **kwargs)
        self.console.debug(event, **kwargs)
    
    def critical(self, event, **kwargs):
        self.file.critical(event, **kwargs)
        self.console.critical(event, **kwargs)

# Default logger writes to both file (plain) and console (colored)
logger = DualLogger(file_log, console_log)