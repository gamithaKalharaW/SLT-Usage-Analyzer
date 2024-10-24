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
import subprocess
import json
import hashlib


from sltusageanalyzer.utils import (
    fetch_vas_data,
    setup_data_folder,
    get_saved_data,
    get_vas_data,
)
from sltusageanalyzer.checkhealth import check_health
from sltusageanalyzer.appserver import server_func


ASSETS_PATH = f'{ IR.files("sltusageanalyzer") }/assets'
DATA_PATH = (
    Path("".join([os.environ["HOMEDRIVE"], os.environ["HOMEPATH"]]))
    / ".sltanalyzer"
)
PROCESSED_JSON_PATH = DATA_PATH / "wifi_data.json"


CFG_PATH = DATA_PATH / ".analyzer.config"
MAIN_SCRIPT_PATH = DATA_PATH / "analyzer_pwsh.ps1"
VAS_SCRIPT_PATH = DATA_PATH / "vas_pwsh.ps1"
LOG_PATH = DATA_PATH / "analyzer.log"
CFG_HASH_PATH = DATA_PATH / ".analyzer.config.hash"
MAIN_SCRIPT_HASH_PATH = DATA_PATH / "analyzer_pwsh.ps1.hash"
VAS_SCRIPT_HASH_PATH = DATA_PATH / "vas_pwsh.ps1.hash"

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
    return summary()


@app.route("/summary")
def summary():
    json_data = get_saved_data(processed_json_path=PROCESSED_JSON_PATH)
    rpt_time = json_data["report_time"]
    total_dt = json_data["total"]
    std_dt = json_data["standard"]
    free_dt = json_data["free"]
    vas_dt = json_data["vas"]

    total_perc = total_dt["rem_perc"]

    logger.debug("Rendering total page")
    return render_template(
        "total.html",
        report_time=rpt_time,
        total_perc=total_perc,
        std_limit=f"{ std_dt["limit"] }GB",
        free_limit=f"{ free_dt["limit"] }GB",
        vas_limit=f"{ vas_dt["limit"] }GB",
        std_rem=std_dt["remaining"],
        std_rem_perc=std_dt["rem_perc"],
        free_rem=free_dt["remaining"],
        free_rem_perc=free_dt["rem_perc"],
        vas_rem=vas_dt["remaining"],
        vas_rem_perc=vas_dt["rem_perc"],
    )


@app.route("/usage/<tp>")
def usage(tp):
    json_data = get_saved_data(processed_json_path=PROCESSED_JSON_PATH)
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
    json_data = get_vas_data(data_path=DATA_PATH)

    logger.debug("Rendering vas page")
    return render_template(
        "vas.html",
        vas_name=json_data["vas_name"],
        vas_limit=json_data["vas_limit"],
        used=json_data["vas_used"],
        rem=json_data["vas_remaining"],
        total_perc=json_data["vas_rem_perc"],
        exp_date=json_data["exp_date"],
        report_time=json_data["rpt_time"],
    )


@app.route("/refresh")
def refresh():
    logger.info("Updating json data")
    save_processed_data()
    logger.info("Refreshing page")
    return summary()


@app.route("/close", methods=["GET"])  # type: ignore
def close():
    logger.debug("App closed by keymap")
    close_application()


def get_json_data():
    logger.debug("Started data fetching.")
    _ = subprocess.run(
        [
            "pwsh",
            "-NoProfile",
            str(MAIN_SCRIPT_PATH),
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
    fetch_vas_data(vas_script_path=VAS_SCRIPT_PATH, data_path=DATA_PATH)

    with open(PROCESSED_JSON_PATH, "w") as jf:
        json.dump(out_data, jf)
        logger.debug(f"Saving processed json data @ {PROCESSED_JSON_PATH}")


def update_config_file():
    config_vals = dotenv_values(CFG_PATH)
    for k, v in config_vals.items():
        config_vals[k] = input(f"{k} ({v}): ") or v

    CFG_PATH.unlink()
    CFG_HASH_PATH.unlink()
    logger.debug("Removing old files")

    CFG_PATH.touch()
    CFG_HASH_PATH.touch()
    logger.debug("Creating new files")

    wrt_str = "\n".join([f"{k}={v}" for k, v in config_vals.items()])

    CFG_PATH.write_text(wrt_str)
    logger.debug("Writing new values to config file")
    CFG_HASH_PATH.write_text(hashlib.sha256(CFG_PATH.read_bytes()).hexdigest())
    logger.debug("Writing new hash to config hash file")
    logger.info("Config file updated.")


@click.command()
@click.option(
    "--debug", is_flag=True, default=False, help="Run with DEBUG log-level"
)
@click.option(
    "--port", "-p", default=3000, type=int, help="Port to run on. Default: 3000"
)
@click.option(
    "--checkhealth",
    "-ch",
    is_flag=True,
    default=False,
    help="Check application health",
)
@click.option(
    "--update-config",
    "-uc",
    is_flag=True,
    default=False,
    help="Update config file",
)
@click.option(
    "--reload",
    "-r",
    is_flag=True,
    default=False,
    help="Fetch new data before app startup",
)
@click.option(
    "--server", "-s", default=None, type=str, help="Run app as web server"
)
@click.version_option(IM.version("sltusageanalyzer"))
def main(
    debug: bool,
    port: int,
    checkhealth: bool,
    update_config: bool,
    reload: bool,
    server: str | None,
):
    logger.remove()
    logger.add(LOG_PATH, level="DEBUG", retention="3 days")

    if debug:
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.add(sys.stderr, level="INFO")

    if checkhealth:
        exit(
            check_health(
                cfg_path=CFG_PATH,
                cfg_hash_path=CFG_HASH_PATH,
                script_path=MAIN_SCRIPT_PATH,
                script_hash_path=MAIN_SCRIPT_HASH_PATH,
            )
        )

    if server:
        logger.info("Running app as web server")
        logger.debug(f"Running on {server}:{port}")
        server_func(app=app, host=server, port=port)  # type: ignore
        exit(0)

    if update_config:
        logger.info("Updating config file...")
        try:
            update_config_file()
            logger.info("Config file updated.")
            exit(0)
        except Exception as e:
            logger.exception(e)
            exit(-1)

    if reload:
        logger.info("Reloading data...")
        save_processed_data()

    setup_data_folder(
        data_path=DATA_PATH,
        cfg_path=CFG_PATH,
        cfg_hash_path=CFG_HASH_PATH,
        assets_path=ASSETS_PATH,
        script_path=MAIN_SCRIPT_PATH,
        script_hash_path=MAIN_SCRIPT_HASH_PATH,
        vas_script_path=VAS_SCRIPT_PATH,
        vas_script_hash_path=VAS_SCRIPT_HASH_PATH,
    )
    browser_path = Path(
        dotenv_values(DATA_PATH / ".analyzer.config")["BROWSER_PATH"]  # type: ignore
    )
    if not browser_path.exists():
        logger.error(
            "Configured browser not found. Switching to default browser..."
        )
        UI = FlaskUI(
            app=app,
            server=server_func,  # type: ignore
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
            server=server_func,  # type: ignore
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
