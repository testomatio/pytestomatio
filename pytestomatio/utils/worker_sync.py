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

    def lock(self) -> bool:
        '''
        :return: True if this worker is the first to lock the file, False otherwise
        '''
        time.sleep(random.randint(1, 1000) / 1000)
        is_first = len([file for file in os.listdir() if file.startswith(prefix)]) == 0
        open(prefix + self.worker_id, 'x').close()
        return is_first

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

        time.sleep(fixed_delay)
        try:
            self.test_run_id = self._read_run_file()
            return self.test_run_id
        except FileNotFoundError:
            time.sleep(fixed_delay)
            try:
                self.test_run_id = self._read_run_file()
                return self.test_run_id
            except FileNotFoundError:
                return None

    def _read_run_file(self) -> str:
        with open(sync_run_file, 'r') as f:
            return f.read()

    def unlock(self) -> bool:
        '''
        :return: True if this worker is the last to unlock the file, False otherwise
        '''
        os.remove(prefix + self.worker_id)
        is_last = len([file for file in os.listdir() if file.startswith(prefix)]) == 0
        return is_last

    def clear_run_id(self) -> None:
        try:
            os.remove(sync_run_file)
        except FileNotFoundError:
            pass
