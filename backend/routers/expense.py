from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pydantic import BaseModel
from typing import Optional
import os
import re
import base64
import json
import tempfile
import asyncio
from io import BytesIO
from datetime import datetime
from PIL import Image
from openai import OpenAI

router = APIRouter()

MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY") or "sk-cp-Y2t5UcQLEBGxSN3NPMSoTsWBX6vZjm2gNVppN0kZ51bRrReigD3oAMrpL2tAaDkmxAA_fW4YSxQb-e-bWRIsQX9LbBoyEeW89gVyS9sjK3X7t38FU7lzDj0"
ai_client = OpenAI(
    api_key=MINIMAX_API_KEY,
    base_url="https://api.minimax.chat/v1",
)

# 智谱视觉模型客户端
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY") or "f630398278ad4c40bcdcf5fbdf0e4f8c.4AaGpVZ9oJzVnGo2"
zhipu_client = OpenAI(
    api_key=ZHIPU_API_KEY,
    base_url="https://open.bigmodel.cn/api/paas/v4",
)

MAX_IMAGE_WIDTH = 1200
THUMBNAIL_WIDTH = 200


def compress_image(img: Image.Image, max_width: int) -> Image.Image:
    if img.mode != 'RGB':
        img = img.convert('RGB')
    if img.width <= max_width:
        return img
    ratio = max_width / img.width
    new_height = int(img.height * ratio)
    return img.resize((max_width, new_height), Image.LANCZOS)


def image_to_base64(img: Image.Image, fmt: str = "PNG") -> str:
    if img.mode != 'RGB':
        img = img.convert('RGB')
    buf = BytesIO()
    img.save(buf, format=fmt)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def resize_for_thumbnail(img: Image.Image) -> Image.Image:
    if img.width <= THUMBNAIL_WIDTH:
        return img
    ratio = THUMBNAIL_WIDTH / img.width
    new_height = int(img.height * ratio)
    return img.resize((THUMBNAIL_WIDTH, new_height), Image.LANCZOS)


async def extract_pages_from_pdf(file_bytes: bytes, filename: str) -> list[dict]:
    try:
        import fitz
    except ImportError:
        raise HTTPException(status_code=500, detail="PyMuPDF 未安装，请运行: pip install PyMuPDF")

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF 解析失败: {str(e)}")

    pages = []
    for i in range(len(doc)):
        page = doc[i]
        mat = fitz.Matrix(2, 2)  # 2x zoom for better quality
        clip = page.rect
        pix = page.get_pixmap(matrix=mat, clip=clip)
        img_bytes = pix.tobytes("jpeg")
        img = Image.open(BytesIO(img_bytes)).convert("RGB")
        thumb = resize_for_thumbnail(img)
        pages.append({
            "source_file": filename,
            "page_num": i + 1,
            "image": img,
            "thumbnail_b64": image_to_base64(thumb),
        })
    doc.close()
    return pages


async def extract_page_from_image(file_bytes: bytes, filename: str) -> dict:
    try:
        img = Image.open(BytesIO(file_bytes)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"图片解析失败: {str(e)}")

    thumb = resize_for_thumbnail(img)
    return {
        "source_file": filename,
        "page_num": 1,
        "image": img,
        "thumbnail_b64": image_to_base64(thumb),
    }


