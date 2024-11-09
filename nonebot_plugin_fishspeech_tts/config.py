from pydantic import BaseModel
from typing import Optional, Literal
from nonebot import get_plugin_config

"""
用于定义配置文件类, 用于配置插件参数
"""


class Config(BaseModel):

    # 基础配置
    tts_is_online: bool = True
    tts_chunk_length: Literal["normal", "short", "long"] = "normal"
    tts_audio_path: str = "./data/参考音频"

    # 区分配置
    online_authorization: Optional[str] = "xxxxx"
    online_model_first: bool = True

    offline_api_url: str = "http://127.0.0.1:8080"


config = get_plugin_config(Config)
