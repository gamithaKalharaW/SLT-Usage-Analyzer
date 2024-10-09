from flask import Flask, render_template
from flaskwebgui import FlaskUI, close_application
from loguru import logger
from dotenv import dotenv_values
import click


from pathlib import Path
import importlib.resources as IR
import importlib.metadata as IM
import os
import sys
import getpass
import subprocess
import json
import hashlib


ASSETS_PATH = f'{ IR.files("sltusageanalyzer") }/assets'
DATA_PATH = (
    Path("".join([os.environ["HOMEDRIVE"], os.environ["HOMEPATH"]]))
    / ".sltanalyzer"
)
PROCESSED_JSON_PATH = DATA_PATH / "wifi_data.json"


CFG_PATH = DATA_PATH / ".analyzer.config"
SCRIPT_PATH = DATA_PATH / "analyzer_pwsh.ps1"
LOG_PATH = DATA_PATH / "analyzer.log"
CFG_HASH_PATH = DATA_PATH / ".analyzer.config.hash"
SCRIPT_HASH_PATH = DATA_PATH / "analyzer_pwsh.ps1.hash"

app = Flask(
    __name__,
    template_folder=f'{ IR.files("sltusageanalyzer") }/template',
    static_folder=f'{IR.files("sltusageanalyzer")}/static',
)


@app.route("/")
def home():
    if not PROCESSED_JSON_PATH.exists():
        logger.debug("Processed json data not found. Saving data...")
        save_processed_data()
    return total()


@app.route("/total")
def total():
    json_data = get_saved_data()
    rpt_time = json_data["report_time"]
    total_dt = json_data["total"]
    std_dt = json_data["standard"]
    free_dt = json_data["free"]

    total_perc = total_dt["rem_perc"]
    tot_perc_angle = int(round(360 * (total_perc / 100)))

    stand_used, stand_rem = std_dt["used"], std_dt["remaining"]
    std_rem_perc = int(round((stand_rem / std_dt["limit"]) * 100))

    free_used, free_rem = free_dt["used"], free_dt["remaining"]
    free_rem_perc = int(round((free_rem / free_dt["limit"]) * 100))

    logger.debug("Rendering total page")
    return render_template(
        "total.html",
        report_time=rpt_time,
        tot_use_perc=total_perc,
        tot_use_angle=tot_perc_angle,
        stand_used=stand_used,
        stand_rem=stand_rem,
        stand_use_perc=std_rem_perc,
        free_used=free_used,
        free_rem=free_rem,
        free_use_perc=free_rem_perc,
    )


@app.route("/usage/<tp>")
def usage(tp="total"):
    json_data = get_saved_data()
    rpt_time = json_data["report_time"]

    date_str = rpt_time.split(" ")[0]
    day, mnt, year = date_str.split("-")
    day, year = int(day), int(year)
    if mnt in ["Jan", "Mar", "May", "Jul", "Aug", "Oct", "Dec"]:
        days = 31
    elif mnt in ["Apr", "Jun", "Sep", "Nov"]:
        days = 30
    else:
        if year % 4 == 0:
            days = 29
        else:
            days = 28

    usage_dt = json_data[tp.lower()]

    used, remaining = usage_dt["used"], usage_dt["remaining"]
    rem_perc = usage_dt["rem_perc"]
    rem_perc_angle = int(round(360 * (rem_perc / 100)))

    used_avg = round(used / day, 1)
    remaining_avg = round(remaining / (days - day), 1)

    calc_val = round((remaining_avg / (usage_dt["limit"] / days)) * 100)
    bar_val = int(round(80 * (calc_val / 100)))
    bar_val = 100 if bar_val > 100 else bar_val

    logger.debug(f"Rendering {tp.lower()} usage page")
    return render_template(
        "usage.html",
        tp=tp,
        report_time=rpt_time,
        used=used,
        remaining=remaining,
        rem_perc=rem_perc,
        rem_percent=70,
        rem_angle=rem_perc_angle,
        used_avg=used_avg,
        rem_avg=remaining_avg,
        calc_val=calc_val,
        bar_val=bar_val,
    )


@app.route("/vas")
def vas():
    json_data = get_saved_data()
    rpt_time = json_data["report_time"]
    vas_dt = json_data["vas"]
    used = vas_dt["used"]
    remaining = vas_dt["remaining"]
    rem_percent = vas_dt["rem_perc"]
    rem_angle = int(round(360 * (rem_percent / 100)))

    logger.debug("Rendering vas page")
    return render_template(
        "vas.html",
        report_time=rpt_time,
        used=used,
        remaining=remaining,
        rem_perc=rem_percent,
        rem_angle=rem_angle,
    )


