from sltusageanalyzer.__main__ import app

from loguru import logger

import sys


if __name__ == "__main__":
    _port = None
    if len(sys.argv) > 1:
        try:
            _port = int(sys.argv[1])
        except ValueError:
            _port = 3000
    logger.add(sys.stderr, format="{time} {level} {message}", level="DEBUG")
    logger.warning("Starting development server...")
    app.run(debug=True, host="0.0.0.0", port=_port)
