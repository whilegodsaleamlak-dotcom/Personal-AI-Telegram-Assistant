import subprocess
import sys
import time
import logging
from datetime import datetime

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

MAX_RETRIES = 50
BASE_DELAY = 5
MAX_DELAY = 300


def run_bot():
    retries = 0
    while retries < MAX_RETRIES:
        try:
            logger.info("Starting bot...")
            process = subprocess.run(
                [sys.executable, "bot.py"],
                check=True,
            )
            logger.info("Bot exited cleanly.")
            break
        except KeyboardInterrupt:
            logger.info("Bot stopped by user.")
            break
        except subprocess.CalledProcessError as e:
            retries += 1
            delay = min(BASE_DELAY * (2 ** (retries - 1)), MAX_DELAY)
            logger.error(
                f"Bot crashed (exit code {e.code}). "
                f"Restart #{retries} in {delay}s..."
            )
            time.sleep(delay)
        except Exception as e:
            retries += 1
            delay = min(BASE_DELAY * (2 ** (retries - 1)), MAX_DELAY)
            logger.error(f"Unexpected error: {e}. Restart #{retries} in {delay}s...")
            time.sleep(delay)

    if retries >= MAX_RETRIES:
        logger.critical(f"Bot crashed {MAX_RETRIES} times. Giving up.")


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("Auto-restart wrapper started")
    logger.info("=" * 50)
    run_bot()
