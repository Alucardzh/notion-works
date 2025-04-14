'''
 # @ Author: Alucard
 # @ Create Time: 2025-04-13 13:44:41
 # @ Modified by: Alucard
 # @ Modified time: 2025-04-14 11:49:05
 # @ Description:
'''


import os
import time
import json
import argparse
from dotenv import load_dotenv
from notion_client import Client


class NotionAPI:
    """Notion API 交互类"""

    def __init__(self, rate_limit=0.5):
        """初始化 Notion 客户端

        Args:
            rate_limit: API调用间隔时间（秒）
        """
        load_dotenv()
        self.notion = Client(auth=os.getenv("NOTION_WORKSPACE_TOKEN"))
        self.rate_limit = rate_limit
        self.last_api_call = 0

    def _rate_limit_wait(self):
        """等待以确保API调用频率不超过限制"""
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call
        if time_since_last_call < self.rate_limit:
            time.sleep(self.rate_limit - time_since_last_call)
        self.last_api_call = time.time()

    def list_all_databases(self):
        """列出工作空间中的所有数据库"""
        try:
            self._rate_limit_wait()
            response = self.notion.search(
                filter={"property": "object", "value": "database"}
            )
            return response.get("results", [])
        except Exception as e:
            print(f"获取数据库列表时出错: {e}")
            return []

    def list_all_pages(self):
        """列出工作空间中的所有页面"""
        try:
            self._rate_limit_wait()
            response = self.notion.search(
                filter={"property": "object", "value": "page"}
            )
            return response.get("results", [])
        except Exception as e:
            print(f"获取页面列表时出错: {e}")
            return []

    def get_database_content(self, database_id):
        """获取指定数据库的内容"""
        try:
            self._rate_limit_wait()
            response = self.notion.databases.query(
                database_id=database_id
            )
            return response.get("results", [])
        except Exception as e:
            print(f"获取数据库内容时出错: {e}")
            return []

    def get_database_by_name(self, database_name):
        """根据数据库名称获取数据库ID"""
        databases = self.list_all_databases()
        for db in databases:
            title = db.get('title', [{'plain_text': '未命名'}])[0]['plain_text']
            if title == database_name:
                return db['id']
        return None

    def get_database_content_by_name(self, database_name):
        """根据数据库名称获取其内容"""
        database_id = self.get_database_by_name(database_name)
        if database_id:
            return self.get_database_content(database_id)
        print(f"未找到名为 '{database_name}' 的数据库")
        return []

    def get_page_by_title(self, database_name, page_title):
        """根据数据库名称和页面标题获取页面内容"""
        content = self.get_database_content_by_name(database_name)
        if content:
            with open('./tmp/content.json', 'w+', encoding='utf-8') as f:
                f.write(json.dumps(content, ensure_ascii=False))
        for page in content:
            title = page.get('properties', {}).get('文档名称', {}).get(
                'title', [{'plain_text': '未命名'}])[0]['plain_text']
            if title == page_title:
                return self.get_page_content(page['id'])
        return None

    def get_page_content(self, page_id):
        """获取指定页面的内容"""
        try:
            self._rate_limit_wait()
            response = self.notion.blocks.children.list(
                block_id=page_id
            )
            return response.get("results", [])
        except Exception as e:
            print(f"获取页面内容时出错: {e}")
            return []

    def print_page_content(self, blocks, indent=0):
        """递归打印页面内容"""
        for block in blocks:
            block_type = block.get('type')
            content = block.get(block_type, {})

            # 处理不同类型的块
            if block_type == 'paragraph':
                text = content.get('rich_text', [])
                if text:
                    print(' ' * indent +
                          ''.join([t.get('plain_text', '') for t in text]))
            elif block_type == 'heading_1':
                text = content.get('rich_text', [])
                if text:
                    print(' ' * indent + '# ' +
                          ''.join([t.get('plain_text', '') for t in text]))
            elif block_type == 'heading_2':
                text = content.get('rich_text', [])
                if text:
                    print(' ' * indent + '## ' +
                          ''.join([t.get('plain_text', '') for t in text]))
            elif block_type == 'heading_3':
                text = content.get('rich_text', [])
                if text:
                    print(' ' * indent + '### ' +
                          ''.join([t.get('plain_text', '') for t in text]))

            # 如果有子块，递归处理
            if block.get('has_children', False):
                children = self.get_page_content(block['id'])
                self.print_page_content(children, indent + 2)

    def print_all_pages_in_database(self, database_name):
        """打印数据库中所有页面的内容"""
        content = self.get_database_content_by_name(database_name)
        if not content:
            return
        with open('./tmp/content.json', 'w+', encoding='utf-8') as f:
            f.write(json.dumps(content, ensure_ascii=False))
        print(f"\n开始遍历数据库 '{database_name}' 中的所有页面...")
        total_pages = len(content)
        print(f"共找到 {total_pages} 个页面")

        for index, page in enumerate(content, 1):
            title = page.get('properties', {}).get('文档名称', {}).get(
                'title', [{'plain_text': '未命名'}])[0]['plain_text']
            print(f"\n[{index}/{total_pages}] 正在处理页面: {title}")
            print("-" * 50)

            page_content = self.get_page_content(page['id'])
            if page_content:
                self.print_page_content(page_content)
            else:
                print("该页面没有内容")

            print("-" * 50)
            print(f"页面 {title} 处理完成")
            print(f"进度: {index}/{total_pages} ({index/total_pages*100:.1f}%)")

    def update_page_text(self, page_id, text_content):
        """更新页面的文本内容

        Args:
            page_id: 页面ID
            text_content: 要更新的文本内容
        """
        try:
            self._rate_limit_wait()
            self.notion.pages.update(
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

    def update_empty_text_pages(self, database_name, update_text):
        """更新数据库中所有空文本的页面

        Args:
            database_name: 数据库名称
            update_text: 要更新的文本内容
        """
        content = self.get_database_content_by_name(database_name)
        if not content:
            return

        print(f"\n开始更新数据库 '{database_name}' 中的空文本页面...")
        print(f"更新内容: {update_text}")
        total_pages = len(content)
        updated_count = 0

        for index, page in enumerate(content, 1):
            title = page.get('properties', {}).get('文档名称', {}).get(
                'title', [{'plain_text': '未命名'}])[0]['plain_text']
            text_property = page.get('properties', {}).get('文本', {})
            rich_text = text_property.get('rich_text', [])

            if not rich_text:
                print(f"\n[{index}/{total_pages}] 正在更新页面: {title}")
                if self.update_page_text(page['id'], update_text):
                    updated_count += 1
                    print(f"页面 {title} 更新成功")
                else:
                    print(f"页面 {title} 更新失败")

        print(f"\n更新完成！共更新了 {updated_count} 个页面")


def main(db_name: str, page_title: str = None, update_text: str = None):
    """主函数

    Args:
        db_name: 数据库名称
        page_title: 页面标题（可选）
        update_text: 要更新的文本内容（可选）
    """
    # 创建 NotionAPI 实例，设置API调用间隔为0.5秒
    notion_api = NotionAPI(rate_limit=0.5)

    if page_title:
        # 获取指定页面的内容
        page_content = notion_api.get_page_by_title(db_name, page_title)
        if page_content:
            print(f"\n页面 '{page_title}' 的内容:")
            notion_api.print_page_content(page_content)
        else:
            print(f"未找到标题为 '{page_title}' 的页面")
    else:
        # 更新数据库中所有空文本的页面
        notion_api.update_empty_text_pages(db_name, update_text)


if __name__ == "__main__":
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='Notion API 工具')
    parser.add_argument('--db', type=str, default="文档中心", help='数据库名称')
    parser.add_argument('--page', type=str, help='页面标题')
    parser.add_argument('--text', type=str, default="测试数据", help='要更新的文本内容')

    # 解析命令行参数
    args = parser.parse_args()

    # 调用主函数
    main(db_name=args.db, page_title=args.page, update_text=args.text)
