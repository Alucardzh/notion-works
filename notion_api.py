'''
 # @ Author: Alucard
 # @ Create Time: 2025-04-14 14:30:05
 # @ Description: Notion API 异步封装类
'''

import os
from pathlib import Path
import logging
from typing import Optional, Dict, List, Union, Any
import asyncio
import aiofiles
from dotenv import load_dotenv
from notion_client import AsyncClient

# 配置日志
logger = logging.getLogger(__name__)


async def save_data_to_file(data: str, filename: str) -> None:
    """将数据保存为文件

    Args:
        data: 要保存的数据对象
        filename: 保存的文件路径

    功能：
        1. 自动创建目标文件夹
    """
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
        await f.write(data)


class NotionAsyncAPI:
    """Notion API 异步交互类"""

    def __init__(self, rate_limit=0.5):
        """初始化 Notion 异步客户端

        Args:
            rate_limit: API调用间隔时间（秒）
        """
        load_dotenv()
        self.notion = AsyncClient(auth=os.getenv("NOTION_WORKSPACE_TOKEN"))
        self.rate_limit = rate_limit
        self.last_api_call = 0
        self._database_cache = {}
        self._lock = asyncio.Lock()
        self._databases = []

    async def _rate_limit_wait(self):
        """等待以确保API调用频率不超过限制"""
        async with self._lock:
            current_time = asyncio.get_event_loop().time()
            time_since_last_call = current_time - self.last_api_call
            if time_since_last_call < self.rate_limit:
                await asyncio.sleep(self.rate_limit - time_since_last_call)
            self.last_api_call = asyncio.get_event_loop().time()

    async def get_formatted_databases(self) -> List[Dict[str, str]]:
        """列出工作空间中的所有数据库,并格式化的数据库列表

        Returns:
            List[Dict[str, str]]: 包含数据库ID和标题的列表
            示例: [{'id': 'database_id', 'title': '数据库名称'}]
        """
        try:
            await self._rate_limit_wait()
            response = await self.notion.search(
                filter={"property": "object", "value": "database"}
            )
            databases = response.get("results", [])
            self._databases = [{
                'id': db['id'],
                'title': db.get('title',
                                [{'plain_text': '未命名'}])[0]['plain_text']
            } for db in databases if db.get('title', [])]
            return self._databases
        except Exception as e:
            logger.error(f"获取格式化数据库列表时出错: {e}")
            return []

    async def get_database_schema(self, database_id: str) -> Dict:
        """获取数据库的属性模式

        Args:
            database_id: 数据库ID

        Returns:
            数据库属性模式字典
        """
        try:
            await self._rate_limit_wait()
            response = await self.notion.databases.retrieve(
                database_id=database_id
            )
            return response.get("properties", {})
        except Exception as e:
            print(f"获取数据库模式时出错: {e}")
            return {}

    async def get_database_data(
        self, database_id: str, use_cache: bool = True,
        filter_property: List[str] = None,
        page_size: int = 100
    ) -> Dict:
        """获取数据库的内容

        Args:
            database_id: 数据库ID
            use_cache: 是否使用缓存
            filter_property: 需要获取的属性列表
            page_size: 每页数据量，最大100

        Returns:
            数据库内容字典列表
        """
        filter_property = filter_property or ["properties", "id", "url"]
        try:
            await self._rate_limit_wait()
            if use_cache and database_id in self._database_cache:
                return self._database_cache[database_id]

            all_results = []
            has_more = True
            next_cursor = None

            while has_more:
                # 构建查询参数
                query_params = {
                    "database_id": database_id,
                    "page_size": min(page_size, 100)  # 确保不超过API限制
                }
                if next_cursor:
                    query_params["start_cursor"] = next_cursor

                # 执行查询
                responses = await self.notion.databases.query(**query_params)

                # 处理当前页的结果
                results = [{
                    item: response.get(item, {}) for item in filter_property
                } for response in responses.get("results", [])]
                all_results.extend(results)

                # 检查是否还有更多数据
                has_more = responses.get("has_more", False)
                next_cursor = responses.get("next_cursor")

                # 如果还有更多数据，等待一下以遵守API限制
                if has_more:
                    await self._rate_limit_wait()

            if use_cache:
                self._database_cache[database_id] = all_results
            return all_results

        except Exception as e:
            logger.error(f"获取数据库数据时出错: {e}")
            return []

    async def add_database_property(
        self, database_id: str, property_name: str,
        property_type: str,
        default_value: Optional[Union[str, int, bool]] = None
    ) -> bool:
        """向数据库添加新属性

        Args:
            database_id: 数据库ID
            property_name: 属性名称
            property_type: 属性类型 (rich_text, number, select, multi_select等)
            default_value: 默认值

        Returns:
            bool: 是否添加成功
        """
        try:
            await self._rate_limit_wait()
            schema = await self.get_database_schema(database_id)

            if property_name in schema:
                logger.warning(f"属性 '{property_name}' 已存在")
                return False

            # 根据不同属性类型构建属性配置
            property_config = {
                property_name: {
                    "type": property_type,
                    property_type: {}
                }
            }

            # 处理不同类型的默认值
            if default_value is not None:
                match property_type:
                    case "select":
                        property_config[property_name][property_type] = {
                            "options": [{"name": str(default_value)}]
                        }
                    case "multi_select":
                        property_config[property_name][property_type] = {
                            "options": [{"name": str(default_value)}]
                        }
                    case "status":
                        property_config[property_name][property_type] = {
                            "options": [{"name": str(default_value)}]
                        }
                    case _:
                        property_config[property_name][property_type] = {}
            await self.notion.databases.update(
                database_id=database_id,
                properties=property_config
            )
            logger.info(f"成功添加属性: {property_name} ({property_type})")
            return True
        except Exception as e:
            logger.error(f"添加数据库属性时出错: {e}")
            return False

    async def remove_database_property(
        self, database_id: str, property_name: str
    ) -> bool:
        """从数据库中删除属性

        Args:
            database_id: 数据库ID
            property_name: 要删除的属性名称

        Returns:
            bool: 是否删除成功
        """
        try:
            await self._rate_limit_wait()
            schema = await self.get_database_schema(database_id)

            if property_name not in schema:
                print(f"属性 '{property_name}' 不存在")
                return False

            await self.notion.databases.update(
                database_id=database_id,
                properties={property_name: None}
            )
            return True
        except Exception as e:
            print(f"删除数据库属性时出错: {e}")
            return False

    async def query_database_with_filter(
        self,
        database_id: str,
        filter_property: str = None,
        filter_value: Union[str, int, bool, List] = None,
        filter_type: str = "equals",
        page_size: int = 100
    ) -> List[Dict]:
        """根据属性值筛选数据库内容

        Args:
            database_id: 数据库ID
            filter_property: 筛选属性名称
            filter_value: 筛选值
            filter_type: 筛选类型，支持：
                - equals: 等于
                - does_not_equal: 不等于
                - contains: 包含
                - does_not_contain: 不包含
                - starts_with: 开头是
                - ends_with: 结尾是
                - greater_than: 大于
                - less_than: 小于
                - greater_than_or_equal_to: 大于等于
                - less_than_or_equal_to: 小于等于
                - is_empty: 为空
                - is_not_empty: 不为空
            page_size: 每页数据量，最大100

        Returns:
            符合条件的页面列表
        """
        try:
            await self._rate_limit_wait()
            # 如果没有指定过滤条件，返回所有数据
            if filter_property is None:
                logger.info("没有指定过滤条件，返回所有数据")
                return await self.get_database_data(database_id=database_id)

            # 获取数据库模式以确定属性类型
            schema = await self.get_database_schema(database_id)
            if filter_property not in schema:
                logger.error(f"属性 '{filter_property}' 不存在")
                return []

            property_type = schema[filter_property]["type"]
            all_results = []
            has_more = True
            next_cursor = None

            while has_more:
                # 构建查询参数
                query_params = {
                    "database_id": database_id,
                    "page_size": min(page_size, 100)
                }
                if next_cursor:
                    query_params["start_cursor"] = next_cursor

                # 构建过滤条件
                filter_condition = {
                    "property": filter_property
                }

                # 根据属性类型和过滤类型构建具体的过滤条件
                match property_type:
                    case "number":
                        filter_condition["number"] = {
                            filter_type: float(filter_value)
                        }
                    case "checkbox":
                        filter_condition["checkbox"] = {
                            filter_type: bool(filter_value)
                        }
                    case "select":
                        filter_condition["select"] = {
                            filter_type: {"equals": filter_value}
                        }
                    case "multi_select":
                        if isinstance(filter_value, list):
                            filter_condition["multi_select"] = {
                                "contains": filter_value
                            }
                        else:
                            filter_condition["multi_select"] = {
                                "contains": str(filter_value)
                            }
                    case "relation":
                        if isinstance(filter_value, list):
                            filter_condition["relation"] = {
                                "contains": filter_value
                            }
                        else:
                            filter_condition["relation"] = {
                                "contains": str(filter_value)
                            }
                    case "date":
                        filter_condition["date"] = {
                            filter_type: str(filter_value)
                        }
                    case "people":
                        filter_condition["people"] = {
                            filter_type: {"id": str(filter_value)}
                        }
                    case "files":
                        filter_condition["files"] = {
                            "is_empty": filter_value
                        }
                    case _:  # 默认作为文本处理
                        filter_condition[property_type] = {
                            filter_type: str(filter_value)
                        }

                query_params["filter"] = filter_condition

                # 执行查询
                response = await self.notion.databases.query(**query_params)
                results = response.get("results", [])
                all_results.extend(results)

                # 检查是否还有更多数据
                has_more = response.get("has_more", False)
                next_cursor = response.get("next_cursor")

                # 如果还有更多数据，等待一下以遵守API限制
                if has_more:
                    await self._rate_limit_wait()

            return all_results

        except Exception as e:
            logger.error(f"查询数据库时出错: {e}")
            return []

    async def get_page_content(self, page_id: str) -> List[Dict]:
        """获取指定页面的内容"""
        try:
            await self._rate_limit_wait()
            response = await self.notion.blocks.children.list(block_id=page_id)
            return response.get("results", [])
        except Exception as e:
            print(f"获取页面内容时出错: {e}")
            return []

    def clear_database_cache(self, database_id: Optional[str] = None):
        """清除数据库缓存

        Args:
            database_id: 指定要清除的数据库ID，如果为None则清除所有缓存
        """
        if database_id:
            self._database_cache.pop(database_id, None)
        else:
            self._database_cache.clear()

    async def export_page_to_markdown(
        self, page_id: str, output_path: str = None
    ) -> Optional[str]:
        """将页面内容导出为 Markdown 格式

        Args:
            page_id: 页面ID
            output_path: 输出文件路径，如果为None则只返回内容不保存文件

        Returns:
            Optional[str]: Markdown格式的内容，如果失败则返回None
        """
        try:
            await self._rate_limit_wait()
            blocks = await self.get_page_content(page_id)
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
            if output_path:
                await save_data_to_file(markdown_text, output_path)
            return markdown_text, blocks

        except Exception as e:
            logger.error(f"导出Markdown时出错: {e}")
            return None

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

    async def update_page_properties(
        self,
        page_id: str,
        properties_to_update: Dict[str, Dict[str, Any]]
    ) -> bool:
        """更新页面的多个属性值

        Args:
            page_id: 页面ID
            properties_to_update: 要更新的属性字典，格式为：
                {
                    "属性名": {
                        "value": 值,
                        "type": 属性类型（可选，如果不指定则自动检测）
                    }
                }

        Returns:
            bool: 更新是否成功

        示例:
        await update_page_properties(
            page_id="xxx",
            properties_to_update={
                "标题": {"value": "新标题", "type": "title"},
                "状态": {"value": "完成", "type": "status"},
                "数量": {"value": 42, "type": "number"},
                "标签": {"value": ["标签1", "标签2"], "type": "multi_select"},
                "关联": {"value": ["page-id-1", "page-id-2"], "type": "relation"}
            }
        )
        """
        try:
            await self._rate_limit_wait()

            # 如果没有提供属性类型，获取页面属性以确定类型
            page = await self.notion.pages.retrieve(page_id=page_id)
            current_properties = page.get("properties", {})

            # 构建更新数据
            properties = {}

            for prop_name, prop_data in properties_to_update.items():
                prop_value = prop_data["value"]
                # 如果未指定类型，从现有属性中获取
                prop_type = prop_data.get("type") or current_properties.get(
                    prop_name, {}).get("type")

                if not prop_type:
                    logger.error(f"属性 '{prop_name}' 类型未知")
                    continue

                # 根据不同属性类型构建更新数据
                match prop_type:
                    case "rich_text":
                        properties[prop_name] = {
                            "rich_text": [{
                                "text": {"content": str(prop_value)}
                            }]
                        }
                    case "text":
                        properties[prop_name] = {
                            "text": {"content": str(prop_value)}
                        }
                    case "number":
                        properties[prop_name] = {
                            "number": float(prop_value)
                        }
                    case "select":
                        properties[prop_name] = {
                            "select": {"name": str(prop_value)}
                        }
                    case "multi_select":
                        # 支持列表或字符串输入
                        if isinstance(prop_value, str):
                            values = [prop_value]
                        else:
                            values = prop_value
                        properties[prop_name] = {
                            "multi_select": [
                                {"name": str(v)} for v in values
                            ]
                        }
                    case "status":
                        properties[prop_name] = {
                            "status": {"name": str(prop_value)}
                        }
                    case "checkbox":
                        properties[prop_name] = {
                            "checkbox": bool(prop_value)
                        }
                    case "date":
                        properties[prop_name] = {
                            "date": {"start": str(prop_value)}
                        }
                    case "url":
                        properties[prop_name] = {
                            "url": str(prop_value)
                        }
                    case "email":
                        properties[prop_name] = {
                            "email": str(prop_value)
                        }
                    case "phone_number":
                        properties[prop_name] = {
                            "phone_number": str(prop_value)
                        }
                    case "relation":
                        # 支持单个ID或ID列表
                        if isinstance(prop_value, str):
                            relation_ids = [prop_value]
                        else:
                            relation_ids = prop_value
                        properties[prop_name] = {
                            "relation": [
                                {"id": page_id} for page_id in relation_ids
                            ]
                        }
                    case "title":
                        properties[prop_name] = {
                            "title": [{
                                "text": {"content": str(prop_value)}
                            }]
                        }
                    case _:
                        logger.warning(
                            f"属性类型 '{prop_type}' 可能不支持: {prop_name}")
                        continue

            if not properties:
                logger.error("没有有效的属性需要更新")
                return False

            # 更新页面属性
            await self.notion.pages.update(
                page_id=page_id,
                properties=properties
            )
            logger.info(f"成功更新属性: {list(properties.keys())}")
            return True

        except Exception as e:
            logger.error(f"更新页面属性时出错: {e}")
            return False

    # 为了保持向后兼容，保留原来的方法名但调用新方法
    async def update_page_property(
        self,
        page_id: str,
        property_name: str,
        new_value: Any,
        property_type: Optional[str] = None
    ) -> bool:
        """更新单个页面属性（保持向后兼容）"""
        return await self.update_page_properties(
            page_id=page_id,
            properties_to_update={
                property_name: {
                    "value": new_value,
                    "type": property_type
                }
            }
        )
