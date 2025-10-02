import os
import random
import traceback
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, MessageSegment
from nonebot.log import logger
from nonebot.rule import to_me
from nonebot.exception import FinishedException

# 可配置参数
COMMAND_ALIASES = {"狐狸图片", "随机狐狸", "来只狐狸", "fox图"}
FOX_FOLDER_NAME = "fox"
SUPPORTED_IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg")
MAX_RETRY = 2

# 命令触发器
send_fox = on_command(
    "狐狸图片",
    aliases=COMMAND_ALIASES,
    priority=5,
    block=True
)


@send_fox.handle()
async def handle_random_fox_image(bot: Bot, event: MessageEvent):
    plugin_dir = os.path.dirname(os.path.abspath(__file__))
    fox_img_dir = os.path.join(plugin_dir, FOX_FOLDER_NAME)
    logger.info(f"插件目录：{plugin_dir} | fox图片目录：{fox_img_dir}")

    try:
        # 检查fox文件夹是否存在
        if not os.path.exists(fox_img_dir):
            err_msg = f"❌ 未找到 {FOX_FOLDER_NAME} 文件夹！\n请在插件目录（{plugin_dir}）下创建该文件夹并放入图片"
            logger.error(err_msg)
            await send_fox.send(err_msg)
            return
        
        # 检查文件夹可读性
        if not os.access(fox_img_dir, os.R_OK):
            err_msg = f"❌ 无 {FOX_FOLDER_NAME} 文件夹读取权限！\n执行命令授权：chmod 755 {fox_img_dir}"
            logger.error(err_msg)
            await send_fox.send(err_msg)
            return
        
        # 筛选有效图片
        valid_images = []
        for filename in os.listdir(fox_img_dir):
            file_path = os.path.join(fox_img_dir, filename)
            if filename.startswith(".") or os.path.isdir(file_path) or os.path.islink(file_path):
                logger.debug(f"跳过无效文件：{file_path}")
                continue
            if file_path.lower().endswith(SUPPORTED_IMAGE_EXTS) and os.access(file_path, os.R_OK):
                valid_images.append(file_path)
        
        # 检查是否有可用图片
        if not valid_images:
            err_msg = f"❌ {FOX_FOLDER_NAME} 文件夹中无可用图片！\n支持格式：{SUPPORTED_IMAGE_EXTS}"
            logger.error(err_msg)
            await send_fox.send(err_msg)
            return
        
        # 随机选图
        selected_img = None
        for _ in range(MAX_RETRY):
            try:
                selected_img = random.choice(valid_images)
                if os.path.exists(selected_img) and os.access(selected_img, os.R_OK):
                    break
                logger.warning(f"图片无效，重试选图：{selected_img}")
            except Exception as e:
                logger.error(f"选图失败，重试：{str(e)}")
        
        if not selected_img:
            await send_fox.send("❌ 选图失败，请稍后再试！")
            return
        logger.info(f"随机选中图片：{selected_img}")

        # 构造正确路径
        image_url = f"file://{selected_img}"
        logger.debug(f"图片发送路径：{image_url}")

        # 直接发送图片（已删除「找到狐狸图片啦～」提示）
        image_msg = MessageSegment.image(image_url)
        await send_fox.finish(image_msg)

    # 捕获FinishedException
    except FinishedException:
        logger.debug("流程已正常终止（FinishedException），无需处理")
    # 其他错误处理
    except PermissionError as e:
        err_msg = f"❌ 权限错误：{str(e)}\n请执行授权命令：\nchmod 755 {fox_img_dir}\nchmod 644 {fox_img_dir}/*"
        logger.error(err_msg)
        await send_fox.send(err_msg)
    except UnicodeDecodeError as e:
        err_msg = f"❌ 文件名编码错误：{str(e)}\n请修改含特殊字符/中文的文件名（如 1.jpg 代替 狐狸图.jpg）"
        logger.error(err_msg)
        await send_fox.send(err_msg)
    except Exception as e:
        err_msg = "❌ 发图失败，请查看机器人日志~"
        logger.error(f"发图全流程错误：{str(e)} | 堆栈：{traceback.format_exc()}")
        await send_fox.send(err_msg)