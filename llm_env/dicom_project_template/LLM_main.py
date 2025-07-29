"""Utility script for handling JLK brain CT data and generating reports."""

from __future__ import annotations

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import uuid
import re

from .dataset_utils import _collection_path
from .file_utils import extract_zip
from .image_processing import convert_all_dicom_to_png_parallel
from .openai_utils import JLK_ICH, JLK_CTL, JLK_CTI, JLK_WMHC
from tqdm import tqdm


def run_jlk_solutions(non_mask_dir: Path, item: Path) -> list[dict]:
    def add_identifier(dir_path: Path) -> None:
        if not dir_path or not dir_path.is_dir():
            return
        for idx, img in enumerate(sorted(dir_path.glob("*.png"))):
            if re.search(r"_[0-9a-f]{8}\.png$", img.name):
                continue
            new_name = f"{img.stem}_{idx}_{uuid.uuid4().hex[:8]}{img.suffix}"
            img.rename(img.with_name(new_name))

    def run(name: str, func):
        ai_dir = next(
            (p for p in item.iterdir() if p.is_dir() and name in p.name), None
        )
        result = func(non_mask_dir, ai_dir)
        add_identifier(ai_dir)
        return {
            "solution": name,
            "result": result,
            "non_mask_dir": str(non_mask_dir),
            "ai_dir": str(ai_dir) if ai_dir else None,
        }

    solution_funcs = [
        ("JLK-ICH", JLK_ICH),
        ("JLK-CTL", JLK_CTL),
        ("JLK-CTI", JLK_CTI),
        ("JLK-WMHC", JLK_WMHC),
    ]

    results = []
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(run, name, func) for name, func in solution_funcs]
        for f in as_completed(futures):
            try:
                results.append(f.result())
            except Exception as e:
                print(f"[ERROR] {e}")
    return results


def main(zip_file, output_root: str | Path = "/media/dicom_outputs") -> None:
    """Run the DICOM to PNG pipeline and JLK solutions.

    Parameters
    ----------
    zip_file : str | Path
        Path to the uploaded zip file.
    output_root : str | Path, optional
        Directory under which the output images will be stored. Defaults to
        ``/media/dicom_outputs``.
    """

    zip_path = Path(zip_file)
    extract_path = extract_zip(zip_path)
    if not extract_path:
        return

    df = _collection_path(extract_path)

    output_root = Path(output_root)
    os.makedirs(output_root, exist_ok=True)
    output_dir = output_root / f"{zip_path.stem}_output_images"

    if not output_dir.exists():
        convert_all_dicom_to_png_parallel(df, output_dir)

    AI_result = []
    for item in tqdm(list(output_dir.iterdir())):
        if item.is_dir():
            non_mask_dir = item / "Non_mask"
            if non_mask_dir.exists() and any(non_mask_dir.iterdir()):
                AI_result.extend(run_jlk_solutions(non_mask_dir, item))

    return AI_result


if __name__ == "__main__":  # pragma: no cover - manual execution
    rr = main(
        "/home/yjpark/llm_env/dicom_project_template/DCM_REQUEST_2025-07-23-05-16-58-465027_0.zip"
    )
