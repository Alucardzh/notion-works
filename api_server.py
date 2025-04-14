'''
 # @ Author: Alucard
 # @ Create Time: 2025-04-14 15:30:05
 # @ Description: Notion API FastAPI 后端服务
'''

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, Union
from notion_api_async import NotionAsyncAPI
import os

app = FastAPI(
    title="Notion 数据库管理工具",
    description="基于 FastAPI 的 Notion 数据库管理工具",
    version="1.0.0"
)

# 配置静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 实例（单例模式）
notion_api = NotionAsyncAPI()


# 请求模型
class PropertyModel(BaseModel):
    database_id: str
    property_name: str
    property_type: str
    default_value: Optional[Union[str, int, bool]] = None


class FilterModel(BaseModel):
    database_id: str
    filter_property: str
    filter_value: Union[str, int, bool]
    filter_type: str = "equals"


class UpdateTextModel(BaseModel):
    database_id: str
    text_content: str


# 主页路由
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """返回主页 HTML"""
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()


# API 路由
@app.get("/databases")
async def list_databases():
    """获取所有数据库列表"""
    try:
        databases = await notion_api.list_all_databases()
        return [{
            "id": db["id"],
            "title": db.get('title', [{'plain_text': '未命名'}])[0]['plain_text']
        } for db in databases]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/databases/{database_id}")
async def get_database_content(database_id: str):
    """获取指定数据库的内容"""
    try:
        content = await notion_api.get_database_content(database_id)
        return content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/databases/property")
async def add_database_property(property_data: PropertyModel):
    """添加数据库属性"""
    try:
        success = await notion_api.add_database_property(
            property_data.database_id,
            property_data.property_name,
            property_data.property_type,
            property_data.default_value
        )
        if success:
            return {"message": f"成功添加属性：{property_data.property_name}"}
        raise HTTPException(status_code=400, detail="添加属性失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/databases/{database_id}/properties/{property_name}")
async def remove_database_property(database_id: str, property_name: str):
    """删除数据库属性"""
    try:
        success = await notion_api.remove_database_property(
            database_id, property_name
        )
        if success:
            return {"message": f"成功删除属性：{property_name}"}
        raise HTTPException(status_code=400, detail="删除属性失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/databases/filter")
async def filter_database_content(filter_data: FilterModel):
    """筛选数据库内容"""
    try:
        results = await notion_api.query_database_with_filter(
            filter_data.database_id,
            filter_data.filter_property,
            filter_data.filter_value,
            filter_data.filter_type
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/databases/update-text")
async def update_database_text(update_data: UpdateTextModel):
    """批量更新数据库中的文本内容"""
    try:
        content = await notion_api.get_database_content(update_data.database_id)
        success_count = 0
        for page in content:
            text_property = page.get('properties', {}).get('文本', {})
            if not text_property.get('rich_text', []):
                if await notion_api.update_page_text(
                    page['id'],
                    update_data.text_content
                ):
                    success_count += 1
        return {
            "message": "更新完成",
            "success_count": success_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    # 确保目录存在
    os.makedirs("static/js", exist_ok=True)
    os.makedirs("templates", exist_ok=True)
    uvicorn.run(app, host="0.0.0.0", port=8000) 