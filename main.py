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
import json
import asyncio
from notion_api import NotionAsyncAPI, save_data_to_file


async def save_temp_data_to_json(data, filename):
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
    tmp_path = Path(f'tmp/{os.getenv("NOTION_WORKSPACE_TOKEN")}')
    # 获取数据库列表示例（已注释）
    # databases = await notion_api.get_formatted_databases()
    # await save_temp_data_to_json(databases, tmp_path / f'databases.json')

    # 使用过滤器查询数据库
    content = await notion_api.query_database_with_filter(
        database_id='c3f1101c-fbf7-4702-8dc4-a22578ac6430',
        filter_property="状态",
        filter_value="未开始",
        filter_type="equals"
    )
    # 保存查询结果
    await save_temp_data_to_json(content, tmp_path / 'content.json')

    # 遍历结果并导出为Markdown
    for i in content:
        page_id = i.get("id")
        print(page_id)
        # 导出页面内容为Markdown格式
        page_content, page = await notion_api.export_page_to_markdown(
            page_id=page_id,
            output_path=tmp_path / f'output/{page_id}.md'
        )
        if page:
            # 同时保存页面的原始数据
            await save_temp_data_to_json(
                page, tmp_path / f'output/{page_id}.json')
            print(page_content)


if __name__ == "__main__":
    asyncio.run(main())
