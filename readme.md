# Notion 数据库管理工具

## 基础配置  

### 1. 需要notion api token  

- 打开设置->连接->开发或管理继承![打开设置->连接->开发或管理继承](./images/微信截图_20250413141918.png)
- 新集成![新集成](./images/微信截图_20250413142414.png)
- 关联工作空间，类型内部,保存![关联工作空间，类型内部](./images/微信截图_20250413142336.png)
- 进入集成，授权，并保存出token密钥![进入集成，授权，并保存出token密钥](./images/微信截图_20250413142506.png)

### 2. 进行数据库连接  

- 进入工作空间，如文档中心![进入工作空间，如文档中心](./images/微信截图_20250413142711.png)
- 根据下图，选择创建的连接![根据下图，选择创建的连接](./images/微信截图_20250413142820.png)

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

## 注意事项

1. API 限制
   - Notion API 有请求频率限制（每分钟最多 3 个写操作）
   - 建议使用内置的速率限制功能
   - 大批量操作时注意控制并发数

2. 异步操作
   - 所有数据库操作都是异步的
   - 需要在异步环境中使用
   - 使用 `asyncio.run()` 或在其他异步函数中调用

3. 安全性
   - 不要在代码中硬编码 API Token
   - 使用环境变量管理敏感信息
   - 注意 CORS 设置
   - 定期更新依赖包以修复潜在安全问题

## 常见问题

1. 速率限制问题
   - 使用内置的重试机制
   - 适当增加操作间隔
   - 监控 API 响应状态

2. 数据库权限问题
   - 确保 API Token 有足够权限
   - 检查数据库访问设置
   - 验证页面共享权限

## 许可证

MIT License

Copyright (c) 2024 Alucardzh

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
