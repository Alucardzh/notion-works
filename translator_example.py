'''
 # @ Author: Alucard
 # @ Create Time: 2025-05-06 14:33:05
 # @ Modified by: Alucard
 # @ Modified time: 2025-05-06 14:33:25
 # @ Description:
 '''

from pathlib import Path
from llm import DeepSeekClient as LlmClient


if __name__ == "__main__":
    article = Path('./article.md')
    llm_model = LlmClient()
    content = llm_model.translation(
        article_text=article, whole=False, max_chars=1000)
    with open(Path('./tr_article.md'), 'w+', encoding='utf-8') as f:
        f.write(content)
