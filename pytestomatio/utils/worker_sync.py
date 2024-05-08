import time
import random
import os
import uuid

prefix = '.sync_temp_file_'
sync_run_file = '.sync_run_id'
fixed_delay = 0.01


class SyncLock:
    def __init__(self):
        self.worker_id = str(uuid.uuid4())
        self.test_run_id: str or None = None

    def lock(self) -> None:
        open(prefix + self.worker_id, 'x').close()

    def save_run_id(self, run_id: str) -> None:
        try:
            with open(sync_run_file, 'x') as f:
                f.write(run_id)
            self.test_run_id = run_id
        except FileExistsError:
            pass
        except Exception:
            pass

    def get_run_id(self) -> str or None:
        if self.test_run_id is not None:
            return self.test_run_id
        try:
            with open(sync_run_file, 'r') as f:
                self.test_run_id = f.read()
            return self.test_run_id
        except FileNotFoundError:
            return None

    def unlock(self) -> None:
        os.remove(prefix + self.worker_id)

    def clear_run_id(self) -> bool:
        file_count = len([file for file in os.listdir() if file.startswith(prefix)])
        if file_count == 0 and not os.path.exists(sync_run_file):
            return True
        try:
            with open(sync_run_file, 'w'):
                for _ in range(10_000):
                    file_count = len([file for file in os.listdir() if file.startswith(prefix)])
                    if file_count == 0:
                        break
                    time.sleep(fixed_delay)
        except PermissionError:
            return False
        except FileNotFoundError:
            return True
        try:
            os.remove(sync_run_file)
        except PermissionError:
            return False
        time.sleep(0.1)
        return True
