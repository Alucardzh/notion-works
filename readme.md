# Notion 数据库管理工具

基于 FastAPI 和异步 Notion API 的数据库管理工具，提供直观的 Web 界面来管理您的 Notion 数据库。

## 基础配置  

### 1. 需要notion api token  

- 打开设置->连接->开发或管理继承![打开设置->连接->开发或管理继承](./images/微信截图_20250413141918.png)
- 新集成![新集成](./images/微信截图_20250413142414.png)
- 关联工作空间，类型内部,保存![关联工作空间，类型内部](./images/微信截图_20250413142336.png)
- 进入集成，授权，并保存出token密钥![进入集成，授权，并保存出token密钥](./images/微信截图_20250413142506.png)

### 2. 进行数据库连接  

- 进入工作空间，如文档中心![进入工作空间，如文档中心](./images/微信截图_20250413142711.png)
- 根据下图，选择创建的连接![根据下图，选择创建的连接](./images/微信截图_20250413142820.png)


## 功能特点

- 完全异步实现，提供更好的性能和并发处理能力
- 基于 FastAPI 的现代化 Web API
- 响应式 Web 界面，支持移动端访问
- 支持数据库的批量操作和属性管理
- 内置速率限制保护，避免触发 Notion API 限制

## 安装

1. 克隆仓库：
```bash
git clone https://github.com/Alucardzh/notion-works.git
cd notion-works
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境变量：
在项目根目录创建 `.env` 文件并添加您的 Notion API Token：
```env
NOTION_WORKSPACE_TOKEN=your_notion_api_token_here
```

## 使用方法

### 启动服务器

```bash
python api_server.py
```

服务器将在 http://localhost:8000 启动，您可以通过浏览器访问 Web 界面。

### API 文档

访问 http://localhost:8000/docs 查看完整的 API 文档。

### 主要功能

1. 数据库管理
   - 查看所有数据库列表
   - 查看数据库详细内容
   - 添加/删除数据库属性
   - 批量更新页面内容
   - 按条件筛选数据

2. 属性操作
   - 支持多种属性类型（文本、数字、复选框、选择、日期等）
   - 支持设置默认值
   - 支持批量属性管理

### 代码示例

1. 异步 API 使用示例：

```python
from notion_api_async import NotionAsyncAPI

async def main():
    api = NotionAsyncAPI()
    
    # 获取所有数据库
    databases = await api.list_all_databases()
    
    # 获取特定数据库内容
    content = await api.get_database_content(database_id)
    
    # 添加新属性
    success = await api.add_database_property(
        database_id,
        "新属性",
        "text",
        default_value="默认值"
    )
    
    # 筛选数据
    results = await api.query_database_with_filter(
        database_id,
        "属性名",
        "搜索值",
        "contains"
    )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

2. FastAPI 路由示例：

```python
from fastapi import FastAPI, HTTPException
from notion_api_async import NotionAsyncAPI

app = FastAPI()
api = NotionAsyncAPI()

@app.get("/databases/{database_id}")
async def get_database_content(database_id: str):
    try:
        content = await api.get_database_content(database_id)
        return content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## 性能优化

1. 异步并发
   - 使用 `asyncio` 处理并发请求
   - 内置速率限制保护
   - 支持批量异步操作

2. 缓存优化
   - 数据库内容缓存
   - 支持手动清除缓存
   - 可配置缓存策略

## 注意事项

1. API 限制
   - Notion API 有请求频率限制
   - 建议使用内置的速率限制功能
   - 大批量操作时注意控制并发数

2. 异步操作
   - 所有数据库操作都是异步的
   - 需要在异步环境中使用
   - 注意正确处理异常

3. 安全性
   - 不要在代码中硬编码 API Token
   - 使用环境变量管理敏感信息
   - 注意 CORS 设置

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License
