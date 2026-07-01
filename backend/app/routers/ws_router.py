"""WebSocket 路由模块，提供实时任务消息推送。
支持无 Redis 降级模式（通过轮询文件系统获取消息）。
"""

import asyncio
import json
import os

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.schemas.response import SystemMessage
from app.services.redis_manager import redis_manager
from app.services.ws_manager import ws_manager
from app.utils.common_utils import ensure_safe_task_id
from app.utils.log_util import logger

router = APIRouter()


def _is_websocket_closed(websocket: WebSocket) -> bool:
    return (
        websocket.client_state == WebSocketState.DISCONNECTED
        or websocket.application_state == WebSocketState.DISCONNECTED
    )


def _is_closed_send_error(error: Exception) -> bool:
    text = str(error)
    return (
        "Cannot call \"send\" once a close message has been sent" in text
        or "Unexpected ASGI message 'websocket.send'" in text
    )


def _load_messages_from_file(task_id: str) -> list[dict]:
    """Load messages from the file-based message store."""
    file_path = os.path.join("logs", "messages", f"{task_id}.json")
    if not os.path.isfile(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, FileNotFoundError):
        return []


@router.websocket("/task/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    try:
        safe_task_id = ensure_safe_task_id(task_id)
    except ValueError:
        logger.warning(f"WebSocket task_id 非法: {task_id}")
        await websocket.close(code=1008, reason="Invalid task id")
        return

    logger.info(f"WebSocket 尝试连接 task_id: {safe_task_id}")

    await ws_manager.connect(websocket)
    logger.info(f"WebSocket connected for task: {safe_task_id}")

    # 尝试订阅 Redis 频道
    pubsub = await redis_manager.subscribe_to_task(safe_task_id)
    use_redis = pubsub is not None

    if use_redis:
        logger.debug(f"Subscribed to Redis channel: task:{safe_task_id}:messages")
    else:
        logger.info(f"降级模式：task {safe_task_id} 使用文件轮询代替 Redis")

    # 文件轮询必要状态
    last_message_count = 0
    if not use_redis:
        messages = _load_messages_from_file(safe_task_id)
        last_message_count = len(messages)
        # 发送已有的历史消息
        for msg in messages:
            try:
                await ws_manager.send_personal_message_json(msg, websocket)
            except Exception:
                pass

    try:
        while True:
            if _is_websocket_closed(websocket):
                logger.info(f"WebSocket 已关闭，停止转发 task_id: {safe_task_id}")
                break
            try:
                if use_redis:
                    msg = await pubsub.get_message(ignore_subscribe_messages=True)
                    if msg:
                        try:
                            msg_dict = json.loads(msg["data"])
                        except Exception as e:
                            logger.error(f"Error parsing websocket payload: {e}")
                            if _is_websocket_closed(websocket):
                                break
                            try:
                                await ws_manager.send_personal_message_json(
                                    SystemMessage(
                                        content="实时消息解析失败，已忽略异常数据。",
                                        type="error",
                                    ).model_dump(),
                                    websocket,
                                )
                            except WebSocketDisconnect:
                                logger.info("WebSocket disconnected while sending parse error notice")
                                break
                            except RuntimeError as send_error:
                                if _is_closed_send_error(send_error):
                                    logger.info("WebSocket 已关闭，跳过解析失败提示发送")
                                    break
                                raise
                        else:
                            try:
                                await ws_manager.send_personal_message_json(msg_dict, websocket)
                            except WebSocketDisconnect:
                                logger.info("WebSocket disconnected while sending message")
                                break
                            except RuntimeError as send_error:
                                if _is_closed_send_error(send_error):
                                    logger.info(f"WebSocket 已关闭，停止发送后续消息 task_id: {safe_task_id}")
                                    break
                                raise
                else:
                    # 降级模式：轮询文件系统
                    messages = _load_messages_from_file(safe_task_id)
                    if len(messages) > last_message_count:
                        for msg in messages[last_message_count:]:
                            try:
                                await ws_manager.send_personal_message_json(msg, websocket)
                            except WebSocketDisconnect:
                                logger.info("WebSocket disconnected during file poll send")
                                break
                            except RuntimeError as send_error:
                                if _is_closed_send_error(send_error):
                                    break
                                raise
                        last_message_count = len(messages)

                await asyncio.sleep(0.1)

            except WebSocketDisconnect:
                logger.info("WebSocket disconnected")
                break
            except Exception as e:
                if _is_closed_send_error(e) or _is_websocket_closed(websocket):
                    logger.info(f"WebSocket 发送通道已关闭，结束循环 task_id: {safe_task_id}")
                    break
                logger.error(f"Error in websocket loop: {e}")
                await asyncio.sleep(1)
                continue

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if use_redis:
            try:
                await pubsub.unsubscribe(f"task:{safe_task_id}:messages")
            except Exception:
                pass
        ws_manager.disconnect(websocket)
        logger.info(f"WebSocket connection closed for task: {safe_task_id}")