@app.route("/refresh")
def refresh():
    logger.info("Updating json data")
    save_processed_data()
    logger.info("Refreshing page")
    return total()


@app.route("/close", methods=["GET"])  # type: ignore
def close():
    logger.debug("App closed by keymap")
    close_application()


def flask_server(**server_kwargs):
    app = server_kwargs.pop("app", None)
    server_kwargs.pop("debug", None)

    try:
        import waitress

        logger.debug("Starting waitress server")
        waitress.serve(app, **server_kwargs)
    except Exception as e:
        logger.exception(e)
        logger.error("Running app with flask server")
        app.run(**server_kwargs)


def setup_data_folder():
    if not DATA_PATH.exists():
        logger.error("Data folder not found.")
        logger.info(f"Creating data folder @ {DATA_PATH}")
        DATA_PATH.mkdir()
    else:
        logger.info(f"Data folder found @ {DATA_PATH}")

    if not CFG_PATH.exists():
        logger.error("Config file not found.")
        logger.info("Creating config file...")

        CFG_PATH.touch()
        CFG_PATH.write_text(
            __format_str(
                Path(ASSETS_PATH) / "template.config.txt",
                username=input("Enter username: "),
                password=getpass.getpass("Enter password: "),
                id=input("Enter id(94xxxxxxxxx): "),
            )
        )
        CFG_HASH_PATH.touch()
        CFG_HASH_PATH.write_text(
            hashlib.sha256(CFG_PATH.read_bytes()).hexdigest()
        )

    else:
        _saved_hash = CFG_HASH_PATH.read_text().removesuffix("\n")
        _cfg_hash = hashlib.sha256(CFG_PATH.read_bytes()).hexdigest()
        if _saved_hash != _cfg_hash:
            logger.error("Config file hash mismatch.")
            if (
                input("Would you like to reset config file?(y/n): ").lower()
                != "y"
            ):
                logger.info("Exiting...")
                exit(0)
            logger.info("Removing corrupt config file...")
            CFG_PATH.unlink()
            logger.info("Creating config file...")
            CFG_PATH.touch()
            CFG_PATH.write_text(
                __format_str(
                    Path(ASSETS_PATH) / "template.config.txt",
                    username=input("Enter username: "),
                    password=getpass.getpass("Enter password: "),
                    id=input("Enter id(94xxxxxxxxx): "),
                )
            )
            CFG_HASH_PATH.touch()
            CFG_HASH_PATH.write_text(
                hashlib.sha256(CFG_PATH.read_bytes()).hexdigest()
            )
        else:
            logger.info("Config file validation successful.")

    if not SCRIPT_PATH.exists():
        logger.info("Creating script file...")
        SCRIPT_PATH.touch()

        username = dotenv_values(CFG_PATH)["USERNAME"]
        passwd = dotenv_values(CFG_PATH)["PASSWORD"]
        id = dotenv_values(CFG_PATH)["ID"]

        SCRIPT_PATH.write_text(
            __format_str(
                Path(ASSETS_PATH) / "template.pwsh_script.txt",
                username=username,
                password=passwd,
                subscriberID=id,
            )
        )

        SCRIPT_HASH_PATH.touch()
        SCRIPT_HASH_PATH.write_text(
            hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest()
        )

    else:
        _saved_hash = SCRIPT_HASH_PATH.read_text().removesuffix("\n")
        _cfg_hash = hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest()
        if _saved_hash != _cfg_hash:
            logger.error("Script file hash mismatch.")
            if (
                input("Would you like to reset script file?(y/n): ").lower()
                != "y"
            ):
                logger.info("Exiting...")
                exit(0)
            logger.info("Removing corrupt script file...")
            SCRIPT_PATH.unlink()
            logger.info("Creating script file...")
            SCRIPT_PATH.touch()
            SCRIPT_PATH.write_text(
                __format_str(
                    Path(ASSETS_PATH) / "template.config.txt",
                    username=dotenv_values(CFG_PATH)["USERNAME"],
                    passwd=dotenv_values(CFG_PATH)["PASSWORD"],
                    id=dotenv_values(CFG_PATH)["ID"],
                )
            )
            SCRIPT_HASH_PATH.touch()
            SCRIPT_HASH_PATH.write_text(
                hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest()
            )
        else:
            logger.info("Script file validation successful.")


