""""""
import hashlib
import logging
import time

from pathlib import Path
from queue import Queue, Empty

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from globals import DATA_FILE_NAME, DEBOUNCE_SECONDS

logger = logging.getLogger(__name__)

class Handler(FileSystemEventHandler):
    def __init__(self, changes: Queue):
        self.changes = changes

    def handle(self, path, is_directory):
        if is_directory:
            return

        file = Path(path)

        if (
            file.name.casefold() == DATA_FILE_NAME.casefold()
            and file.parent.name.casefold() == "savedvariables"
            and file.parent.parent.parent.name.casefold() == "account"
        ):
            self.changes.put(file)

    def on_modified(self, event):
        self.handle(event.src_path, event.is_directory)

    def on_created(self, event):
        self.handle(event.src_path, event.is_directory)

    def on_moved(self, event):
        self.handle(event.dest_path, event.is_directory)

def process_file(path: Path, data: bytes):
    """Temporary implementation; parser/uploader comes later."""
    data = path.read_bytes()
    logging.info("Read %s (%d bytes)", path, len(data))

    # TODO: Parse Lua
    # TODO: Convert to JSON
    # TODO: Upload to server


def watch(wow_path):
    account_dir = wow_path / "WTF" / "Account"

    if not account_dir.is_dir():
        raise FileNotFoundError(
            f"Account directory not found: {account_dir}"
        )

    changes = Queue()
    pending = {}
    last_hashes = {}

    handler = Handler(changes)
    observer = Observer()

    observer.schedule(
        handler,
        str(account_dir),
        recursive=True
    )

    observer.start()
    logging.info("Watching %s", account_dir)

    # Process files that already exist on startup.
    for file in account_dir.glob(
        f"*/SavedVariables/{DATA_FILE_NAME}"
    ):
        changes.put(file)

    try:
        while True:
            try:
                file = changes.get(timeout=5)
                pending[file] = time.monotonic()
            except Empty:
                pass

            now = time.monotonic()

            for file, changed_at in list(pending.items()):
                if now - changed_at < DEBOUNCE_SECONDS:
                    continue

                del pending[file]

                if not file.is_file():
                    continue

                try:
                    data = file.read_bytes()
                    digest = hashlib.sha256(data).hexdigest()

                    if last_hashes.get(file) == digest:
                        continue

                    process_file(file, data)
                    last_hashes[file] = digest

                except Exception:
                    logger.exception("Failed to process %s", file)
                    pending[file] = time.monotonic()
    finally:
        observer.stop()
        observer.join()
