'''
 # @ Author: Alucard
 # @ Create Time: 2025-04-14 11:49:05
 # @ Description: Notion API 异步命令行工具
 # @ 主要功能：
 #   1. 导出数据库内容到JSON文件
 #   2. 根据条件筛选数据库内容
 #   3. 将页面导出为Markdown格式
 #   4. 自动处理文章分类和作者信息
'''
import os
from pathlib import Path
from typing import List, Dict, Union
import json
from notion_api import save_data_to_file
from notion_workspace import NotionWorkspace
from llm import OllamaClient as LlmClient


async def save_temp_data_to_json(data, filename) -> None:
    """将数据保存为JSON文件

    Args:
        data: 要保存的数据对象
        filename: 保存的文件路径

    功能：
        1. 自动创建目标文件夹
        2. 以UTF-8编码保存JSON文件
        3. 保持中文显示
    """
    data = json.dumps(data, ensure_ascii=False, indent=4)
    await save_data_to_file(data, filename)


class WorkFlow:
    """工作流程管理类

    负责协调 Notion 工作区操作和 DeepSeek AI 的文章分析功能。
    主要处理文章的自动分类、作者信息提取和数据库更新等任务。
    """

    def __init__(self, notion_workspace: NotionWorkspace,
                 update_field_info: bool = False,
                 save_path: Path = Path(
                     f'tmp/{os.getenv("NOTION_WORKSPACE_TOKEN")}')
                 ) -> None:
        """初始化工作流程管理器

        Args:
            notion_workspace: Notion工作区实例
            update_field_info: 是否更新分类字段信息
            save_path: 临时文件保存路径，默认使用工作区token作为子目录
        """
        self.notion_workspace = notion_workspace
        self.update_field_info = update_field_info
        self.save_path = save_path
        self.llm_model = LlmClient()

    async def renew_fields(self) -> Dict:
        """更新或获取分类字段信息

        如果 update_field_info 为 True，会从 Notion 获取最新的分类信息并保存；
        否则直接从本地文件读取已保存的分类信息。

        Returns:
            Dict: 分类字段信息字典
        """
        if self.update_field_info:
            fields = await self.notion_workspace.get_fields()
            await save_temp_data_to_json(
                fields, self.save_path / 'field.info.json')
        with open(self.save_path / 'field.info.json', 'r',
                  encoding='utf-8') as data:
            fields = json.loads(data.read())
        return fields

    @staticmethod
    async def workflow_get_field_id_list(
        field_id: Dict, category: Union[str, List[str]]
    ) -> List[Dict]:
        """生成字段ID列表

        Args:
            field_id: 字段ID列表
            category: 分类列表

        Returns:
            List[Dict]: 包含字段ID的字典列表
        """
        if isinstance(category, str):
            category = category.split(',')
        return [field_id.get(item.strip()) for item in category]

    async def workflow_main(
        self,
        article: Dict = None,
        fields: List = None
    ) -> None:
        """主要工作流程处理

        处理单篇文章的分类、作者信息提取和数据库更新。

        Args:
            article: 文章信息字典
            fields: 分类字段列表

        流程：
            1. 获取文章内容
            2. 生成分类目录
            3. 调用 DeepSeek 分析文章信息
            4. 处理作者信息
            5. 更新数据库记录
        """
        # 获取文章内容
        content = await self.notion_workspace.get_articles_content(
            page_id=article.get('id'))

        # 生成分类目录
        catelog = [
            f"{field['category']}:{field['reason']}" for field in fields]
        field_id = {
            f"{field['category']}": f"{field['id']}" for field in fields}

        # 构建分类分析文本
        classify_catelog = "\n".join(
            ["==============",
             "【分类类型】:【理由】",
             "==============",
             '\n'.join(catelog),
             f"文章标题：{article.get('name')}",
             f"文章内容：{content}"
             ])

        # 调用 DeepSeek API 分析文章信息
        article_info = await self.llm_model.get_article_info_from_file(
            article_text=classify_catelog)

        # 提取作者信息
        author = article_info.get('author')
        author_english_name = article_info.get('author_english_name')
        author_chinese_name = article_info.get('author_chinese_name')

        # 设置文章状态
        status = "进行中"
        if (author == 'unknown' and author_english_name == 'unknown'
                and author_chinese_name == "none"):
            status = "信息缺失"
            author_id = None
        else:
            # 获取或创建作者ID
            author_id = await self.workflow_get_author_id(
                article_info=article_info)
        # 暂存LLM返回的结果
        await save_temp_data_to_json(
            {**article_info, **article},
            self.save_path / 'output' / f'{article.get("id")}.json')
        # 更新文章信息
        update_data = {
            "page_id": article.get('id'),
            "status": status,
            "category": await self.workflow_get_field_id_list(
                field_id=field_id, category=article_info.get('category')
            )
        }
        if author_id:
            return await self.notion_workspace.update_article_detail(
                author_id=author_id,
                **update_data)
        else:
            return await self.notion_workspace.update_article_detail(
                **update_data)

    async def worklow_get_articles(
        self, database_id: str = 'c3f1101c-fbf7-4702-8dc4-a22578ac6430',
        fliter: str = '未开始', filter_type: str = "equals",
        filter_property: str = "状态"
    ) -> List[Dict]:
        """获取符合条件的文章列表

        Args:
            database_id: 数据库ID
            fliter: 筛选条件值，默认为"未开始"
            filter_type: 筛选类型，默认为精确匹配
            filter_property: 筛选属性

        Returns:
            List[Dict]: 文章信息列表
        """
        return await self.notion_workspace.get_articles(
            database_id=database_id, fliter=fliter, filter_type=filter_type,
            filter_property=filter_property)

    async def workflow_get_author_id(
        self,
        article_info: Dict = None,
    ) -> str:
        """获取或创建作者ID

        通过以下步骤查找或创建作者记录：
        1. 通过英文名查找
        2. 如果未找到，通过中文名查找
        3. 如果仍未找到，创建新的作者记录

        Args:
            article_info: 文章信息字典，包含作者相关信息

        Returns:
            str: 作者ID
        """
        author_id = None
        chinese_name = article_info.get("author_chinese_name")

        # 通过英文名称查询
        author_db = await self.notion_workspace.get_authors(
            filter_property="英文名称", filter_type="contains",
            fliter=article_info.get("author_english_name"))

        if author_db:
            author_id = author_db[0].get('id')
        else:
            # 通过中文名称查询
            author_db = await self.notion_workspace.get_authors(
                filter_property="中文名称", filter_type="equals",
                fliter=chinese_name)
            if author_db:
                author_id = author_db[0].get('id')

        # 如果作者不存在，创建新记录
        if author_id is None:
            # 获取作者详细信息
            res = self.llm_model.get_author_info(
                author_info={"name": article_info.get("author")})

            # 创建新作者记录
            author_id = await self.notion_workspace.new_authors(
                properties={
                    "中文名称": chinese_name if chinese_name != "none" else "",
                    "英文名称": article_info.get("author_english_name", ""),
                    "名称": article_info.get("author"),
                    "简述": res.get("introduction", "")
                }
            )
        return author_id
