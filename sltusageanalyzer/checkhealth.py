from sltusageanalyzer.utils import compare_file_hash

import requests
from loguru import logger


def check_health(cfg_path, cfg_hash_path, script_path, script_hash_path):
    return_code = 0

    if not cfg_path.exists():
        logger.error("Configuration file missing.")
        return_code += 1
    else:
        logger.info("Configuration file found.")
        logger.debug(f"File attrs: { cfg_path.stat() }")

        if compare_file_hash(cfg_path, cfg_hash_path):
            logger.info("Configuration file hash verified.")
        else:
            logger.error("Configuration file hash mismatch.")
            return_code += 1

    if not script_path.exists():
        logger.error("Script file missing.")
        return_code += 1
    else:
        logger.info("Script file found.")
        logger.debug(f"File attrs: { script_path.stat() }")

        if compare_file_hash(script_path, script_hash_path):
            logger.info("Script file hash verified.")
        else:
            logger.error("Script file hash mismatch.")
            return_code += 1

    try:
        response = requests.get("https://www.google.com", timeout=5)
        if response.status_code == 200:
            logger.info("Internet connection verified.")
        else:
            logger.error(
                f"Received unexpected status code: { response.status_code }"
            )
            return_code += 1

    except requests.ConnectionError:
        logger.error("No internet connection.")
        return_code += 1

    except requests.Timeout:
        logger.error("The request timed out.")
        return_code += 1

    except Exception as e:
        logger.error("Unexpected error")
        logger.exception(e)
        return_code += 1

    return return_code
