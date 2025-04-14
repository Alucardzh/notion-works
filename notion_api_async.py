'''
 # @ Author: Alucard
 # @ Create Time: 2025-04-14 14:30:05
 # @ Description: Notion API 异步封装类
'''

import os
import asyncio
from typing import Optional, Dict, List, Union
from dotenv import load_dotenv
from notion_client import AsyncClient


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

    async def _rate_limit_wait(self):
        """等待以确保API调用频率不超过限制"""
        async with self._lock:
            current_time = asyncio.get_event_loop().time()
            time_since_last_call = current_time - self.last_api_call
            if time_since_last_call < self.rate_limit:
                await asyncio.sleep(self.rate_limit - time_since_last_call)
            self.last_api_call = asyncio.get_event_loop().time()

    async def list_all_databases(self) -> List[Dict]:
        """列出工作空间中的所有数据库"""
        try:
            await self._rate_limit_wait()
            response = await self.notion.search(
                filter={"property": "object", "value": "database"}
            )
            return response.get("results", [])
        except Exception as e:
            print(f"获取数据库列表时出错: {e}")
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

    async def add_database_property(
        self, database_id: str, property_name: str,
        property_type: str, default_value: Optional[Union[str, int, bool]] = None
    ) -> bool:
        """向数据库添加新属性

        Args:
            database_id: 数据库ID
            property_name: 属性名称
            property_type: 属性类型 (text, number, checkbox, select, date 等)
            default_value: 默认值

        Returns:
            bool: 是否添加成功
        """
        try:
            await self._rate_limit_wait()
            schema = await self.get_database_schema(database_id)

            if property_name in schema:
                print(f"属性 '{property_name}' 已存在")
                return False

            property_config = {property_name: {"type": property_type}}

            if default_value is not None:
                if property_type == "rich_text":
                    property_config[property_name]["rich_text"] = [
                        {"text": {"content": str(default_value)}}
                    ]
                elif property_type == "number":
                    property_config[property_name]["number"] = float(
                        default_value
                    )
                elif property_type == "checkbox":
                    property_config[property_name]["checkbox"] = bool(
                        default_value
                    )

            await self.notion.databases.update(
                database_id=database_id,
                properties=property_config
            )
            return True
        except Exception as e:
            print(f"添加数据库属性时出错: {e}")
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
        self, database_id: str, filter_property: str,
        filter_value: Union[str, int, bool], filter_type: str = "equals"
    ) -> List[Dict]:
        """根据属性值筛选数据库内容

        Args:
            database_id: 数据库ID
            filter_property: 筛选属性名称
            filter_value: 筛选值
            filter_type: 筛选类型 (equals, contains, greater_than 等)

        Returns:
            符合条件的页面列表
        """
        try:
            await self._rate_limit_wait()
            filter_condition = {
                "property": filter_property,
                filter_type: filter_value
            }

            response = await self.notion.databases.query(
                database_id=database_id,
                filter=filter_condition
            )
            return response.get("results", [])
        except Exception as e:
            print(f"查询数据库时出错: {e}")
            return []

    async def get_database_content(
        self, database_id: str, use_cache: bool = True
    ) -> List[Dict]:
        """获取指定数据库的内容，支持缓存

        Args:
            database_id: 数据库ID
            use_cache: 是否使用缓存

        Returns:
            数据库内容列表
        """
        if use_cache and database_id in self._database_cache:
            return self._database_cache[database_id]

        try:
            await self._rate_limit_wait()
            response = await self.notion.databases.query(
                database_id=database_id
            )
            results = response.get("results", [])

            if use_cache:
                self._database_cache[database_id] = results

            return results
        except Exception as e:
            print(f"获取数据库内容时出错: {e}")
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

    async def get_database_by_name(self, database_name: str) -> Optional[str]:
        """根据数据库名称获取数据库ID"""
        databases = await self.list_all_databases()
        for db in databases:
            title = db.get('title', [{'plain_text': '未命名'}])[0]['plain_text']
            if title == database_name:
                return db['id']
        return None

    async def get_page_content(self, page_id: str) -> List[Dict]:
        """获取指定页面的内容"""
        try:
            await self._rate_limit_wait()
            response = await self.notion.blocks.children.list(block_id=page_id)
            return response.get("results", [])
        except Exception as e:
            print(f"获取页面内容时出错: {e}")
            return []

    async def update_page_text(self, page_id: str, text_content: str) -> bool:
        """更新页面的文本内容

        Args:
            page_id: 页面ID
            text_content: 要更新的文本内容

        Returns:
            bool: 是否更新成功
        """
        try:
            await self._rate_limit_wait()
            await self.notion.pages.update(
                page_id=page_id,
                properties={
                    "文本": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": text_content
                                }
                            }
                        ]
                    }
                }
            )
            return True
        except Exception as e:
            print(f"更新页面内容时出错: {e}")
            return False

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        pass
