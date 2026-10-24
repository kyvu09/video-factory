"""
Client gọi Gemini API (ưu tiên SDK chính thức `google-genai`, có kèm REST fallback,
tự động retry Exponential Backoff & chuyển model dự phòng khi máy chủ Google quá tải 503/429).
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import time
import urllib.error
import urllib.request


class GeminiAPIError(RuntimeError):
    """Lỗi khi gọi Gemini API."""


@dataclass
class GeminiResult:
    text: str
    model: str
    prompt_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


_TRANSIENT_MARKERS = (
    "503",
    "UNAVAILABLE",
    "high demand",
    "overloaded",
    "429",
    "RESOURCE_EXHAUSTED",
    "500",
    "502",
    "504",
    "INTERNAL",
    "DEADLINE_EXCEEDED",
    "timed out",
    "timeout",
    "ConnectionReset",
    "RemoteDisconnected",
)

_FALLBACK_MODELS = (
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
)


def _is_transient_error(msg: str) -> bool:
    low = (msg or "").lower()
    return any(m.lower() in low for m in _TRANSIENT_MARKERS)


class GeminiService:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.api_key = (api_key or "").strip()
        self.model = (model or "gemini-2.5-flash").strip()
        if not self.api_key:
            raise GeminiAPIError(
                "Chưa có Gemini API Key! Vui lòng nhập API Key ở khung Cấu hình Gemini."
            )

    def generate(
        self,
        system_instruction: str,
        user_prompt: str,
        temperature: float = 0.25,
        json_output: bool = False,
        max_retries: int = 4,
    ) -> GeminiResult:
        """Gọi Gemini sinh nội dung (có tự động thử lại khi gặp lỗi 503/429 quá tải tạm thời)."""
        candidate_models = [self.model] + [m for m in _FALLBACK_MODELS if m != self.model]
        last_error: Exception | None = None

        for model_idx, active_model in enumerate(candidate_models):
            # Model chính thử tối đa max_retries lần; các model dự phòng thử 2 lần nếu model chính vẫn 503
            attempts_for_model = max(1, max_retries) if model_idx == 0 else 2

            for attempt in range(1, attempts_for_model + 1):
                try:
                    return self._call_once(
                        target_model=active_model,
                        system_instruction=system_instruction,
                        user_prompt=user_prompt,
                        temperature=temperature,
                        json_output=json_output,
                    )
                except Exception as exc:
                    last_error = exc
                    err_str = str(exc)
                    if not _is_transient_error(err_str):
                        # Lỗi cố định (sai API key, sai tên model, quota cứng = 0...) -> dừng ngay
                        if model_idx == 0:
                            if isinstance(exc, GeminiAPIError):
                                raise
                            raise GeminiAPIError(f"Lỗi khi gọi Gemini API ({active_model}): {exc}") from exc
                        break

                    # Lỗi tạm thời (503 UNAVAILABLE / 429 / timeout) -> chờ backoff rồi thử lại
                    if attempt < attempts_for_model:
                        wait_sec = min(12.0, 2.0 * (1.8 ** (attempt - 1)))
                        time.sleep(wait_sec)
                    else:
                        # Chuyển sang model dự phòng tiếp theo sau 1.5s
                        time.sleep(1.5)

        if isinstance(last_error, GeminiAPIError):
            raise last_error
        raise GeminiAPIError(
            f"Máy chủ Gemini đang quá tải tạm thời (503/429) sau nhiều lần thử lại: {last_error}"
        ) from last_error

    def _call_once(
        self,
        target_model: str,
        system_instruction: str,
        user_prompt: str,
        temperature: float,
        json_output: bool,
    ) -> GeminiResult:
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            return self._generate_via_rest(
                target_model=target_model,
                system_instruction=system_instruction,
                user_prompt=user_prompt,
                temperature=temperature,
                json_output=json_output,
            )

        try:
            client = genai.Client(api_key=self.api_key)
            cfg_kwargs: dict = {
                "system_instruction": system_instruction,
                "temperature": temperature,
            }
            if json_output:
                cfg_kwargs["response_mime_type"] = "application/json"

            response = client.models.generate_content(
                model=target_model,
                contents=user_prompt,
                config=types.GenerateContentConfig(**cfg_kwargs),
            )
            text = (response.text or "").strip()
            if not text:
                raise GeminiAPIError("Gemini trả về phản hồi rỗng (503/empty). Hãy thử lại.")

            usage = getattr(response, "usage_metadata", None)
            p_tok = int(getattr(usage, "prompt_token_count", 0) or 0) if usage else 0
            c_tok = int(getattr(usage, "candidates_token_count", 0) or 0) if usage else 0
            t_tok = int(getattr(usage, "total_token_count", 0) or (p_tok + c_tok)) if usage else 0

            return GeminiResult(
                text=text,
                model=target_model,
                prompt_tokens=p_tok,
                output_tokens=c_tok,
                total_tokens=t_tok,
            )
        except GeminiAPIError:
            raise
        except Exception as exc:
            raise GeminiAPIError(f"Lỗi khi gọi Gemini API ({target_model}): {exc}") from exc

    def _generate_via_rest(
        self,
        target_model: str,
        system_instruction: str,
        user_prompt: str,
        temperature: float = 0.25,
        json_output: bool = False,
    ) -> GeminiResult:
        """Phương án dự phòng qua HTTPS chuẩn nếu môi trường chưa cài `google-genai`."""
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{target_model}:generateContent?key={self.api_key}"
        )
        gen_cfg: dict = {"temperature": temperature}
        if json_output:
            gen_cfg["responseMimeType"] = "application/json"

        payload = {
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": gen_cfg,
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            detail = err.read().decode("utf-8", errors="ignore")
            raise GeminiAPIError(f"HTTP {err.code} từ Gemini API ({target_model}): {detail[:400]}") from err
        except Exception as exc:
            raise GeminiAPIError(f"Lỗi kết nối tới Gemini API ({target_model}): {exc}") from exc

        candidates = data.get("candidates") or []
        if not candidates:
            raise GeminiAPIError(f"Gemini không trả về kết quả: {data}")

        parts = (candidates[0].get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts).strip()
        usage = data.get("usageMetadata") or {}
        p_tok = int(usage.get("promptTokenCount", 0) or 0)
        c_tok = int(usage.get("candidatesTokenCount", 0) or 0)
        t_tok = int(usage.get("totalTokenCount", p_tok + c_tok) or 0)

        return GeminiResult(
            text=text,
            model=target_model,
            prompt_tokens=p_tok,
            output_tokens=c_tok,
            total_tokens=t_tok,
        )
