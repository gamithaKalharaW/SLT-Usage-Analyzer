from pathlib import Path
import hashlib
import getpass
import json
import subprocess

from loguru import logger
from dotenv import dotenv_values


def get_saved_data(processed_json_path):
    with open(processed_json_path, "r") as f:
        return json.load(f)


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
    vas_script_path,
    vas_script_hash_path,
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

    if not vas_script_path.exists():
        logger.info("Creating vas script file...")
        vas_script_path.touch()

        username = dotenv_values(cfg_path)["USERNAME"]
        passwd = dotenv_values(cfg_path)["PASSWORD"]
        id = dotenv_values(cfg_path)["ID"]

        vas_script_path.write_text(
            format_str(
                Path(assets_path) / "template.vas_data_script.txt",
                username=username,
                password=passwd,
                subscriberID=id,
            )
        )

        vas_script_hash_path.touch()
        vas_script_hash_path.write_text(
            hashlib.sha256(vas_script_path.read_bytes()).hexdigest()
        )

    else:
        _saved_hash = vas_script_hash_path.read_text().removesuffix("\n")
        _cfg_hash = hashlib.sha256(vas_script_path.read_bytes()).hexdigest()
        if _saved_hash != _cfg_hash:
            logger.error("VAS script file hash mismatch.")
            if (
                input("Would you like to reset vas script file?(y/n): ").lower()
                != "y"
            ):
                logger.info("Exiting...")
                exit(0)
            logger.info("Removing corrupt script file...")
            vas_script_path.unlink()
            logger.info("Creating script file...")
            vas_script_path.touch()
            vas_script_path.write_text(
                format_str(
                    Path(assets_path) / "template.vas_data_script.txt",
                    username=dotenv_values(cfg_path)["USERNAME"],
                    passwd=dotenv_values(cfg_path)["PASSWORD"],
                    id=dotenv_values(cfg_path)["ID"],
                )
            )
            vas_script_hash_path.touch()
            vas_script_hash_path.write_text(
                hashlib.sha256(vas_script_path.read_bytes()).hexdigest()
            )
        else:
            logger.info("VAS script file validation successful.")


def fetch_vas_data(vas_script_path, data_path):
    logger.info("Fetching vas data...")
    _ = subprocess.run(
        ["pwsh", "-NoProfile", str(vas_script_path)], cwd=str(data_path)
    )
    logger.debug("Completed VAS data fetch.")
    vas_data_path = data_path / "BBVAS.json"

    with open(vas_data_path, "r") as f:
        raw_json = json.load(f)

    vas_data = raw_json["dataBundle"]["usageDetails"][0]

    write_json_data = {
        "vas_name": vas_data["name"],
        "vas_limit": vas_data["limit"],
        "vas_used": vas_data["used"],
        "vas_remaining": vas_data["remaining"],
        "vas_rem_perc": vas_data["percentage"],
        "exp_date": vas_data["expiry_date"],
        "rpt_time": raw_json["dataBundle"]["reported_time"],
    }
    with open(data_path / "vas_data.json", "w") as f:
        json.dump(write_json_data, f)


def get_vas_data(data_path):
    with open(data_path / "vas_data.json", "r") as f:
        return json.load(f)
