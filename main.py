import json
import logging
from pathlib import Path
from types import SimpleNamespace as Namespace

import tabulate

from qislib import QisLib
from qislib.mailhelper import MailHelper

logger = logging.getLogger(__name__)


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
    values = [[entry.get_attr(k.lower()) for k in header] for entry in diff]
    table = tabulate(values, header, tablefmt=fmt)
    return table


def notify(updated, config, fnames):
    """notify as defined in config"""
    if config.sendMail:
        email_formats = config.notification.format
        mailhelper = MailHelper(config.sender)
        for eformat in email_formats:
            table = create_table(updated, eformat.header, fmt="html")
            imgs = fnames if config.notification.graph else None
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
    config = load_config()
    qis = QisLib(config)
    success = qis.login()
    if not success:
        logger.error("failed to login")
        return
    updated = qis.check()
    if not updated:
        logger.info("nothing changed")
        return
    # generate plots
    names = qis.create_plots(updated)
    # generate and send emails
    notify(updated, config, names)


if __name__ == "__main__":
    main()
