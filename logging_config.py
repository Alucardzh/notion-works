'''
 # @ Author: Alucard
 # @ Create Time: 2025-04-17 23:40:17
 # @ Modified by: Alucard
 # @ Modified time: 2025-04-17 23:41:13
 # @ Description:
 '''

import logging
import logging.handlers
from pathlib import Path


def setup_logger(name: str = None) -> logging.Logger:
    """配置并返回一个日志记录器

    Args:
        name: 日志记录器名称，默认为None（使用root logger）

    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # 如果已经有处理器，不重复添加
    if logger.handlers:
        return logger

    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器 - 按天轮转
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_dir / 'notion_api.log',
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 文件处理器 - 按大小轮转
    size_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / 'notion_api.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    size_handler.setFormatter(formatter)
    logger.addHandler(size_handler)

    return logger


# 配置根日志记录器
setup_logger()
