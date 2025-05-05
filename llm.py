'''
 # @ Author: Alucard
 # @ Create Time: 2025-04-15 09:02:47
 # @ Modified by: Alucard
 # @ Modified time: 2025-04-15 09:11:35
 # @ Description: LLM 客户端封装，支持 DeepSeek 和 Ollama 模型
 # @ 主要功能：
 #   1. 文章内容分析
 #   2. 作者识别
 #   3. 文章分类
 #   4. AI封面图生成
'''

import os
import json
from uuid import uuid4
from typing import Union, Dict
from pathlib import Path
import time
from dotenv import load_dotenv
from openai import OpenAI
from tools.searxing_search import SearxingSearch
from tools.logging_config import setup_logger

logger = setup_logger(__name__)
# 加载环境变量
load_dotenv()

# API配置
DEEKSEE_API_KEY = os.getenv("DEEKSEE_API_KEY", '')  # DeepSeek API密钥
DEEKSEE_MODEL = os.getenv("DEEKSEE_MODEL", "deepseek-chat")  # DeepSeek模型名称
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", '')  # Ollama模型名称
OLLAMA_URL = os.getenv("OLLAMA_URL", '')  # Ollama服务URL
SEARXING_URL = os.getenv("SEARXING_HOST", "http://localhost:8080")


