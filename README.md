# 本草视界 · TCM Visual Query System

## 运行说明

### 一、启动后端

进入后端目录：

```powershell
cd backend
```

安装依赖：

```powershell
pip install -r requirements.txt
```

在 `backend` 目录下创建 `.env` 文件，示例内容如下：

```env
PROJECT_NAME=TCM Visual Query System API
PROJECT_VERSION=0.1.0
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=123456
MYSQL_DATABASE=tcm
SQL_ECHO=false
VISION_API_URL=
VISION_API_KEY=
VISION_API_TIMEOUT=20
```

启动服务：

```powershell
# Run from the repository root
uvicorn app.main:app --reload

# Or run from the backend directory
cd backend
uvicorn app.main:app --reload
```

默认服务地址：

```text
http://127.0.0.1:8000
```

说明：

- 后端启动时会自动执行建表和样例数据初始化
- 请提前确保本机 MySQL 已安装并已创建可连接的数据库
- 若数据库账号、密码或库名不同，请同步修改 `.env`
- 如果暂时不配置 `VISION_API_URL`，拍照识别会退回到按文件名匹配的降级模式

### 一点五、启动本地视觉适配服务

如果你希望拍照识别真的基于图片内容工作，而不是按文件名降级匹配，建议在 `backend` 目录下额外创建 `.env.vision`。

可参考 [backend/.env.vision.example](/E:/GitDownload/project/tcm-visual-query-system/backend/.env.vision.example)：

```env
VISION_PROVIDER_NAME=DashScope
ADAPTER_API_KEY=your_local_adapter_token
OPENAI_COMPATIBLE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_COMPATIBLE_API_KEY=your_provider_api_key
VISION_MODEL=qwen-vl-plus-latest
VISION_REQUEST_TIMEOUT=60
VISION_TEMPERATURE=0.1
VISION_IMAGE_DETAIL=high
VISION_MAX_CANDIDATES=3
VISION_JSON_MODE=true
```

启动本地视觉适配服务：

```powershell
# Run from the repository root
uvicorn vision_adapter.main:app --host 127.0.0.1 --port 8001 --reload

# Or run from the backend directory
cd backend
uvicorn vision_adapter.main:app --host 127.0.0.1 --port 8001 --reload
```

然后把主后端的 `.env` 配成：

```env
VISION_API_URL=http://127.0.0.1:8001/recognize
VISION_API_KEY=your_local_adapter_token
VISION_API_TIMEOUT=60
```

说明：

- 主后端调用的是本地适配服务，不直接耦合某一家模型厂商
- 适配服务内部走 OpenAI 兼容协议，所以后续切换 OpenAI、阿里百炼或智谱时通常只需改 `.env.vision`
- 如果你经常不方便开 VPN，更建议优先配置国内可直连的兼容供应商

### 二、启动微信小程序前端

1. 打开微信开发者工具
2. 选择“导入项目”
3. 项目目录选择仓库根目录 `tcm-visual-query-system`
4. 按需填写或使用已有 `AppID`
5. 编译运行

### 三、配置前端请求地址

前端接口地址定义在 [utils/env.js](./utils/env.js)。

当前支持 3 套环境：

- `local`：`http://127.0.0.1:8000`
- `lan`：`http://192.168.1.100:8000`
- `prod`：占位生产地址

默认配置：

- 非发布环境默认走 `local`
- 发布环境默认走 `prod`
- 也可以通过本地缓存中的 `apiEnv` 手动覆盖

如果你在真机调试，需要注意：

- `127.0.0.1` 指向的是手机本机，而不是电脑
- 真机联调时应把 `lan` 地址改成电脑局域网 IP
- 后端服务和手机需处于同一局域网

## 项目简介

本项目是一个基于微信小程序的中医药可视化查询系统，采用“前端小程序 + FastAPI 后端 + MySQL 数据库”的前后端分离架构，围绕中药材查询、方剂查询和统计分析三个核心场景展开。

项目适合作为课程设计、毕业设计或中医药信息化方向的原型系统。当前版本已经完成基础查询与可视化能力，并预留了拍照识别入口，便于后续扩展 OCR 或图像识别功能。

## 项目亮点

- 微信小程序端提供首页、查询、分析、我的等核心页面
- 支持中药材与方剂双模式检索
- 支持详情查看，包括功效、主治、用法、来源等信息
- 后端提供统一 REST API，返回结构一致
- 首次启动后端时会自动建表并写入样例数据
- 内置统计分析接口，可直接支撑前端排行榜和分布展示
- 预留拍照识别页面，便于后续扩展智能识别能力

## 技术栈

### 前端

- 微信小程序原生开发
- WXML
- WXSS
- JavaScript

### 后端

- FastAPI
- SQLAlchemy
- PyMySQL
- Uvicorn
- MySQL

## 已实现功能

### 1. 首页

- 展示系统简介与搜索入口
- 展示药材、方剂、分类总量概览
- 提供中药查询、方剂查询、数据分析、拍照识别快捷入口
- 提供常用药材与常见方剂推荐词，点击后可直接跳转查询

### 2. 查询页

- 支持“中药材 / 方剂”两种模式切换
- 支持关键词检索
- 支持快捷标签检索
- 支持分页加载
- 支持下拉刷新
- 点击结果可进入详情页

