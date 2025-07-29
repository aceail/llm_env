import base64
import logging
import os
from io import BytesIO
from pathlib import Path
from typing import Optional

from PIL import Image

from .report_models import ImagingReport
from dotenv import load_dotenv
load_dotenv() 
try:  # Optional dependency
    from openai import OpenAI
except Exception:  # pragma: no cover - openai might not be available
    OpenAI = None


if OpenAI:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
else:  # pragma: no cover - when openai is unavailable
    client = None


def pil_to_base64(image_path: str) -> str:
    """Return the base64-encoded string of the given image."""

    image = Image.open(image_path)
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def safe_load_image(image_path: str) -> Optional[str]:
    if not os.path.exists(image_path):
        logging.warning(f"이미지 파일이 존재하지 않음: {image_path}")
        return None
    try:
        return f"data:image/png;base64,{pil_to_base64(image_path)}"
    except Exception as e:
        logging.error(f"이미지 변환 실패: {image_path} - {e}")
        return None


def JLK_ICH(mask_path: Path, path: Path) -> Optional[str]:
    try:

        content_blocks = []

        desc_masked = (
            "Summary_0000_0 : JLK ICH는 비조영 CT에서 모든 유형의 뇌출혈을 탐지하는 AI 알고리즘입니다. 뇌출혈 의심 영역은 붉은색 마스크로 표시되며, 환자 단위의 뇌출혈 확률값과 전체 뇌영역에서의 뇌출혈 부피 정보가 함께 제공됩니다."
        )
        img_masked = safe_load_image(str(path / "Summary_0000.png"))
        if img_masked:
            content_blocks.append({"type": "input_text", "text": desc_masked})
            content_blocks.append({"type": "input_image", "image_url": img_masked})

        desc_nomask = (
            "non_mask : Summary_0000_0과 동일한 영상이며, 붉은색 마스크를 제거한 버전입니다. (정확한 비교를 위해 mask만 제외되었습니다.)"
        )
        nomask_files = sorted(mask_path.glob("non_mask*.png"))
        img_nomask = safe_load_image(str(nomask_files[0])) if nomask_files else None
        if img_nomask:
            content_blocks.append({"type": "input_text", "text": desc_nomask})
            content_blocks.append({"type": "input_image", "image_url": img_nomask})

        if not content_blocks:
            logging.error("유효한 이미지가 없어 요청을 수행할 수 없습니다.")
            return None

        if client is None:
            logging.error("OpenAI client not available")
            return None

        response = client.responses.parse(
            model="gpt-4.1",
            prompt={"id": "pmpt_687ee31179fc819091e852e25eaca6c20399e215f5db1fab", "version": "2"},
            input=[{"role": "user", "content": content_blocks}],
            reasoning={},
            max_output_tokens=8192,
            store=True,
            text_format=ImagingReport,
        )

        if not hasattr(response, "output_parsed"):
            logging.error("output_parsed 항목이 응답에 존재하지 않음")
            return None

        return response.output_parsed.model_dump_json(indent=2)
    except Exception as e:
        logging.exception(f"JLK_ICH 실행 중 오류 발생: {e}")
        return None



