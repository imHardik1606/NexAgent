import logging
import os

# Create logs/ directory if it doesn't exist
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, "agent.log")

# Configure logging with basicConfig
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Create and export the logger object
logger = logging.getLogger("nexagent")

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
