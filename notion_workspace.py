'''
 # @ Author: Alucard
 # @ Create Time: 2025-04-14 14:30:05
 # @ Description: Notion API 异步封装类
 # @ 主要功能：
 #   1. 管理作者信息
 #   2. 处理文章分类
 #   3. 更新文章内容
 #   4. 格式化数据转换
'''
from typing import Dict, List, Optional
from notion_api import NotionAsyncAPI
from tools.logging_config import setup_logger

# 配置日志
logger = setup_logger(__name__)


class NotionWorkspace:
    """Notion 工作空间管理类

    负责管理 Notion 工作空间中的数据库操作，包括：
    1. 作者信息的增删改查
    2. 文章分类的管理和更新
    3. 文章内容的获取和更新
    4. 富文本内容的格式化处理
    """

    def __init__(self, rate_limit: float = 0.5):
        """初始化 Notion 工作空间管理器

        Args:
            rate_limit: API 调用频率限制（秒），默认 0.5 秒/次
        """
        self.notion_api = NotionAsyncAPI(rate_limit=rate_limit)

    def _extract_rich_text(self, rich_text: List[Dict]) -> str:
        """从富文本内容中提取文本并保留格式

        处理 Notion 富文本的各种格式，包括：
        - 粗体、斜体、删除线
        - 代码块
        - 超链接

        Args:
            rich_text: Notion 富文本内容列表

        Returns:
            str: 转换后的 Markdown 格式文本
        """
        text_parts = []
        for text in rich_text:
            content = text.get("text", {}).get("content", "")
            annotations = text.get("annotations", {})

            # 处理文本样式
            if annotations.get("bold"):
                content = f"**{content}**"  # 粗体
            if annotations.get("italic"):
                content = f"*{content}*"    # 斜体
            if annotations.get("strikethrough"):
                content = f"~~{content}~~"  # 删除线
            if annotations.get("code"):
                content = f"`{content}`"    # 行内代码

            # 处理超链接
            if text.get("href"):
                content = f"[{content}]({text['href']})"

            text_parts.append(content)

        return "".join(text_parts)

    async def get_authors(
        self, fliter: str = None,
        filter_type: str = "equals",
        filter_property: str = "名称",
        database_id: str = '1b127b61-0892-80a3-81c6-cf051139859c'
    ) -> List[Dict]:
        """获取作者信息

        从作者数据库中检索作者信息，支持按不同属性筛选。

        Args:
            fliter: 筛选值，为空时返回所有作者
            filter_type: 筛选类型，默认为精确匹配
            filter_property: 筛选属性，默认为"名称"
            database_id: 作者数据库ID

        Returns:
            List[Dict]: 作者信息列表，每个作者包含：
                - id: 作者ID
                - name: 作者名称
                - description: 作者简述
        """
        content = await self.notion_api.query_database_with_filter(
            database_id=database_id,
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

    async def new_authors(
        self, properties: Dict,
        database_id: str = '1b127b61-0892-80a3-81c6-cf051139859c'
    ) -> Optional[str]:
        """创建新作者记录

        Args:
            properties: 作者属性字典，包含：
                - 名称: 作者名称（必填）
                - 中文名称: 中文名
                - 英文名称: 英文名
                - 简述: 作者简介
            database_id: 作者数据库ID

        Returns:
            Optional[str]: 新创建的作者ID，失败返回 None
        """
        new_author = await self.notion_api.create_database_item(
            database_id=database_id,
            properties=properties
        )
        return new_author

    async def update_author_description(
        self, data: Dict
    ) -> bool:
        """更新作者信息

        更新作者的简述、英文名和中文名等信息。

        Args:
            data: 作者信息列表，每项包含：
                - id: 作者ID
                - introduction: 作者简介
                - english name: 英文名
                - chinese name: 中文名

        Returns:
            bool: 更新是否成功
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
        self, database_id: str = '1b127b61-0892-80ec-a433-c85bf18f6496',
        fliter: str = None, filter_type: str = "equals"
    ) -> List[Dict]:
        """获取文章分类字段

        检索文章分类数据库中的分类信息。

        Args:
            database_id: 分类数据库ID
            fliter: 分类名称筛选
            filter_type: 筛选类型

        Returns:
            List[Dict]: 分类信息列表，每项包含：
                - id: 分类ID
                - name: 分类名称
                - category: 分类类型
                - reason: 分类说明
        """
        content = await self.notion_api.query_database_with_filter(
            database_id=database_id,
            filter_property="名称" if fliter else None,
            filter_value=fliter,
            filter_type=filter_type if fliter else None,
        )
        content = content if isinstance(content, list) else [content]

        res = list()
        for i in content:
            res += [{
                "id": i['id'],
                "name": i['properties']['领域名称']['title'][0]['plain_text'],
                "category": i['properties']['领域名称']['title'][0]['plain_text'],
                "reason": i['properties']['分类概述']['rich_text'][0]['plain_text']
            }]
        return res

    async def update_fields_description(self, data: Dict) -> List[Dict]:
        """更新分类字段描述

        Args:
            data: 分类信息列表，每项包含：
                - id: 分类ID
                - reason: 分类说明
        """
        for item in data:
            page_id = item['id']
            properties_to_update = {
                "分类概述": {"value": item['reason']}
            }
            await self.notion_api.update_page_properties(
                page_id=page_id,
                properties_to_update=properties_to_update
            )

    async def get_articles(
        self, database_id: str = 'c3f1101c-fbf7-4702-8dc4-a22578ac6430',
        fliter: str = '未开始', filter_type: str = "equals",
        filter_property: str = "状态"
    ) -> List[Dict]:
        """获取文章列表

        检索文章数据库中的文章信息，支持按状态筛选。

        Args:
            database_id: 文章数据库ID
            fliter: 状态筛选值，默认为"未开始"
            filter_type: 筛选类型，默认为精确匹配

        Returns:
            List[Dict]: 文章信息列表，每项包含：
                - id: 文章ID
                - name: 文章标题
        """
        content = await self.notion_api.query_database_with_filter(
            database_id=database_id,
            filter_property=filter_property if fliter else None,
            filter_value=fliter,
            filter_type=filter_type if fliter else None,
        )
        content = content if isinstance(content, list) else [content]
        res = list()
        for i in content:
            try:
                title = i['properties']['标题']['title'][0]['plain_text']
                author = [relation['id']
                          for relation in i['properties']['作者']['relation']]
                if title != '新文章':  # 排除模板页面
                    res += [{"id": i['id'], "name": title, "author": author}]
            except (KeyError, ValueError, IndexError):
                # 跳过无效或不完整的条目
                pass
        return res

    async def get_articles_content(
        self, page_id: str
    ) -> List[Dict]:
        """获取文章内容并转换为Markdown格式

        将 Notion 页面中的各种块转换为对应的 Markdown 格式。

        支持的块类型：
        - 段落
        - 标题（H1-H3）
        - 列表（有序、无序）
        - 待办事项
        - 代码块
        - 引用
        - 分割线
        - 标注

        Args:
            page_id: 文章页面ID

        Returns:
            Tuple[str, List]: (Markdown文本, 原始块数据)
            如果页面为空，返回 (False, False)
        """
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

    async def update_article_detail(
        self, page_id: str,
        properties_to_update: Dict
    ) -> str:
        """更新文章详细信息

        更新文章的作者、状态和分类信息。

        Args:
            page_id: 文章页面ID
            author_id: 作者ID
            status: 文章状态
            category: 文章分类列表

        Returns:
            str: 更新结果信息
        """
        await self.notion_api.update_page_properties(
            page_id=page_id,
            properties_to_update=properties_to_update)
        return f'{page_id}: ok'
