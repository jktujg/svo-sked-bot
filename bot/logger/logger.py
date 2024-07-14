import json
import logging.config
import os
from pathlib import Path


def create_logfile_dirs(conf: dict) -> None:
    for handler_name, handler_value in conf.get('handlers', {}).items():
        if file_path := handler_value.get('filename'):
            log_dir = Path(file_path).parent
            if not log_dir.exists():
                os.mkdir(log_dir)


with open(Path(__file__).parent / 'logger_conf.json', 'r') as log_conf:
    log_config = json.load(log_conf)
    create_logfile_dirs(log_config)
    logging.config.dictConfig(log_config)

logger = logging.getLogger()