def JLK_CTL(mask_path: Path, path: Path) -> Optional[str]:
    try:
        content_blocks = []

        desc_0 = (
            "JLK-CTL Summary_0000: NCCT 영상을 기반으로 LVO를 예측하는 알고리즘의 결과. "
            "좌우 APSECT 영역을 modification 해서 M1, M2, M3, M4, M5, M6, striatocapsular 영역으로 나누고 "
            "LVO 판단에 가장 중요한 정보인 modified ASEPCTS 영역의 HU difference 를 보여주고, "
            "hyperdense artery sign 의 유무와 부피, 길이 정보를 표시. "
            "LVO score는 12.0 이상인 경우 LVO를 의심할 수 있으며 점수가 높을수록 LVO 확률이 높음. "
            "LVO 확률에 따라 0–10 (unlikely), 11–20 (less likely), 21–50 (possible), and 51–100 (suggestive)로 구분하고 있음. "
            "HU에 차이가 있어도 차이가 크지 않을 경우, LVO 확률이 낮을 수 있음."
        )
        img_0 = safe_load_image(str(path / "JLK-CTL Summary_0000.png"))
        if img_0:
            content_blocks.append({"type": "input_text", "text": desc_0})
            content_blocks.append({"type": "input_image", "image_url": img_0})


        desc_1 = "JLK-CTL Summary_0001: NCCT 영상을 분석해서 나온 ASPECT 점수 결과와 영역별 HU 의 평균"
        img_1 = safe_load_image(str(path / "JLK-CTL Summary_0001.png"))
        if img_1:
            content_blocks.append({"type": "input_text", "text": desc_1})
            content_blocks.append({"type": "input_image", "image_url": img_1})

        desc_2 = (
            "JLK-CTL Summary_0002: LVO 예측 알고리즘인 JLK CTL 이 LVO를 예측하는데 사용된 feature importance 와 "
            "NIHSS 를 고려했을 때 확률, ASPECT 영역의 net-water uptake 결과"
        )
        img_2 = safe_load_image(str(path / "JLK-CTL Summary_0002.png"))
        if img_2:
            content_blocks.append({"type": "input_text", "text": desc_2})
            content_blocks.append({"type": "input_image", "image_url": img_2})

        if not content_blocks:
            logging.error("유효한 이미지가 없어 요청을 수행할 수 없습니다.")
            return None

        if client is None:
            logging.error("OpenAI client not available")
            return None

        response = client.responses.parse(
            model="gpt-4.1",
            prompt={"id": "pmpt_687ee31179fc819091e852e25eaca6c20399e215f5db1fab", "version": "2"},
            input=[{"role": "user", "content": content_blocks}],
            reasoning={},
            max_output_tokens=8192,
            store=True,
            text_format=ImagingReport,
        )

        if not hasattr(response, "output_parsed"):
            logging.error("output_parsed 항목이 응답에 존재하지 않음")
            return None

        return response.output_parsed.model_dump_json(indent=2)
    except Exception as e:
        logging.exception(f"JLK_CTL 실행 중 오류 발생: {e}")
        return None



def JLK_CTI(mask_path: Path, path: Path) -> Optional[str]:
    try:

        content_blocks = []

        desc_masked = (
            "JLK-CTI Summary_0000: JLK CTI는 NCCT 기반 뇌경색 의심 영역을 탐지하는 AI 알고리즘입니다. 원본 영상 위에 병변 의심 영역을 마스크로 표현하며, 마스크 색상은 병변이 없는 반대쪽 반구의 평균 HU와 비교하여 병변 쪽 voxel의 HU 감소 정도를 반영합니다."
        )
        img_masked = safe_load_image(str(path / "JLK-CTI Summary_0000.png"))
        if img_masked:
            content_blocks.append({"type": "input_text", "text": desc_masked})
            content_blocks.append({"type": "input_image", "image_url": img_masked})

        desc_nomask = (
            "non_mask : JLK-CTI Summary_0000과 동일한 영상이며, 붉은색 마스크를 제거한 버전입니다. (정확한 비교를 위해 mask만 제외되었습니다.)"
        )
        nomask_files = sorted(mask_path.glob("non_mask*.png"))
        img_nomask = safe_load_image(str(nomask_files[0])) if nomask_files else None
        if img_nomask:
            content_blocks.append({"type": "input_text", "text": desc_nomask})
            content_blocks.append({"type": "input_image", "image_url": img_nomask})

        if not content_blocks:
            logging.error("유효한 이미지가 없어 요청을 수행할 수 없습니다.")
            return None

        if client is None:
            logging.error("OpenAI client not available")
            return None

        response = client.responses.parse(
            model="gpt-4.1",
            prompt={"id": "pmpt_687ee31179fc819091e852e25eaca6c20399e215f5db1fab", "version": "2"},
            input=[{"role": "user", "content": content_blocks}],
            reasoning={},
            max_output_tokens=8192,
            store=True,
            text_format=ImagingReport,
        )

        if not hasattr(response, "output_parsed"):
            logging.error("output_parsed 항목이 응답에 존재하지 않음")
            return None

        return response.output_parsed.model_dump_json(indent=2)
    except Exception as e:
        logging.exception(f"JLK_ICH 실행 중 오류 발생: {e}")
        return None


