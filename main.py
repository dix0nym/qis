import json
import logging
import logging.config
from pathlib import Path
from types import SimpleNamespace as Namespace

from tabulate import tabulate

from qislib import QisLib
from qislib.mailhelper import MailHelper

logger = logging.getLogger("qis-checker")

def setup_logging(default_path='logging.json', default_level=logging.INFO):
    """Setup logging configuration"""
    log_path = Path("logs")
    if not log_path.exists():
        log_path.mkdir(parents=True, exist_ok=True)
    config_path = Path(default_path)
    if config_path.exists():
        with config_path.open('rt') as config_file:
            config = json.load(config_file)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)


def load_config():
    """load json_config file"""
    config_path = Path("config.json")
    if not config_path.exists():
        exit("couldn't find config.json")
    return json.load(config_path.open('r'), object_hook=lambda d: Namespace(**d))


def create_table(diff, header, fmt=None):
    values = [[entry[k.lower()] for k in header] for entry in diff]
    table = tabulate(values, header, tablefmt=fmt)
    return table

def notify(updated, config, fnames):
    """notify as defined in config"""
    logger.info(f"email notification {'en' if config.email else 'dis'}abled")
    if config.email:
        email_formats = config.format
        mailhelper = MailHelper(config.sender)
        logger.info(f"found {len(email_formats)} email formats")
        for eformat in email_formats:
            table = create_table(updated, eformat.header, fmt="html")
            imgs = fnames if config.graph else None
            for receiver in eformat.email:
                result = mailhelper.send_mail(
                    receiver, "Veränderung im QIS", table, fnames=imgs)
                if result:
                    logger.info(f'notificate {", ".join(eformat.email)}')
                else:
                    logger.error(
                        f'failed to sent email to {", ".join(eformat.email)}')
    else:
        table = create_table(
            updated, ["Nr", "Modul", "Semester", "Note"], fmt="simple")
        logger.info(table)

def main():
    setup_logging()
    config = load_config()
    logger.info("loaded configuration")
    qis = QisLib(config)
    logger.info("initialized qislib")
    success = qis.login()
    logger.info(f"qis login: {'successfull' if success else 'failed'}")
    if not success:
        return
    logger.info("checking modules for changes")
    updated = qis.check()
    if not updated:
        logger.info("no changes detected")
        return
    logger.info(f"found {len(updated)} changes")
    # generate plots
    logger.info(f"generating plots")
    names = qis.create_plots(updated)
    # generate and send emails
    notify(updated, config.notification, names)
    qis.logout()
    logger.info("qis logout")

if __name__ == "__main__":
    main()
