"""Utility script for handling JLK brain CT data and generating reports."""

from __future__ import annotations

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from .dataset_utils import _collection_path
from .file_utils import extract_zip
from .image_processing import convert_all_dicom_to_png_parallel
from .openai_utils import JLK_ICH, JLK_CTL, JLK_CTI, JLK_WMHC
from tqdm import tqdm


def run_jlk_solutions(non_mask_dir: Path, item: Path) -> list[dict]:
    def run(name: str, func):
        ai_dir = next((p for p in item.iterdir() if p.is_dir() and name in p.name), None)
        return {
            "solution": name,
            "result": func(non_mask_dir, ai_dir),
            "non_mask_dir": str(non_mask_dir),
            "ai_dir": str(ai_dir) if ai_dir else None
        }

    solution_funcs = [
        ("JLK-ICH", JLK_ICH),
        ("JLK-CTL", JLK_CTL),
        ("JLK-CTI", JLK_CTI),
        ("JLK-WMHC", JLK_WMHC)
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


def main(zip_file) -> None:
    """Example main routine."""

    zip_path = Path(zip_file)
    extract_path = extract_zip(zip_path)
    if not extract_path:
        return

    df = _collection_path(extract_path)
    output_dir = Path(f"{Path(zip_file).stem}_output_images")
    convert_all_dicom_to_png_parallel(df, output_dir)

    AI_result = []
    for item in tqdm(list(output_dir.iterdir())[:3]):
        if item.is_dir():
            non_mask_dir = item / "Non_mask"
            if non_mask_dir.exists() and any(non_mask_dir.iterdir()):
                AI_result.extend(run_jlk_solutions(non_mask_dir, item))

    return AI_result
if __name__ == "__main__":  # pragma: no cover - manual execution
    rr = main("/home/yjpark/llm_env/dicom_project_template/DCM_REQUEST_2025-07-23-05-16-58-465027_0.zip")
