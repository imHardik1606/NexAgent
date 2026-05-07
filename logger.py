import logging
import os

# Create logs/ directory if it doesn't exist
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, "agent.log")

# Configure logging
logger = logging.getLogger("nexagent")
logger.setLevel(logging.DEBUG)  # Capture everything for the file

# 1. File Handler: Detailed logging with timestamps
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
file_handler.setFormatter(file_formatter)
file_handler.setLevel(logging.DEBUG) # Save debug info to file

# 2. Console Handler: Clean output (only INFO and above)
console_handler = logging.StreamHandler()
console_formatter = logging.Formatter('%(message)s')
console_handler.setFormatter(console_formatter)
console_handler.setLevel(logging.INFO) # Hide debug info from console


# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Suppress noisy logs from external libraries (HTTP requests, etc.)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("groq").setLevel(logging.WARNING)
logging.getLogger("duckduckgo_search").setLevel(logging.WARNING)

# Create and export the logger object (legacy support for variable name)
# logger already defined above


def log_session_start():
    """Logs a visually distinct header at the start of a session."""
    from datetime import datetime
    logger.info("="*50)
    logger.info("SESSION STARTED")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*50)

def log_session_end(total_interactions: int):
    """Logs a visually distinct header at the end of a session with interaction count."""
    logger.info("="*50)
    logger.info(f"SESSION ENDED | Total interactions: {total_interactions}")
    logger.info("="*50)

if __name__ == "__main__":
    # Log one INFO message and one ERROR message
    logger.info("Test INFO message: Logger is initialized.")
    logger.error("Test ERROR message: Checking error logging.")
    
    # Verify logs/agent.log file is created
    if os.path.exists(log_file):
        print(f"\nVerification: '{log_file}' exists.")
    else:
        print(f"\nVerification Failure: '{log_file}' was not found.")
