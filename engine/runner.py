"""Batch execution engine for AudioCheck.

Kept completely decoupled from Streamlit to allow safe execution in headless CLI,
background workers, and web UI without multiprocessing spawn deadlocks.
"""
from __future__ import annotations

import os
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from typing import Any, Callable

from audiocheck_core import QCSettings, analyze_audio


def analyze_single_item(
    item: tuple[str, bytes | Path | str], settings_dict: dict[str, Any]
) -> tuple[dict[str, Any] | None, dict[str, str] | None]:
    name, data_or_path = item
    settings = QCSettings(**settings_dict)
    try:
        if isinstance(data_or_path, (str, Path)):
            data = Path(data_or_path).read_bytes()
        else:
            data = data_or_path
        result = analyze_audio(data, name, settings)
        return result, None
    except Exception as exc:
        return None, {"filename": name, "error": str(exc)}


class BatchRunner:
    """Executes audio QC across batches of audio files."""

    def __init__(self, max_workers: int | None = None, prefer_threads: bool = False) -> None:
        self.max_workers = max_workers or min(16, (os.cpu_count() or 1))
        self.prefer_threads = prefer_threads

    def run(
        self,
        files: list[tuple[str, bytes | Path | str]],
        settings: QCSettings,
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
        """Analyze a list of (filename, data) audio items.

        Returns (results, failures).
        """
        if not files:
            return [], []

        results: list[dict[str, Any]] = []
        failures: list[dict[str, str]] = []
        settings_dict = settings.to_dict()
        total = len(files)

        if total == 1:
            res, err = analyze_single_item(files[0], settings_dict)
            if res:
                results.append(res)
            if err:
                failures.append(err)
            if progress_callback:
                progress_callback(1, 1, files[0][0])
            return results, failures

        executor_cls = ThreadPoolExecutor if self.prefer_threads else ProcessPoolExecutor

        completed_count = 0
        indexed_results: list[tuple[int, dict[str, Any]]] = []
        indexed_failures: list[tuple[int, dict[str, str]]] = []

        try:
            with executor_cls(max_workers=min(self.max_workers, total)) as executor:
                future_to_info = {
                    executor.submit(analyze_single_item, item, settings_dict): (idx, item[0])
                    for idx, item in enumerate(files)
                }
                for future in as_completed(future_to_info):
                    idx, item_name = future_to_info[future]
                    completed_count += 1
                    try:
                        res, err = future.result()
                        if res:
                            indexed_results.append((idx, res))
                        if err:
                            indexed_failures.append((idx, err))
                    except Exception as exc:
                        indexed_failures.append((idx, {"filename": item_name, "error": str(exc)}))
                    if progress_callback:
                        progress_callback(completed_count, total, item_name)
        except Exception:
            # Fallback to in-process execution if process pool encounters issues
            indexed_results.clear()
            indexed_failures.clear()
            for idx, item in enumerate(files):
                res, err = analyze_single_item(item, settings_dict)
                if res:
                    indexed_results.append((idx, res))
                if err:
                    indexed_failures.append((idx, err))
                if progress_callback:
                    progress_callback(idx + 1, total, item[0])

        indexed_results.sort(key=lambda pair: pair[0])
        indexed_failures.sort(key=lambda pair: pair[0])

        return [res for _, res in indexed_results], [err for _, err in indexed_failures]
