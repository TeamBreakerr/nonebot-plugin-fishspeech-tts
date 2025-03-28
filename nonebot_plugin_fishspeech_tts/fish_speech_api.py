from pathlib import Path
from typing import ClassVar

import ormsgpack
from httpx import (
    AsyncClient,
    HTTPStatusError,
    RequestError,
)
from nonebot.log import logger

from .config import config
from .exception import APIException, FileHandleException, HTTPException
from .files import (
    extract_text_by_filename,
    get_path_speaker_list,
    get_speaker_audio_path,
)
from .request_params import ChunkLength, ServeReferenceAudio, ServeTTSRequest

API_URL = config.offline_api_url + "/v1/tts"
PATH_AUDIO = Path(config.tts_audio_path)
MAX_NEW_TOKENS = config.tts_max_new_tokens
IS_STREAM = config.tts_is_stream


class FishSpeechAPI:
    api_url: str = API_URL
    path_audio: Path = PATH_AUDIO
    _headers: ClassVar[dict] = {
        "content-type": "application/msgpack",
    }

    @classmethod
    async def generate_servettsrequest(
        cls,
        text: str,
        speaker_name: str,
        chunk_length: ChunkLength = ChunkLength.NORMAL,
        # TODO: speed: int = 0,
    ) -> ServeTTSRequest:
        """
        生成TTS请求

        Args:
            text: 文本
            speaker_name: 说话人姓名
            chunk_length: 请求语音的切片长度
            TODO:speed: 语速
        Returns:
            ServeTTSRequest: TTS请求
        """

        references = []
        try:
            speaker_audio_path = get_speaker_audio_path(cls.path_audio, speaker_name)
        except FileHandleException as e:
            raise APIException(str(e)) from e
        for audio in speaker_audio_path:
            audio_bytes = audio.read_bytes()
            ref_text = extract_text_by_filename(audio.name)
            references.append(ServeReferenceAudio(audio=audio_bytes, text=ref_text))
        return ServeTTSRequest(
            text=text,
            chunk_length=chunk_length.value,
            format="wav",
            references=references,
            normalize=True,
            opus_bitrate=64,
            latency="normal",
            max_new_tokens=MAX_NEW_TOKENS,
            top_p=0.7,
            repetition_penalty=1.2,
            temperature=0.7,
            streaming=IS_STREAM,
            mp3_bitrate=64,
        )

    @classmethod
    async def generate_tts(cls, request: ServeTTSRequest) -> bytes:
        """
        获取TTS音频

        Args:
            request: TTS请求
        Returns:
            bytes: TTS音频二进制数据
        """
        try:
            async with AsyncClient() as client:
                response = await client.post(
                    cls.api_url,
                    headers=cls._headers,
                    content=ormsgpack.packb(
                        request, option=ormsgpack.OPT_SERIALIZE_PYDANTIC
                    ),
                    timeout=60,
                )
                return response.content
        except (
            HTTPStatusError,
            RequestError,
        ) as e:
            logger.error(f"获取TTS音频失败: {e}")
            raise HTTPException(
                f"{e}\n获取TTS音频超时, 你的接口配置错误或者文本过长"
            ) from e
        except Exception as e:
            raise APIException(f"{e}\n获取TTS音频失败, 检查API后端") from e

    @classmethod
    def get_speaker_list(cls) -> list[str]:
        """
        获取说话人列表

        Returns:
            list[str]: 说话人列表
        """
        try:
            return get_path_speaker_list(cls.path_audio)
        except FileHandleException as e:
            raise APIException(str(e)) from e