async def verify_page(page: dict, client: OpenAI) -> dict:
    import logging
    logger = logging.getLogger("expense")
    img = page["image"]
    print(f"[DEBUG] image size: {img.size}, mode: {img.mode}", flush=True)
    logger.info(f"[verify_page] image size: {img.size}, mode: {img.mode}")
    compressed = compress_image(img, MAX_IMAGE_WIDTH)
    print(f"[DEBUG] compressed size: {compressed.size}", flush=True)
    logger.info(f"[verify_page] compressed size: {compressed.size}")
    img_b64 = image_to_base64(compressed, fmt="PNG")
    print(f"[DEBUG] b64 length: {len(img_b64)}", flush=True)
    logger.info(f"[verify_page] b64 length: {len(img_b64)}")

    system_prompt = "你是一个票据凭证审核专家，直接看图返回审核结果JSON。"
    user_prompt = """仔细看这张图片，返回JSON格式的审核结果：
{"type":"类型","description":"内容描述","has_stamp":true/false,"has_signature":true/false,"has_applicant":true/false,"approval_status":"已通过/审批中/未知","date":"YYYY-MM-DD或null","amount":数字或null}

直接返回JSON，不要其他内容。"""

    try:
        import logging
        logger = logging.getLogger("expense")
        print(f"[DEBUG] calling Zhipu AI API for {page.get('source_file', 'unknown')}, img_b64_len={len(img_b64)}", flush=True)
        logger.info(f"[verify_page] calling Zhipu AI API...")
        print(f"[DEBUG] using model: glm-5v-turbo", flush=True)

        # 使用智谱 glm-5v-turbo 进行图片识别
        response = zhipu_client.chat.completions.create(
            model="glm-5v-turbo",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{img_b64}"},
                        },
                        {
                            "type": "text",
                            "text": user_prompt
                        }
                    ]
                }
            ],
            max_tokens=2048
        )
        content = response.choices[0].message.content or ""
        # glm-5v-turbo 可能把回复放在 reasoning_content 字段
        if not content and hasattr(response.choices[0].message, 'reasoning_content'):
            content = response.choices[0].message.reasoning_content or ""
        try:
            safe_content = content[:500].encode('utf-8', errors='replace').decode('utf-8', errors='replace')
            print(f"[DEBUG] AI raw response (first 500): {safe_content}", flush=True)
        except Exception:
            print(f"[DEBUG] AI raw response (first 500): <content with unicode chars>", flush=True)
        logger.info(f"[verify_page] AI response received, content length: {len(content)}")
        content = re.sub(
            r"<think>.*?</think>", "", response.choices[0].message.content or "", flags=re.DOTALL
        ).strip()

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        # 清理不可见控制字符
        content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', content)

        try:
            result = json.loads(content)
        except json.JSONDecodeError as je:
            # 尝试找到 JSON 对象并修复截断问题
            parsed = None
            try:
                stack = []
                start = -1
                for i, c in enumerate(content):
                    if c == '{':
                        stack.append(i)
                    elif c == '}':
                        if stack:
                            start = stack.pop()
                            if not stack:
                                potential = content[start:i+1]
                                try:
                                    parsed = json.loads(potential)
                                except json.JSONDecodeError:
                                    pass
                                break
            except Exception:
                pass

            if parsed:
                result = parsed
            else:
                result = {
                    "has_stamp": False,
                    "has_signature": False,
                    "date": None,
                    "type": "其他",
                    "amount": None,
                    "description": f"AI解析失败: {str(je)[:100].encode('utf-8', errors='replace').decode('utf-8', errors='replace')}",
                }
    except Exception as e:
        err_str = str(e)
        try:
            err_str.encode('gbk')
        except UnicodeEncodeError:
            err_str = err_str.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
        result = {
            "has_stamp": False,
            "has_signature": False,
            "date": None,
            "type": "其他",
            "amount": None,
            "description": f"AI调用失败: {err_str[:80]}",
        }

    page["ai_result"] = result
    return page


EXEMPT_KEYWORDS = [
    "火车票", "高铁票", "机票", "电子客票", "登机牌",
    "支付宝", "微信支付", "银行转账", "支付截图",
    "银联", "云闪付", "收钱码", "付款码",
    "会议通知", "活动通知",
]


def is_exempt_page(ai_result: dict) -> bool:
    desc = (ai_result.get("description") or "") + (ai_result.get("type") or "")
    return any(kw in desc for kw in EXEMPT_KEYWORDS)


def is_page_passed(ai_result: dict) -> bool:
    if is_exempt_page(ai_result):
        return True
    # 审批截图类型：有申请人 + 已通过 = 合格
    if ai_result.get("type") in ("申请单", "审批截图") and \
       ai_result.get("has_applicant") and \
       ai_result.get("approval_status") == "已通过":
        return True
    return ai_result.get("has_stamp", False) or ai_result.get("has_signature", False)


def sort_key(p: dict):
    d = p.get("date")
    if d is None:
        return ("zzz", p["source_file"], p["page_num"])
    return (d, p["source_file"], p["page_num"])


