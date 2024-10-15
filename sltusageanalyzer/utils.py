from pathlib import Path
import hashlib
import getpass

from loguru import logger
from dotenv import dotenv_values


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


def setup_data_folder(
    data_path,
    cfg_path,
    cfg_hash_path,
    assets_path,
    script_path,
    script_hash_path,
):
    if not data_path.exists():
        logger.error("Data folder not found.")
        logger.info(f"Creating data folder @ {data_path}")
        data_path.mkdir()
    else:
        logger.info(f"Data folder found @ {data_path}")

    if not cfg_path.exists():
        logger.error("Config file not found.")
        logger.info("Creating config file...")

        cfg_path.touch()
        cfg_path.write_text(
            format_str(
                Path(assets_path) / "template.config.txt",
                username=input("Enter username: "),
                password=getpass.getpass("Enter password: "),
                id=input("Enter id(94xxxxxxxxx): "),
            )
        )
        cfg_hash_path.touch()
        cfg_hash_path.write_text(
            hashlib.sha256(cfg_path.read_bytes()).hexdigest()
        )

    else:
        _saved_hash = cfg_hash_path.read_text().removesuffix("\n")
        _cfg_hash = hashlib.sha256(cfg_path.read_bytes()).hexdigest()
        if _saved_hash != _cfg_hash:
            logger.error("Config file hash mismatch.")
            if (
                input("Would you like to reset config file?(y/n): ").lower()
                != "y"
            ):
                logger.info("Exiting...")
                exit(0)
            logger.info("Removing corrupt config file...")
            cfg_path.unlink()
            logger.info("Creating config file...")
            cfg_path.touch()
            cfg_path.write_text(
                format_str(
                    Path(assets_path) / "template.config.txt",
                    username=input("Enter username: "),
                    password=getpass.getpass("Enter password: "),
                    id=input("Enter id(94xxxxxxxxx): "),
                )
            )
            cfg_hash_path.touch()
            cfg_hash_path.write_text(
                hashlib.sha256(cfg_path.read_bytes()).hexdigest()
            )
        else:
            logger.info("Config file validation successful.")

    if not script_path.exists():
        logger.info("Creating script file...")
        script_path.touch()

        username = dotenv_values(cfg_path)["USERNAME"]
        passwd = dotenv_values(cfg_path)["PASSWORD"]
        id = dotenv_values(cfg_path)["ID"]

        script_path.write_text(
            format_str(
                Path(assets_path) / "template.pwsh_script.txt",
                username=username,
                password=passwd,
                subscriberID=id,
            )
        )

        script_hash_path.touch()
        script_hash_path.write_text(
            hashlib.sha256(script_path.read_bytes()).hexdigest()
        )

    else:
        _saved_hash = script_hash_path.read_text().removesuffix("\n")
        _cfg_hash = hashlib.sha256(script_path.read_bytes()).hexdigest()
        if _saved_hash != _cfg_hash:
            logger.error("Script file hash mismatch.")
            if (
                input("Would you like to reset script file?(y/n): ").lower()
                != "y"
            ):
                logger.info("Exiting...")
                exit(0)
            logger.info("Removing corrupt script file...")
            script_path.unlink()
            logger.info("Creating script file...")
            script_path.touch()
            script_path.write_text(
                format_str(
                    Path(assets_path) / "template.config.txt",
                    username=dotenv_values(cfg_path)["USERNAME"],
                    passwd=dotenv_values(cfg_path)["PASSWORD"],
                    id=dotenv_values(cfg_path)["ID"],
                )
            )
            script_hash_path.touch()
            script_hash_path.write_text(
                hashlib.sha256(script_path.read_bytes()).hexdigest()
            )
        else:
            logger.info("Script file validation successful.")
