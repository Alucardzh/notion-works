'''
 # @ Author: Alucard
 # @ Create Time: 2025-04-14 11:49:05
 # @ Description: Notion API 异步命令行工具
 # @ 主要功能：
 #   1. 导出数据库内容到JSON文件
 #   2. 根据条件筛选数据库内容
 #   3. 将页面导出为Markdown格式
'''
import os
from pathlib import Path
from typing import List, Dict
from time import time, sleep
import json
import asyncio
from notion_api import save_data_to_file, NotionWorkspace, NotionAsyncAPI
from llm import DeepSeekClient


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


async def workflow_get_author_id(
    notion_workspace: NotionWorkspace,
    author_english_name: str = None,
    author_chinese_name: str = None
) -> None:
    author_db = await notion_workspace.get_authors(
        filter_property="英文名称", filter_type="contains",
        fliter=author_english_name)
    author_id = None
    if author_db:
        author_id = author_db[0].get('id')
    else:
        author_db = await notion_workspace.get_authors(
            filter_property="中文名称", filter_type="equals",
            fliter=author_chinese_name)
        if author_db:
            author_id = author_db[0].get('id')
    return author_id


async def workflow(
    notion_workspace: NotionWorkspace,
    artical: Dict = None,
    fields: List = None
) -> None:
    deepseek = DeepSeekClient()
    # 读取文章未开始内容
    content = await notion_workspace.get_articals_content(page_id=artical.get('id'))
    catelog = [f"{field['category']}:{field['reason']}" for field in fields]
    classify_catelog = "\n".join(
        ["==============",
         "【分类类型】:【理由】",
         "==============",
         '\n'.join(catelog),
         f"文章标题：{artical.get('name')}",
         f"文章内容：{content}"
         ])
    # 调用DeepSeek API获取文章信息
    article_info = deepseek.get_article_info_from_file(
        article_text=classify_catelog)
    author = article_info.get('author')
    author_english_name = article_info.get('author_english_name')
    author_chinese_name = article_info.get('author_chinese_name')
    status = "进行中"
    # 如果作者信息缺失，则设置为信息缺失
    if author == 'unknown' and author_english_name == 'unknown' and author_chinese_name == "none":
        status = "信息缺失"
    # 获取数据库中的作者信息
    author_id = await workflow_get_author_id(
        notion_workspace=notion_workspace,
        author_english_name=author_english_name,
        author_chinese_name=author_chinese_name
    )


async def main():
    """主函数

    功能流程：
        1. 初始化Notion API客户端（限制请求频率为0.5秒/次）
        2. 设置临时文件存储路径
        3. 根据状态筛选数据库内容
        4. 将筛选结果保存为JSON
        5. 遍历结果并导出为Markdown
    """
    notion_api = NotionAsyncAPI(rate_limit=0.5)
    notion_workspace = NotionWorkspace(rate_limit=0.5)
    tmp_path = Path(f'tmp/{os.getenv("NOTION_WORKSPACE_TOKEN")}')
    # articals = await notion_workspace.get_articals(fliter='未开始')
    # test
    articals = [{'id': '1b127b61-0892-808b-a392-e3572a1f7564',
                 'name': '这个晨间习惯能帮助你每周节省20小时'}]
    with open(tmp_path / 'field.info.json', 'r', encoding='utf-8') as data:
        fields = json.loads(data.read())
        for artical in articals:
            await workflow(
                notion_workspace=notion_workspace,
                artical=artical, fields=fields)

    # 获取数据库列表示例（已注释）
    # databases = await notion_api.get_formatted_databases()
    # await save_temp_data_to_json(databases, tmp_path / 'databases.json')

    # 使用过滤器查询数据库
    # content = await notion_api.query_database_with_filter(
    #     database_id='1b127b61-0892-80ec-a433-c85bf18f6496',
    #     # filter_property="名称",
    #     # filter_value="贝索斯",
    #     # filter_type="equals"
    # )
    # 保存查询结果
    # await save_temp_data_to_json(content, tmp_path / 'field.json')

    # field = await notion_workspace.get_fields()
    # await save_temp_data_to_json(field, tmp_path / 'fields.json')

    # 遍历结果并导出为Markdown
    # for i in content:
    #     page_id = i.get("id")
    #     print(page_id)
    #     # 导出页面内容为Markdown格式
    #     page_content, page = await notion_api.export_page_to_markdown(
    #         page_id=page_id,
    #         output_path=tmp_path / f'output/{page_id}.md'
    #     )
    #     if page:
    #         # 同时保存页面的原始数据
    #         await save_temp_data_to_json(
    #             page, tmp_path / f'output/{page_id}.json')
    #         print(page_content)
    # await notion_api.update_page_property(
    #     page_id='1b227b61-0892-8023-a9c7-d296f6f03294',
    #     property_name='中文名称',
    #     new_value='保罗·格雷厄姆',
    #     property_type='rich_text'
    # )

    # deepseek = DeepSeekClient()
    # with open(tmp_path / 'fields.json', 'r', encoding='utf-8') as data:
    #     fields = json.loads(data.read())
    #     print(fields)
    # text = []
    # try:
    #     for index, field in enumerate(fields):
    #         res = deepseek.get_field_info(field_info=field)
    #         sleep(1)
    #         print(res)
    #         text += [{**res, "id": field['id']}]
    # except:
    #     print(index)
    # with open(tmp_path / 'field.info.json', 'w+', encoding='utf-8') as info:
    #     info.write(json.dumps(text, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
