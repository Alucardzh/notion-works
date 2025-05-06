'''
# @ Author: Alucard
# @ Create Time: 2025-05-06 13:43:38
# @ Modified by: Alucard
# @ Modified time: 2025-05-06 13:45:54
# @ Description: 用于处理markdown文件，将内容按段落分割并合并，确保每个段落不超过指定字符数
'''

import re
from pathlib import Path
import asyncio
from typing import List, Optional, Union
import aiofiles


class ParagraphsMerga:
    """_summary_
    """

    def __init__(self, file_path: Union[str, Path], max_chars: int = 1000):
        """_summary_

        Args:
            file_path (str, Path): markdown文件的路径或者内容
            max_chars (int, optional): 每个合并后段落的最大字符数. 默认为1000
        """
        self.file = file_path
        self.max_chars = max_chars

    @staticmethod
    def split_into_paragraphs(content: str) -> List[str]:
        """
        将内容按段落分割成list

        Args:
            content (str): 要分割的文本内容

        Returns:
            List[str]: 分割后的段落列表，每个元素是一个段落

        Note:
            使用正则表达式匹配段落，保留markdown格式
            过滤掉空段落
        """
        # 使用正则表达式匹配段落，保留markdown格式
        paragraphs = re.split(r'\n\s*\n', content)
        # 过滤空段落
        return [p.strip() for p in paragraphs if p.strip()]

    def read_markdown_file(self) -> str:
        """
        读取markdown文件内容

        Args:
            file_path (str): markdown文件的路径

        Returns:
            str: 文件内容

        Raises:
            FileNotFoundError: 当文件不存在时抛出
            UnicodeDecodeError: 当文件编码不是UTF-8时抛出
        """
        if Path(self.file).is_file():
            with open(self.file, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        return self.file

    async def async_read_markdown_file(self) -> str:
        """
        异步读取markdown文件内容

        Args:
            file_path (str): markdown文件的路径

        Returns:
            str: 文件内容

        Raises:
            FileNotFoundError: 当文件不存在时抛出
            UnicodeDecodeError: 当文件编码不是UTF-8时抛出
        """
        if Path(self.file).is_file():
            async with aiofiles.open(self.file, 'r', encoding='utf-8') as f:
                content = await f.read()
            return content
        return self.file

    def merge_paragraphs(self, paragraphs: List[str]) -> List[str]:
        """
        合并段落，确保每个合并后的段落不超过最大字符数

        Args:
            paragraphs (List[str]): 要合并的段落列表
            max_chars (int): 每个合并后段落的最大字符数

        Returns:
            List[str]: 合并后的段落列表

        Note:
            如果单个段落超过最大字符数，将保持原样
            合并时会保留段落间的空行（\n\n）
        """
        merged: List[str] = []
        current_paragraph: str = ""

        for p in paragraphs:
            # 如果当前段落加上新段落不超过最大字符数，则合并
            if len(current_paragraph) + len(p) + 2 <= self.max_chars:
                if current_paragraph:
                    current_paragraph += "\n\n" + p
                else:
                    current_paragraph = p
            else:
                # 如果当前段落不为空，添加到结果中
                if current_paragraph:
                    merged.append(current_paragraph)
                # 如果单个段落超过最大字符数，需要进一步处理
                if len(p) > self.max_chars:
                    # 这里可以添加更复杂的处理逻辑，比如按句子分割
                    merged.append(p)
                else:
                    current_paragraph = p

        # 添加最后一个段落
        if current_paragraph:
            merged.append(current_paragraph)

        return merged

    async def async_merge_paragraphs(self, paragraphs: List[str]) -> List[str]:
        """
        异步合并段落，确保每个合并后的段落不超过最大字符数

        Args:
            paragraphs (List[str]): 要合并的段落列表

        Returns:
            List[str]: 合并后的段落列表

        Note:
            如果单个段落超过最大字符数，将保持原样
            合并时会保留段落间的空行（\n\n）
        """
        merged: List[str] = []
        current_paragraph: str = ""

        # 使用异步处理大量段落
        async def process_paragraph(p: str) -> Optional[str]:
            nonlocal current_paragraph
            if len(current_paragraph) + len(p) + 2 <= self.max_chars:
                if current_paragraph:
                    current_paragraph += "\n\n" + p
                else:
                    current_paragraph = p
                return None
            else:
                if current_paragraph:
                    result = current_paragraph
                    current_paragraph = p if len(p) <= self.max_chars else ""
                    return result
                return p if len(p) <= self.max_chars else p

        # 并发处理段落
        tasks = [process_paragraph(p) for p in paragraphs]
        results = await asyncio.gather(*tasks)

        # 过滤None值并添加结果
        merged.extend([r for r in results if r is not None])

        # 添加最后一个段落
        if current_paragraph:
            merged.append(current_paragraph)

        return merged

    def main(self) -> List[str]:
        """
        处理markdown文件的主函数

        Returns:
            List[str]: 处理后的段落列表

        Note:
            完整的处理流程：
            1. 读取文件内容
            2. 按段落分割
            3. 合并段落
        """
        # 读取文件
        content = self.read_markdown_file()

        # 分割段落
        paragraphs = self.split_into_paragraphs(content)

        # 合并段落
        merged_paragraphs = self.merge_paragraphs(paragraphs)

        return merged_paragraphs

    async def async_main(self) -> List[str]:
        """
        异步处理markdown文件的主函数

        Returns:
            List[str]: 处理后的段落列表

        Note:
            完整的处理流程：
            1. 异步读取文件内容
            2. 按段落分割
            3. 异步合并段落
        """
        # 异步读取文件
        content = await self.async_read_markdown_file()

        # 分割段落
        paragraphs = self.split_into_paragraphs(content)

        # 异步合并段落
        merged_paragraphs = await self.async_merge_paragraphs(paragraphs)

        return merged_paragraphs
