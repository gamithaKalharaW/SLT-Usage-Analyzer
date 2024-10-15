from pathlib import Path
import hashlib

from loguru import logger


def format_str(fp: str | Path, **kwargs):
    template_str: str = ""
    if isinstance(fp, str):
        fp = Path(fp)
    try:
        template_str = Path(fp).read_text()

    except FileNotFoundError as e:
        logger.error(e)
        exit(1)
    except Exception as e:
        logger.exception(e)
        pass

    for k, v in kwargs.items():
        template_str = template_str.replace(f"{{{{ {k} }}}}", str(v))

    return template_str


def compare_file_hash(filepath: Path, hashpath: Path):
    target_hash = hashpath.read_text().removesuffix("\n")
    current_hash = hashlib.sha256(filepath.read_bytes()).hexdigest()
    return target_hash == current_hash
