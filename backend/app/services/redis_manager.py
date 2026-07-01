"""Redis 管理模块，提供消息发布/订阅和持久化存储。
支持无 Redis 降级模式（仅文件存储，无实时推送）。
"""

import redis.asyncio as aioredis
from typing import Optional
import json
from pathlib import Path
from app.config.setting import settings
from app.schemas.response import Message
from app.utils.log_util import logger


class RedisManager:
    """Redis 连接管理器，负责消息发布/订阅和任务消息持久化。

    如果 Redis 不可用，将降级为文件存储模式（仅保存消息到文件，
    不提供实时 Pub/Sub 推送）。
    """
    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self._client: Optional[aioredis.Redis] = None
        self._fallback_mode = False
        # 创建消息存储目录
        self.messages_dir = Path("logs/messages")
        self.messages_dir.mkdir(parents=True, exist_ok=True)

    async def get_client(self) -> Optional[aioredis.Redis]:
        """获取 Redis 客户端连接，失败时返回 None 并切换到降级模式。"""
        if self._fallback_mode:
            return None
        if self._client is None:
            try:
                self._client = aioredis.Redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    max_connections=settings.REDIS_MAX_CONNECTIONS,
                )
            except Exception as e:
                logger.warning(f"Redis 连接失败，降级为文件存储模式: {e}")
                self._fallback_mode = True
                return None
        try:
            await self._client.ping()  # type: ignore[reportGeneralTypeIssues]
            logger.info(f"Redis 连接成功: {self.redis_url}")
            return self._client
        except Exception as e:
            logger.warning(f"Redis Ping 失败，降级为文件存储模式: {e}")
            self._fallback_mode = True
            self._client = None
            return None

    async def set(self, key: str, value: str):
        """设置 Redis 键值对（降级模式下无操作）。"""
        client = await self.get_client()
        if client is not None:
            try:
                await client.set(key, value)
                await client.expire(key, 36000)
            except Exception as e:
                logger.warning(f"Redis set 失败: {e}")

    async def _save_message_to_file(self, task_id: str, message: Message):
        """将消息保存到文件中。"""
        try:
            self.messages_dir.mkdir(exist_ok=True)
            file_path = self.messages_dir / f"{task_id}.json"
            messages = []
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    messages = json.load(f)
            message_data = message.model_dump()
            messages.append(message_data)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存消息到文件失败: {str(e)}")

    async def publish_message(self, task_id: str, message: Message):
        """发布消息到特定任务的频道并保存到文件。

        降级模式下仅保存到文件（WebSocket 无法收到实时推送）。
        """
        # 始终保存到文件
        await self._save_message_to_file(task_id, message)

        client = await self.get_client()
        if client is None:
            return

        channel = f"task:{task_id}:messages"
        try:
            message_json = message.model_dump_json()
            await client.publish(channel, message_json)
            logger.debug(
                f"消息已发布到频道 {channel}: mes_type:{message.msg_type}"
            )
        except Exception as e:
            logger.error(f"发布消息失败: {e}")

    async def subscribe_to_task(self, task_id: str):
        """订阅特定任务的消息（降级模式下返回 None）。"""
        client = await self.get_client()
        if client is None:
            return None
        try:
            pubsub = client.pubsub()
            await pubsub.subscribe(f"task:{task_id}:messages")
            return pubsub
        except Exception as e:
            logger.warning(f"Redis 订阅失败: {e}")
            return None

    async def close(self):
        """关闭 Redis 连接。"""
        if self._client:
            try:
                await self._client.close()
            except Exception:
                pass
            self._client = None


redis_manager = RedisManager()