class DeepSeekClient:
    """DeepSeek API客户端封装类

    主要功能：
    1. 文章内容分析
    2. 作者信息识别
    3. 文章类型分类
    4. 生成AI封面图提示词

    使用方法：
    client = DeepSeekClient()
    result = client.get_article_info("article.md")
    """

    # 系统提示词配置
    system_prompt_for_get_article_info = {
        "content": """
            You are a smart assistant.
            Please read the article and provide the following information:
            1. Who is the author of the article? If this article is an interview, the author is defined as the interviewee.
            2. What type of article can it be classified as?
            3. Need to generate an AI cover image for the article, please provide suitable drawing prompts.
            Please answer in Chinese and output in the following format:
            {"author": author(If you cannot determine the author, please set author to "unknown".),
            "category": category(The category must be selected within the range of 分类范围. The article category can be multiple.),
            "cover_image_prompt": cover_image_prompt(The cover image prompt should be in English.),
            "author_english_name": author name in English or Chinese Pinyin,
            "author_chinese_name": author name in Chinese(if available) or none if you unknown}.
            """
    }
    system_prompt_for_get_article_info_no_fields = {
        "content": """
            You are a smart assistant.
            Please read the article and provide the following information:
            Who is the author of the article? If this article is an interview, the author is defined as the interviewee.
            Please answer in Chinese and output in the following format:
            {"author": author(If you cannot determine the author, please set author to "unknown".),
            "author_english_name": author name in English or Chinese Pinyin,
            "author_chinese_name": author name in Chinese(if available) or none if you unknown}.
            """
    }
    system_prompt_for_get_author_info = {
        "content": """
            You are a smart assistant.
            Please read the information sent by the user and provide the following information:
            1. The person with this name might be a celebrity, a scientist, a politician, a financial industry expert, or a well-known blog author. So, who is the person with this name? If you don't know, don't make it up. Just answer "unknown." If the name is incomplete, please provide the full English name (if available) and the Chinese name (if available).
            2. Provide a brief introduction of this person.
            Please answer in Chinese and output in the following format:
            {"english name":english name, "chinese name":chinese name, "introduction": introduction}。
            The English name should be in English.
            """
    }
    system_prompt_for_get_field_info = {
        "content": """
            You are a smart assistant.
            I'd like to classify some articles and have come up with my own category names. Could you analyze my naming and guess the reasoning behind the classification?
            Please answer in Chinese and output in the following format:
            {"category":category, "reason":reason}。
            """
    }

    def __init__(self, model: str = DEEKSEE_MODEL):
        """初始化DeepSeek客户端

        Args:
            model: 使用的模型名称，默认使用环境变量中的DEEKSEE_MODEL

        功能：
            1. 初始化OpenAI客户端
            2. 配置DeepSeek API地址
            3. 设置使用的模型
        """
        self.client = OpenAI(
            api_key=DEEKSEE_API_KEY,
            base_url="https://api.deepseek.com"
        )
        self.model = model
        self.assistant_name = 'system'

    @staticmethod
    def check_file(article_text: Union[str, Path]) -> str:
        """检查并读取文章内容

        Args:
            article_text: 文章内容或文件路径

        Returns:
            str: 文章内容

        功能：
            1. 支持直接传入文本内容
            2. 支持传入文件路径
            3. 自动处理文件读取
        """
        if Path(article_text).is_file():
            with open(article_text, "r", encoding="utf-8") as f:
                article_text = f.read()
        return article_text

    @staticmethod
    def answer_to_json(answer: str) -> Dict:
        """将LLM回答转换为JSON格式

        Args:
            answer: LLM的原始回答文本

        Returns:
            Dict: 解析后的JSON对象

        功能：
            1. 清理回答中的代码块标记
            2. 解析JSON格式
            3. 返回结构化数据
        """
        answer = answer.split("\n")
        try:
            index = answer.index('</think>')
        except ValueError:
            index = -1
        a = [i for i in answer[index+1:] if not i.strip().startswith("```")]
        answer = json.loads("".join(a))
        return answer

    def get_article_info_from_file(
        self, article_text: Union[str, Path],
        content: str = None
    ) -> Dict:
        """获取文章信息

        Args:
            article_text: 文章内容或文件路径

        Returns:
            Dict: 包含author、category和cover_image_prompt的字典

        功能：
            1. 分析文章内容
            2. 识别作者信息
            3. 确定文章类型
            4. 生成封面图提示词
            5. 错误处理和日志记录
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": f"{self.assistant_name}",
                 **self.system_prompt_for_get_article_info},
                {"role": "user", "content": self.check_file(article_text)},
            ],
            stream=False
        )
        content = response.choices[0].message.content
        try:
            return self.answer_to_json(content)
        except json.decoder.JSONDecodeError as e:
            # 保存错误日志
            with open(f"tmp/{uuid4().hex}.txt", "a", encoding="utf-8") as f:
                f.write(f"{article_text}\n{content}\n\n")
            print(f"Error: {e}")
            return None

    def get_author_info(self, author_info: Dict) -> Dict:
        """_summary_

        Args:
            author_info (Dict): _description_

        Returns:
            Dict: _description_
        """
        name = author_info.get('name')
        desc = author_info.get('description', '')
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": f"{self.assistant_name}",
                 **self.system_prompt_for_get_author_info},
                {"role": "user", "content": f"{name}, {desc}"},
            ],
            stream=False
        )
        content = response.choices[0].message.content
        try:
            return self.answer_to_json(content)
        except json.decoder.JSONDecodeError as e:
            # 保存错误日志
            with open(f"tmp/{uuid4().hex}.txt", "a", encoding="utf-8") as f:
                f.write(f"{author_info.get('id')}\n{content}\n\n")
            print(f"Error: {e}")
            return {}

    def get_field_info(self, field_info: Dict) -> Dict:
        """_summary_

        Args:
            author_info (Dict): _description_

        Returns:
            Dict: _description_
        """
        name = field_info.get('name')
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": f"{self.assistant_name}",
                 **self.system_prompt_for_get_field_info},
                {"role": "user", "content": f"{name}"},
            ],
            stream=False
        )
        content = response.choices[0].message.content
        try:
            return self.answer_to_json(content)
        except json.decoder.JSONDecodeError as e:
            # 保存错误日志
            with open(f"tmp/{uuid4().hex}.txt", "a", encoding="utf-8") as f:
                f.write(f"{field_info.get('id')}\n{content}\n\n")
            print(f"Error: {e}")
            return None


class OllamaClient(DeepSeekClient):
    """Ollama API客户端封装类

    继承DeepSeek客户端的功能，使用本地Ollama服务

    主要特点：
    1. 支持本地部署
    2. 兼容DeepSeek接口
    3. 无需远程API
    4. 支持联网搜索

    使用方法：
    client = OllamaClient()
    result = client.get_article_info("article.md")
    """

    def __init__(self, model: str = OLLAMA_MODEL):
        """初始化Ollama客户端

        Args:
            model: 使用的模型名称，默认使用环境变量中的OLLAMA_MODEL

        功能：
            1. 继承DeepSeek客户端初始化
            2. 配置Ollama服务地址
            3. 设置本地模型
            4. 初始化Searxing搜索客户端
        """
        super().__init__(model)
        self.model = model
        self.client = OpenAI(base_url=f'{OLLAMA_URL}/v1/', api_key='ollama')
        self.assistant_name = 'assistant'
        self.searxing = SearxingSearch(
            base_url=SEARXING_URL,
            max_retries=3
        )

    def get_article_info_from_file(
        self, article_text: Union[str, Path],
        content: str = None,
    ) -> Dict:
        """获取文章信息，支持联网搜索

        Args:
            article_text: 文章内容或文件路径

        Returns:
            Dict: 包含author、category和cover_image_prompt的字典

        功能：
            1. 分析文章内容
            2. 识别作者信息
            3. 确定文章类型
            4. 生成封面图提示词
            5. 使用Searxing进行联网搜索以提高准确性
            6. 错误处理和日志记录
        """
        # 获取文章内容
        article_text = self.check_file(article_text)

        # 使用Searxing进行联网搜索
        try:
            search_results = self.searxing.search(
                query=content[:100].replace(
                    "*", '').replace("\n", ""),  # 使用文章前100个字符作为搜索关键词
                categories=["general"],
                language="zh-CN"
            )

            # 构建包含搜索结果的提示词
            search_context = "\n\n相关搜索结果：\n"
            if search_results and "results" in search_results:
                for result in search_results["results"][:3]:  # 只使用前3个结果
                    search_context += f"- {result.get('title', '')}: {result.get('content', '')}\n"
        except Exception as e:
            logger.info("搜索失败: %s", (e))
            search_context = ""

        # 构建完整的提示词
        full_prompt = f"""{article_text}\n======以下是根据文章前100个字符进行网页搜索的相关结果=========\n{search_context}\n===============搜索内容结束,可以在回答时进行参考==================\n"""

        # 调用Ollama API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": full_prompt + '\n' + self.system_prompt_for_get_article_info.get('content')},
            ],
            stream=False
        )

        res_content = response.choices[0].message.content
        try:
            with open(f"tmp/{time.time()}.txt", "a", encoding="utf-8") as f:
                f.write(f"{full_prompt}\n\n{res_content}")
            return self.answer_to_json(res_content)
        except json.decoder.JSONDecodeError as e:
            # 保存错误日志
            with open(f"tmp/{time.time()}.txt", "a", encoding="utf-8") as f:
                f.write(f"{full_prompt}\n\n{res_content}")
            print(f"Error: {e}")
            return None

    def get_article_info_from_file_no_fields(
        self, article_text: Union[str, Path],
        content: str = None,
    ) -> Dict:
        """获取文章信息，支持联网搜索

        Args:
            article_text: 文章内容或文件路径

        Returns:
            Dict: 包含author、category和cover_image_prompt的字典

        功能：
            1. 分析文章内容
            2. 识别作者信息
            3. 确定文章类型
            4. 生成封面图提示词
            5. 使用Searxing进行联网搜索以提高准确性
            6. 错误处理和日志记录
        """
        # 获取文章内容
        article_text = self.check_file(article_text)

        # 使用Searxing进行联网搜索
        try:
            search_results = self.searxing.search(
                query=content[:100].replace(
                    "*", '').replace("\n", ""),  # 使用文章前100个字符作为搜索关键词
                categories=["general"],
                language="zh-CN"
            )

            # 构建包含搜索结果的提示词
            search_context = "\n\n相关搜索结果：\n"
            if search_results and "results" in search_results:
                for result in search_results["results"][:5]:  # 只使用前3个结果
                    search_context += f"- {result.get('title', '')}: {result.get('content', '')}\n"
        except Exception as e:
            logger.info("搜索失败: %s", (e))
            search_context = ""

        # 构建完整的提示词
        full_prompt = f"""{article_text}\n======以下是根据文章前100个字符进行网页搜索的相关结果=========\n{search_context}\n===============搜索内容结束,可以在回答时进行参考==================\n"""

        # 调用Ollama API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": full_prompt + '\n' + self.system_prompt_for_get_article_info_no_fields.get('content')},
            ],
            stream=False
        )

        res_content = response.choices[0].message.content
        try:
            with open(f"tmp/{time.time()}.txt", "a", encoding="utf-8") as f:
                f.write(f"{full_prompt}\n\n{res_content}")
            return self.answer_to_json(res_content)
        except json.decoder.JSONDecodeError as e:
            # 保存错误日志
            with open(f"tmp/{time.time()}.txt", "a", encoding="utf-8") as f:
                f.write(f"{full_prompt}\n\n{res_content}")
            print(f"Error: {e}")
            return None
