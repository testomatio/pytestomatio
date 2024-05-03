import time
import random
import os
import uuid
from collections import namedtuple

temp_file = 'sync_temp_file_'
Lock = namedtuple('lock', ['uuid', 'is_first'])


def start_file_sync_lock(prefix: str = temp_file) -> Lock:
    uid = str(uuid.uuid4())
    time.sleep(random.randint(1, 1000) / 1000)
    is_first = len([file for file in os.listdir() if file.startswith(prefix)]) == 0
    open(prefix + uid, 'x').close()
    return Lock(uuid=uid, is_first=is_first)


def stop_file_sync_lock_is_last(id: str, prefix: str = temp_file) -> bool:
    os.remove(prefix + id)
    if len([file for file in os.listdir() if file.startswith(prefix)]) == 0:
        return True