def JLK_WMHC(mask_path: Path, path: Path) -> Optional[str]:
    try:

        content_blocks = []

        desc_masked = (
            "Summary_0000_0 : JLK WMHC는 비조영 CT 기반 백질변성 탐지 AI 알고리즘입니다. 백질변성 의심 영역은 파란색 마스크로 표시되며, 여런 HU threshold 를 적용한 백질변성의 부피 정보를 제공합니다."
        )
        img_masked = safe_load_image(str(path / "Summary_0000.png"))
        if img_masked:
            content_blocks.append({"type": "input_text", "text": desc_masked})
            content_blocks.append({"type": "input_image", "image_url": img_masked})

        desc_nomask = (
            "non_mask : Summary_0000_0과 동일한 영상이며, 파란색 마스크를 제거한 버전입니다. (정확한 비교를 위해 mask만 제외되었습니다.)"
        )
        nomask_files = sorted(mask_path.glob("non_mask*.png"))
        img_nomask = safe_load_image(str(nomask_files[0])) if nomask_files else None
        if img_nomask:
            content_blocks.append({"type": "input_text", "text": desc_nomask})
            content_blocks.append({"type": "input_image", "image_url": img_nomask})

        if not content_blocks:
            logging.error("유효한 이미지가 없어 요청을 수행할 수 없습니다.")
            return None

        if client is None:
            logging.error("OpenAI client not available")
            return None

        response = client.responses.parse(
            model="gpt-4.1",
            prompt={"id": "pmpt_687ee31179fc819091e852e25eaca6c20399e215f5db1fab", "version": "2"},
            input=[{"role": "user", "content": content_blocks}],
            reasoning={},
            max_output_tokens=8192,
            store=True,
            text_format=ImagingReport,
        )

        if not hasattr(response, "output_parsed"):
            logging.error("output_parsed 항목이 응답에 존재하지 않음")
            return None

        return response.output_parsed.model_dump_json(indent=2)
    except Exception as e:
        logging.exception(f"JLK_ICH 실행 중 오류 발생: {e}")
        return None

def JLK_CVL(mask_path: Path, path: Path) -> Optional[str]:
    try:

        content_blocks = []

        desc_masked = (
            "JLK-CVL: Summary_0000_0 : JLK CVL는 비조영 CT 기반 만성 혈관성 병변 탐지 AI 알고리즘입니다. 작은 열공 뇌경색이 아닌, 피질이 침범되어 있거나 백질에 있는 큰 만성 뇌혈관질환 병변을 탐지합니다. 의심 영역은 HU의 평균값에 따라 노란색~빨간색 마스크로 표시됩니다. "
        )
        img_masked = safe_load_image(str(path / "JLK-CTI Summary_0000.png"))
        if img_masked:
            content_blocks.append({"type": "input_text", "text": desc_masked})
            content_blocks.append({"type": "input_image", "image_url": img_masked})

        desc_nomask = (
            "non_mask : Summary_0000_0과 동일한 영상이며, 마스크를 제거한 버전입니다. (정확한 비교를 위해 mask만 제외되었습니다.)"
        )
        nomask_files = sorted(mask_path.glob("non_mask*.png"))
        img_nomask = safe_load_image(str(nomask_files[0])) if nomask_files else None
        if img_nomask:
            content_blocks.append({"type": "input_text", "text": desc_nomask})
            content_blocks.append({"type": "input_image", "image_url": img_nomask})

        if not content_blocks:
            logging.error("유효한 이미지가 없어 요청을 수행할 수 없습니다.")
            return None

        if client is None:
            logging.error("OpenAI client not available")
            return None

        response = client.responses.parse(
            model="gpt-4.1",
            prompt={"id": "pmpt_687ee31179fc819091e852e25eaca6c20399e215f5db1fab", "version": "2"},
            input=[{"role": "user", "content": content_blocks}],
            reasoning={},
            max_output_tokens=8192,
            store=True,
            text_format=ImagingReport,
        )

        if not hasattr(response, "output_parsed"):
            logging.error("output_parsed 항목이 응답에 존재하지 않음")
            return None

        return response.output_parsed.model_dump_json(indent=2)
    except Exception as e:
        logging.exception(f"JLK_ICH 실행 중 오류 발생: {e}")
        return None