def get_json_data():
    logger.debug("Started data fetching.")
    _ = subprocess.run(
        [
            "pwsh",
            "-NoProfile",
            str(SCRIPT_PATH),
        ],
        cwd=str(DATA_PATH),
    )
    logger.debug("Completed fetching data.")
    json_path = DATA_PATH / "summary.json"

    with open(json_path, "r") as f:
        raw_json = json.load(f)["dataBundle"]

    rpt_time = raw_json["reported_time"]

    vas_limit = round(float((raw_json["vas_data_summary"]["limit"])), 1)
    vas_used = round(float((raw_json["vas_data_summary"]["used"])), 1)
    vas_remaining = vas_limit - vas_used

    _mpi_ud = raw_json["my_package_info"]["usageDetails"]
    _std_data = _mpi_ud[0]
    _tot_data = _mpi_ud[1]

    std_limit = round(float((_std_data["limit"])), 1)
    std_remaining = round(float((_std_data["remaining"])), 1)
    std_used = round(float((_std_data["used"])), 1)

    tot_limit = round(float((_tot_data["limit"])), 1)
    tot_remaining = round(float((_tot_data["remaining"])), 1)
    tot_used = round(float((_tot_data["used"])), 1)

    free_limit = tot_limit - std_limit
    free_remaining = round(tot_remaining - std_remaining, 1)
    free_used = round(tot_used - std_used, 1)

    return {
        "report_time": rpt_time,
        "vas": {
            "limit": vas_limit,
            "used": vas_used,
            "remaining": vas_remaining,
            "rem_perc": int(round((vas_remaining / vas_limit) * 100)),
        },
        "standard": {
            "limit": std_limit,
            "used": std_used,
            "remaining": std_remaining,
            "rem_perc": int(round((std_remaining / std_limit) * 100)),
        },
        "free": {
            "limit": free_limit,
            "used": free_used,
            "remaining": free_remaining,
            "rem_perc": int(round((free_remaining / free_limit) * 100)),
        },
        "total": {
            "limit": tot_limit,
            "used": tot_used,
            "remaining": tot_remaining,
            "rem_perc": int(round((tot_remaining / tot_limit) * 100)),
        },
    }


def save_processed_data():
    out_data = get_json_data()

    with open(PROCESSED_JSON_PATH, "w") as jf:
        json.dump(out_data, jf)
        logger.debug(f"Saving processed json data @ {PROCESSED_JSON_PATH}")


def get_saved_data():
    with open(PROCESSED_JSON_PATH, "r") as f:
        return json.load(f)


def check_health():
    click.echo(click.style("Under development", fg="red"))

    return 404


def __format_str(fp: str | Path, **kwargs):
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


@click.command()
@click.option(
    "--debug", is_flag=True, default=False, help="Run with DEBUG log-level"
)
@click.option(
    "--port", "-p", default=3000, type=int, help="Port to run on. Default: 3000"
)
@click.option("--checkhealth", "-ch", is_flag=True, default=False, help="Check application health")
@click.version_option(IM.version("sltusageanalyzer"))
def main(debug: bool, port: int, checkhealth: bool):
    logger.remove()
    logger.add(LOG_PATH, level="DEBUG")
    if debug:
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.add(sys.stderr, level="INFO")
    
    if checkhealth:
        exit( check_health() )

    setup_data_folder()
    browser_path = Path(
        dotenv_values(DATA_PATH / ".analyzer.config")["BROWSER_PATH"]  # type: ignore
    )
    if not browser_path.exists():
        logger.error(
            "Configured browser not found. Switching to default browser..."
        )
        UI = FlaskUI(
            app=app,
            server=flask_server,  # type: ignore
            server_kwargs={
                "app": app,
                "port": port,
            },
            fullscreen=False,
            width=825,
            height=570,
            on_startup=lambda: logger.info("Starting..."),
            on_shutdown=lambda: logger.info("Shutting down..."),
        )
    else:
        logger.debug(f"Using browser @ {browser_path}")
        UI = FlaskUI(
            app=app,
            server=flask_server,  # type: ignore
            server_kwargs={
                "app": app,
                "port": port,
            },
            fullscreen=False,
            width=825,
            height=570,
            browser_path=str(browser_path),
            on_startup=lambda: logger.info("Starting..."),
            on_shutdown=lambda: logger.info("Shutting down..."),
        )
    UI.run()


if __name__ == "__main__":
    main()
