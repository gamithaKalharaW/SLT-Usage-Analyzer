from sltusageanalyzer.__main__ import app

from loguru import logger


if __name__ == "__main__":
    logger.warning("Starting development server...")
    app.run(debug=True, host="0.0.0.0", port=3000)