### 3. 中药材详情页

- 展示药材名称、别名、分类
- 展示性味归经、功效、主治
- 展示用法用量、使用注意、出处来源

### 4. 方剂详情页

- 展示方剂名称、分类、组成
- 展示功效、主治、用法、出处
- 展示方剂组成药材
- 支持从方剂详情跳转到相关药材详情

### 5. 数据分析页

- 总量概览统计
- 药材功效关键词分布
- 方剂分类分布
- 方剂高频组成药材排行

当前分析页使用轻量化列表/条形展示方式实现可视化，后续可平滑升级到 ECharts 等图表组件。

### 6. 我的页

- 采用更接近日常小程序的个人中心布局
- 展示项目名称、数据规模与当前 API 地址
- 集中提供查询、分析、识别等高频入口
- 预留收藏、最近搜索、识别记录等扩展位

### 7. 拍照识别页

- 已实现图片选择/拍照交互入口
- 后端已预留视觉识别服务接入能力，配置 `VISION_API_URL` 后可调用真实视觉模型
- 未配置 `VISION_API_URL` 时会降级为按文件名匹配白名单关键词，真实拍照图片通常难以稳定识别
- 适合作为二期功能继续扩展

## 项目结构

```text
tcm-visual-query-system/
├─ app.js                         # 小程序入口
├─ app.json                       # 小程序全局配置
├─ app.wxss                       # 小程序全局样式
├─ custom-tab-bar/                # 自定义底部导航
├─ pages/                         # 页面目录
│  ├─ home/                       # 首页
│  ├─ query/                      # 查询页
│  ├─ analysis/                   # 数据分析页
│  ├─ profile/                    # 我的
│  ├─ herb-detail/                # 药材详情
│  ├─ formula-detail/             # 方剂详情
│  └─ recognition/                # 拍照识别预留页
├─ services/
│  └─ api.js                      # 前端接口封装
├─ utils/
│  ├─ env.js                      # API 环境配置
│  ├─ request.js                  # 请求封装
│  └─ tabbar.js                   # tabBar 同步逻辑
└─ backend/
   ├─ requirements.txt            # 后端依赖
   └─ app/
      ├─ main.py                  # FastAPI 入口
      ├─ api/                     # 路由层
      ├─ core/                    # 配置与统一响应
      ├─ db/                      # 数据库连接、建表、初始化数据
      └─ models/                  # ORM 模型
```

## 数据模型

项目当前包含 4 张核心业务表：

- `category`：分类表，区分药材分类和方剂分类
- `herb`：中药材表
- `formula`：方剂表
- `formula_herb_rel`：方剂与药材关联表

后端启动时会自动创建表结构，并写入一批演示样例数据。

当前样例数据规模：

- 药材分类：11 类
- 方剂分类：8 类
- 药材样例：67 条
- 方剂样例：20 条

## 后端接口概览

### 系统接口

- `GET /`：服务首页
- `GET /health`：健康检查

### 药材接口

- `GET /api/herbs`：药材列表查询
- `GET /api/herbs/{id}`：药材详情

支持参数：

- `keyword`：关键词搜索
- `categoryId`：分类筛选
- `page`：页码
- `pageSize`：每页数量

### 方剂接口

- `GET /api/formulas`：方剂列表查询
- `GET /api/formulas/{id}`：方剂详情

支持参数：

- `keyword`：关键词搜索
- `categoryId`：分类筛选
- `page`：页码
- `pageSize`：每页数量

### 统计接口

- `GET /api/statistics/overview`：总览统计
- `GET /api/statistics/herb-efficacy`：药材功效统计
- `GET /api/statistics/formula-category`：方剂分类统计
- `GET /api/statistics/formula-herb-top`：方剂高频药材排行

### 统一返回格式

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

## 开发建议

- 当前版本更偏向课程设计/演示系统，适合做功能展示和论文答辩
- 若继续完善，建议优先补充分类筛选 UI、后台管理端、单元测试和部署文档
- 拍照识别功能建议优先接入真实视觉模型，再继续补充 OCR、多图识别或第三方 AI 识别服务
- 分析页当前使用轻量可视化样式，如需更强展示效果，可接入微信小程序版图表库

## 已知说明

- 仓库中部分历史中文内容存在编码显示异常，但不影响整体结构理解和 README 编写
- `recognition` 页面已具备基础识别闭环，但未配置 `VISION_API_URL` 时仍属于文件名降级匹配，不等同于真实图像识别
- 项目当前未提供后台管理页面，样例数据主要通过后端初始化脚本写入

## 后续可扩展方向

- 增加药材/方剂分类筛选与高级检索
- 增加收藏、最近搜索、识别记录本地持久化
- 接入图片识别或 OCR 服务
- 增加后台管理功能与数据维护页面
- 增加接口测试、单元测试和部署脚本
- 接入更完整的图表组件提升可视化表现

## 适用场景

- 微信小程序课程设计
- 毕业设计项目原型
- 中医药信息查询系统演示
- 中医药数据可视化方向的教学/展示项目

## 许可证

仓库当前未提供明确许可证文件。如需开源分发，建议补充 `LICENSE`。
