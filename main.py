'''
 # @ Author: Alucard
 # @ Create Time: 2025-04-14 11:49:05
 # @ Description: Notion API 异步命令行工具
 # @ 主要功能：
 #   程序入口
'''
from json import dumps
import asyncio
from notion_workspace import NotionWorkspace
from workflow import WorkFlow


async def main():
    """主函数

    工作流程：
        1. 初始化工作流实例（API请求频率限制为0.5秒/次）
        2. 更新或获取分类字段信息
        3. 获取待处理的文章列表
        4. 处理每篇文章的分类和作者信息

    """
    article_status = '信息缺失'
    pass_articles = list()
    workflow = WorkFlow(notion_workspace=NotionWorkspace(rate_limit=0.5),
                        update_field_info=False)
    # await workflow.workflow_remove_unknown_authors(fliter='进行中')
    # fields = await workflow.renew_fields()
    articles = await workflow.worklow_get_articles(
        database_id='c3f1101c-fbf7-4702-8dc4-a22578ac6430',
        fliter=article_status, filter_type="equals")
    for article in articles:
        try:
            # await workflow.workflow_main(
            #     article=article, fields=fields)
            await workflow.workflow_main_no_fields(
                article=article, article_status=article_status)
        except Exception as e:
            print(e)
            pass_articles += [article]
    if pass_articles:
        with open('pass_articles.json', 'w+', encoding='utf-8') as f:
            f.write(dumps(pass_articles, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
