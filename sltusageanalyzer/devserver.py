from sltusageanalyzer.__main__ import app

from loguru import logger

import sys


if __name__ == "__main__":
    logger.add(sys.stderr, format="{time} {level} {message}", level="DEBUG")
    logger.warning("Starting development server...")
    app.run(debug=True, host="0.0.0.0", port=3000)
