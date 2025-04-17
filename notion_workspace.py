'''
 # @ Author: Alucard
 # @ Create Time: 2025-04-14 14:30:05
 # @ Description: Notion API 异步封装类
'''

from typing import Dict, List
from notion_api import NotionAsyncAPI


class NotionWorkspace:
    """Notion 工作空间类"""

    def __init__(self, rate_limit: float = 0.5):
        """_summary_

        Args:
            rate_limit (float, optional): _description_. Defaults to 0.5.
        """
        self.notion_api = NotionAsyncAPI(rate_limit=rate_limit)

    def _extract_rich_text(self, rich_text: List[Dict]) -> str:
        """从富文本内容中提取文本

        Args:
            rich_text: 富文本内容列表

        Returns:
            str: 提取的文本
        """
        text_parts = []
        for text in rich_text:
            content = text.get("text", {}).get("content", "")
            annotations = text.get("annotations", {})
            # 处理文本样式
            if annotations.get("bold"):
                content = f"**{content}**"
            if annotations.get("italic"):
                content = f"*{content}*"
            if annotations.get("strikethrough"):
                content = f"~~{content}~~"
            if annotations.get("code"):
                content = f"`{content}`"

            # 处理链接
            if text.get("href"):
                content = f"[{content}]({text['href']})"

            text_parts.append(content)

        return "".join(text_parts)

    async def get_authors(
        self, fliter: str = None,
        filter_type: str = "equals",
        filter_property: str = "名称"
    ) -> List[Dict]:
        """获取工作空间中的所有数据库

        Returns:
            List[Dict]: 包含数据库ID和标题的列表
        """
        content = await self.notion_api.query_database_with_filter(
            database_id='1b127b61-0892-80a3-81c6-cf051139859c',
            filter_property=filter_property if fliter else None,
            filter_value=fliter,
            filter_type=filter_type if fliter else None,
        )
        content = content if isinstance(content, list) else [content]
        res = list()
        for i in content:
            简述 = i['properties']['简述'].get("rich_text")
            name = i['properties']['名称']['title'][0]['plain_text']
            res += [{
                "id": i['id'],
                "name": name,
                "description": 简述[0]['plain_text'] if 简述 else None
            }]
        return res

    async def update_author_description(
        self, data: Dict
    ) -> bool:
        """更新作者与书籍的关系
        """
        for item in data:
            page_id = item['id']
            properties_to_update = {
                "简述": {"value": item['introduction']},
                "英文名称": {"value": item['english name']},
                "中文名称": {"value": item['chinese name']}
            }
            await self.notion_api.update_page_properties(
                page_id=page_id,
                properties_to_update=properties_to_update
            )

    async def get_fields(
        self, fliter: str = None, filter_type: str = "equals"
    ) -> List[Dict]:
        """获取所有字段"""
        content = await self.notion_api.query_database_with_filter(
            database_id='1b127b61-0892-80ec-a433-c85bf18f6496',
            filter_property="名称" if fliter else None,
            filter_value=fliter,
            filter_type=filter_type if fliter else None,
        )
        content = content if isinstance(content, list) else [content]
        res = list()
        for i in content:
            res += [{
                "id": i['id'],
                "name": i['properties']['Name']['title'][0]['plain_text']
            }]
        return res

    async def update_fields_description(self, data: Dict) -> List[Dict]:
        """更新字段描述"""
        for item in data:
            page_id = item['id']
            properties_to_update = {
                "分类概述": {"value": item['reason']}
            }
            await self.notion_api.update_page_properties(
                page_id=page_id,
                properties_to_update=properties_to_update
            )

    async def get_articals(
        self, fliter: str = '未开始', filter_type: str = "equals"
    ) -> List[Dict]:
        content = await self.notion_api.query_database_with_filter(
            database_id='c3f1101c-fbf7-4702-8dc4-a22578ac6430',
            filter_property="状态" if fliter else None,
            filter_value=fliter,
            filter_type=filter_type if fliter else None,
        )
        content = content if isinstance(content, list) else [content]
        res = list()
        for i in content:
            title = i['properties']['标题']['title'][0]['plain_text']
            if title != '新文章':
                res += [{"id": i['id'], "name": title}]
        return res

    async def get_articals_content(
        self, page_id: str
    ) -> List[Dict]:
        blocks = await self.notion_api.get_page_content(
            page_id=page_id
        )
        markdown_content = []

        for block in blocks:
            block_type = block.get("type")
            if not block_type:
                continue

            content = block.get(block_type, {})
            match block_type:
                case "paragraph":
                    text = self._extract_rich_text(
                        content.get("rich_text", []))
                    if text:
                        markdown_content.append(text + "\n\n")
                case "heading_1":
                    text = self._extract_rich_text(
                        content.get("rich_text", []))
                    if text:
                        markdown_content.append(f"# {text}\n\n")
                case "heading_2":
                    text = self._extract_rich_text(
                        content.get("rich_text", []))
                    if text:
                        markdown_content.append(f"## {text}\n\n")
                case "heading_3":
                    text = self._extract_rich_text(
                        content.get("rich_text", []))
                    if text:
                        markdown_content.append(f"### {text}\n\n")
                case "bulleted_list_item":
                    text = self._extract_rich_text(
                        content.get("rich_text", []))
                    if text:
                        markdown_content.append(f"* {text}\n")
                case "numbered_list_item":
                    text = self._extract_rich_text(
                        content.get("rich_text", []))
                    if text:
                        markdown_content.append(f"1. {text}\n")
                case "to_do":
                    text = self._extract_rich_text(
                        content.get("rich_text", []))
                    checked = content.get("checked", False)
                    if text:
                        markdown_content.append(
                            f"- [{'x' if checked else ' '}] {text}\n"
                        )
                case "code":
                    text = self._extract_rich_text(
                        content.get("rich_text", []))
                    language = content.get("language", "")
                    if text:
                        markdown_content.append(
                            f"```{language}\n{text}\n```\n\n"
                        )
                case "quote":
                    text = self._extract_rich_text(
                        content.get("rich_text", []))
                    if text:
                        markdown_content.append(f"> {text}\n\n")
                case "divider":
                    markdown_content.append("---\n\n")
                case "callout":
                    text = self._extract_rich_text(
                        content.get("rich_text", []))
                    icon = content.get("icon", {}).get("emoji", "💡")
                    if text:
                        markdown_content.append(f"{icon} {text}\n\n")

        markdown_text = "".join(markdown_content)
        if not markdown_text.strip():
            return False, False
        return markdown_text, blocks
