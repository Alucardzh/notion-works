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
from .logging_config import setup_logger

# 配置日志
logger = setup_logger(__name__)


class SearxingSearch:
    def __init__(self, base_url: str, api_key: Optional[str] = None, max_retries: int = 3):
        """
        初始化 Searxing 搜索客户端

        Args:
            base_url (str): Searxing 实例的基础 URL
            api_key (Optional[str]): API 密钥（如果需要）
            max_retries (int): 最大重试次数
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Connection': 'keep-alive'
        }
        self.max_retries = max_retries

        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'

    def search(self, query: str,
               categories: Optional[List[str]] = None,
               engines: Optional[List[str]] = ['google'],
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
            'engines': ','.join(engines)
        }

        if categories:
            params['categories'] = ','.join(categories)

        for attempt in range(self.max_retries):
            try:
                # 使用不同的客户端配置
                transport = httpx.HTTPTransport(
                    retries=3,
                    verify=False,
                    trust_env=True
                )

                with httpx.Client(
                    transport=transport,
                    headers=self.headers,
                    timeout=httpx.Timeout(30.0, connect=10.0),
                    follow_redirects=True,
                    limits=httpx.Limits(
                        max_keepalive_connections=5, max_connections=10)
                ) as client:
                    response = client.get(endpoint, params=params)
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPError as e:
                if attempt < self.max_retries - 1:
                    pass
                else:
                    raise Exception(
                        f"搜索请求失败，已重试 {self.max_retries} 次: {str(e)}")
            except Exception as e:
                raise


def main_for_example():
    try:
        # 初始化搜索客户端
        searxing = SearxingSearch(
            base_url="http://192.168.3.244:58080",
            max_retries=3
        )

        # 执行搜索
        results = searxing.search(
            query="Python 编程",
            categories=["general"],
            language="zh-CN"
        )

        # 打印结果
        print(results)
    except Exception as e:
        print(f"程序执行失败: {str(e)}")


if __name__ == "__main__":
    main_for_example()