@router.post("/expense/check-and-merge")
async def check_and_merge(files: list[UploadFile] = File(...)):
    """
    上传报销凭证图片/PDF，AI逐页审核，返回审核结果。
    """
    all_pages: list[dict] = []

    for file in files:
        ext = os.path.splitext(file.filename or "unknown")[1].lower()
        file_bytes = await file.read()

        if ext == ".pdf":
            pages = await extract_pages_from_pdf(file_bytes, file.filename or "unknown.pdf")
            all_pages.extend(pages)
        elif ext in (".jpg", ".jpeg", ".bmp", ".png"):
            page = await extract_page_from_image(file_bytes, file.filename or "unknown.jpg")
            all_pages.append(page)

    if not all_pages:
        raise HTTPException(status_code=400, detail="未找到有效的图片或PDF页面")

    tasks = [verify_page(p, ai_client) for p in all_pages]
    verified_pages = await asyncio.gather(*tasks)

    passed: list = []
    rejected: list = []
    total_amount = 0.0

    for p in verified_pages:
        ai = p["ai_result"]
        page_info = {
            "source_file": p["source_file"],
            "page_num": p["page_num"],
            "thumbnail": p["thumbnail_b64"],
            "description": ai.get("description", ""),
            "date": ai.get("date"),
            "type": ai.get("type", "其他"),
            "amount": ai.get("amount"),
            "has_applicant": ai.get("has_applicant", False),
            "approval_status": ai.get("approval_status", "未知"),
        }

        if is_page_passed(ai):
            passed.append(page_info)
            if ai.get("amount") is not None:
                try:
                    total_amount += float(ai["amount"])
                except (TypeError, ValueError):
                    pass
        else:
            reasons = []
            if ai.get("type") in ("申请单", "审批截图"):
                if not ai.get("has_applicant"):
                    reasons.append("缺少申请人")
                if ai.get("approval_status") != "已通过":
                    reasons.append("未审批通过")
            else:
                if not ai.get("has_stamp"):
                    reasons.append("缺少公章")
                if not ai.get("has_signature"):
                    reasons.append("缺少签字")
            page_info["reject_reason"] = "且".join(reasons) if reasons else "不符合报销规范"
            rejected.append(page_info)

    passed_sorted = sorted(passed, key=sort_key)
    rejected_sorted = sorted(rejected, key=sort_key)

    return {
        "passed": passed_sorted,
        "rejected": rejected_sorted,
        "summary": {
            "total": len(verified_pages),
            "passed": len(passed_sorted),
            "rejected": len(rejected_sorted),
            "total_amount": round(total_amount, 2),
        },
    }


@router.post("/expense/merge-upload")
async def merge_with_upload(
    files: list[UploadFile] = File(...),
    page_order: Optional[str] = Form(""),
):
    """
    接收文件上传，按 page_order 顺序合并为 PDF。
    page_order: 逗号分隔的 "文件名:页码" 列表，如 "a.pdf:1,a.pdf:2,b.jpg"
    """
    try:
        import img2pdf
    except ImportError:
        raise HTTPException(status_code=500, detail="img2pdf 未安装，请运行: pip install img2pdf")

    if not files:
        raise HTTPException(status_code=400, detail="没有上传文件")

    order_map: dict[str, int] = {}
    if page_order:
        for i, name in enumerate(page_order.split(",")):
            order_map[name.strip()] = i

    file_pages: list[tuple[int, bytes]] = []

    for f in files:
        ext = os.path.splitext(f.filename or "unknown")[1].lower()
        data = await f.read()

        if ext == ".pdf":
            try:
                import fitz
                doc = fitz.open(stream=data, filetype="pdf")
                for i in range(len(doc)):
                    page = doc[i]
                    mat = fitz.Matrix(2, 2)
                    pix = page.get_pixmap(matrix=mat, clip=page.rect)
                    img_bytes = pix.tobytes("jpeg")
                    key = f"{f.filename}:{i + 1}"
                    idx = order_map.get(key, len(order_map))
                    file_pages.append((idx, img_bytes))
                doc.close()
            except Exception:
                continue
        elif ext in (".jpg", ".jpeg", ".bmp", ".png"):
            idx = order_map.get(f.filename or "", len(order_map))
            file_pages.append((idx, data))

    if not file_pages:
        raise HTTPException(status_code=400, detail="没有有效的页面")

    file_pages.sort(key=lambda x: x[0])
    img_bytes_list = [p[1] for p in file_pages]

    try:
        pdf_bytes = img2pdf.convert(img_bytes_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 合并失败: {str(e)}")

    buf = BytesIO(pdf_bytes)
    buf.seek(0)

    from fastapi.responses import Response
    return Response(
        content=buf.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=expense_merged.pdf"},
    )
