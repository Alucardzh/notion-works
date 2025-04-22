'''
 # @ Author: Alucard
 # @ Create Time: 2025-04-22 12:29:29
 # @ Modified by: Alucard
 # @ Modified time: 2025-04-22 12:34:03
 # @ Description:
 '''

import httpx
from typing import List, Dict, Optional
from urllib.parse import urljoin


class SearxingSearch:
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """
        初始化 Searxing 搜索客户端

        Args:
            base_url (str): Searxing 实例的基础 URL
            api_key (Optional[str]): API 密钥（如果需要）
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {}

        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'

    async def search(self, query: str,
                     categories: Optional[List[str]] = None,
                     engines: Optional[List[str]] = None,
                     language: str = 'zh-CN',
                     page: int = 1,
                     format: str = 'json') -> Dict:
        """
        执行异步搜索查询

        Args:
            query (str): 搜索查询字符串
            categories (Optional[List[str]]): 搜索类别列表
            engines (Optional[List[str]]): 搜索引擎列表
            language (str): 搜索语言
            page (int): 页码
            format (str): 返回格式

        Returns:
            Dict: 搜索结果
        """
        endpoint = urljoin(self.base_url, '/search')

        params = {
            'q': query,
            'format': format,
            'language': language,
            'pageno': page
        }

        if categories:
            params['categories'] = ','.join(categories)
        if engines:
            params['engines'] = ','.join(engines)

        async with httpx.AsyncClient(headers=self.headers) as client:
            try:
                response = await client.get(endpoint, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                raise Exception(f"搜索请求失败: {str(e)}")

    async def get_engines(self) -> Dict:
        """
        异步获取可用的搜索引擎列表

        Returns:
            Dict: 搜索引擎信息
        """
        endpoint = urljoin(self.base_url, '/engines')

        async with httpx.AsyncClient(headers=self.headers) as client:
            try:
                response = await client.get(endpoint)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                raise Exception(f"获取搜索引擎列表失败: {str(e)}")

# 使用示例


async def main():
    # 初始化搜索客户端
    searxing = SearxingSearch(
        base_url="http://192.168.3.244:58080",
    )

    # 执行搜索
    results = await searxing.search(
        query="Python 编程",
        categories=["general"],
        language="zh-CN"
    )

    # 打印结果
    print(results)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
