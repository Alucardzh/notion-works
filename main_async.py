'''
 # @ Author: Alucard
 # @ Create Time: 2025-04-14 11:49:05
 # @ Description: Notion API 异步命令行工具
'''

import asyncio
import argparse
from notion_api_async import NotionAsyncAPI


async def main():
    """异步主函数入口"""
    parser = argparse.ArgumentParser(description='Notion API 异步命令行工具')

    # 基本参数
    parser.add_argument('--db', type=str, required=True, help='数据库名称')
    parser.add_argument(
        '--action', type=str, required=True,
        choices=['view', 'update', 'add_prop', 'remove_prop', 'filter'],
        help='操作类型'
    )

    # 查看和更新页面相关参数
    parser.add_argument('--page', type=str, help='页面标题')
    parser.add_argument('--text', type=str, help='要更新的文本内容')

    # 属性管理相关参数
    parser.add_argument('--prop_name', type=str, help='属性名称')
    parser.add_argument(
        '--prop_type', type=str,
        choices=['text', 'number', 'checkbox', 'select', 'date'],
        help='属性类型'
    )
    parser.add_argument('--default_value', type=str, help='属性默认值')

    # 筛选相关参数
    parser.add_argument('--filter_prop', type=str, help='筛选属性名称')
    parser.add_argument('--filter_value', type=str, help='筛选值')
    parser.add_argument(
        '--filter_type', type=str, default='equals',
        choices=['equals', 'contains', 'greater_than', 'less_than'],
        help='筛选类型'
    )

    args = parser.parse_args()

    async with NotionAsyncAPI(rate_limit=0.5) as notion_api:
        # 获取数据库 ID
        database_id = await notion_api.get_database_by_name(args.db)
        if not database_id:
            print(f"未找到数据库: {args.db}")
            return

        # 根据操作类型执行相应的功能
        if args.action == 'view':
            if args.page:
                # 查看特定页面
                page_content = await notion_api.get_page_content(database_id)
                if page_content:
                    print(f"\n页面 '{args.page}' 的内容:")
                    for block in page_content:
                        print(block.get('type'), block.get('content', {}))
                else:
                    print(f"未找到标题为 '{args.page}' 的页面")
            else:
                # 查看数据库内容
                content = await notion_api.get_database_content(database_id)
                print(f"\n数据库内容 (共 {len(content)} 条):")
                for item in content:
                    title = item.get('properties', {}).get('文档名称', {}).get(
                        'title', [{'plain_text': '未命名'}])[0]['plain_text']
                    print(f"- {title}")

        elif args.action == 'update':
            if not args.text:
                print("更新操作需要提供 --text 参数")
                return
            # 获取所有页面并更新
            content = await notion_api.get_database_content(database_id)
            update_tasks = []
            for page in content:
                text_property = page.get('properties', {}).get('文本', {})
                if not text_property.get('rich_text', []):
                    update_tasks.append(
                        notion_api.update_page_text(page['id'], args.text)
                    )
            if update_tasks:
                results = await asyncio.gather(*update_tasks)
                success_count = sum(1 for r in results if r)
                print(f"更新完成！成功更新 {success_count} 个页面")
            else:
                print("没有找到需要更新的页面")

        elif args.action == 'add_prop':
            if not all([args.prop_name, args.prop_type]):
                print("添加属性需要提供 --prop_name 和 --prop_type 参数")
                return
            success = await notion_api.add_database_property(
                database_id, args.prop_name, args.prop_type, args.default_value
            )
            if success:
                print(f"成功添加属性: {args.prop_name}")
            else:
                print(f"添加属性失败: {args.prop_name}")

        elif args.action == 'remove_prop':
            if not args.prop_name:
                print("删除属性需要提供 --prop_name 参数")
                return
            success = await notion_api.remove_database_property(
                database_id, args.prop_name
            )
            if success:
                print(f"成功删除属性: {args.prop_name}")
            else:
                print(f"删除属性失败: {args.prop_name}")

        elif args.action == 'filter':
            if not all([args.filter_prop, args.filter_value]):
                print("筛选需要提供 --filter_prop 和 --filter_value 参数")
                return
            results = await notion_api.query_database_with_filter(
                database_id, args.filter_prop,
                args.filter_value, args.filter_type
            )
            print(f"\n筛选结果 (共 {len(results)} 条):")
            for page in results:
                title = page.get('properties', {}).get('文档名称', {}).get(
                    'title', [{'plain_text': '未命名'}])[0]['plain_text']
                print(f"- {title}")


if __name__ == "__main__":
    asyncio.run(main())
