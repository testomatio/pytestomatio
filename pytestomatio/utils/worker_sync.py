import time
import random
import os
import uuid
from collections import namedtuple

temp_file = 'sync_temp_file_'
sync_run_file = 'sync_run_file'

Lock = namedtuple('lock', ['uuid', 'is_first'])


def start_file_sync_lock(prefix: str = temp_file) -> Lock:
    uid = str(uuid.uuid4())
    time.sleep(random.randint(1, 1000) / 1000)
    is_first = len([file for file in os.listdir() if file.startswith(prefix)]) == 0
    open(prefix + uid, 'x').close()
    return Lock(uuid=uid, is_first=is_first)


def save_test_run_id(run_id: str, sync_file: str = sync_run_file) -> None:
    with open(sync_file + run_id, 'x') as f:
        f.write(run_id)


def get_test_run_id(sync_file: str = sync_run_file) -> str or None:
    if not os.path.exists(sync_file):
        return None
    with open(sync_file, 'r') as f:
        return f.read()


def stop_file_sync_lock_is_last(id: str, prefix: str = temp_file) -> bool:
    os.remove(prefix + id)
    if len([file for file in os.listdir() if file.startswith(prefix)]) == 0:
        return True


def remove_sync_run(sync_file: str = sync_run_file) -> None:
    try:
        os.remove(sync_file)
    except Exception:
        pass
