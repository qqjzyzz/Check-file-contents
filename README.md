# 文本重复率检测系统

这是一个基于向量相似度的文本重复率检测系统，可以帮助用户快速识别Excel文件中的相似文本内容。系统使用了先进的自然语言处理技术和向量搜索引擎，能够高效地发现文本之间的相似度。

## 功能特点

- 支持Excel文件(.xlsx, .xls)的文本内容分析
- 使用OpenAI的文本嵌入模型进行文本向量化
- 采用Milvus向量数据库进行高效的相似度搜索
- 提供文本预过滤功能，提高处理效率
- 可调节的相似度阈值设置
- 生成详细的相似度报告
- 友好的Web界面，支持文件上传和结果展示
- 支持多种相似度报告导出选项（70%、80%、90%及全部结果）

## 系统要求

- Python 3.8+
- Milvus 2.0+
- OpenAI API访问权限

## 安装说明

1. 克隆项目到本地：
```bash
git clone [项目地址]
cd repeat-rate
```

2. 安装依赖包：
```bash
pip install -r requirements.txt
```

3. 配置环境变量：
创建`.env`文件并设置以下参数：
```
OPENAI_API_KEY=your_api_key
OPENAI_API_BASE=your_api_base_url
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

## 使用方法

1. 启动Milvus服务器（确保Milvus已正确安装和配置）

2. 运行Flask应用：
```bash
python app.py
```

3. 在浏览器中访问：`http://localhost:5000`

4. 使用步骤：
   - 上传Excel文件（确保包含文本列）
   - 设置文本列名和相似度阈值
   - 点击开始分析
   - 查看分析结果并下载报告

## 注意事项

- 确保Excel文件中包含要分析的文本列
- 建议根据数据量适当调整相似度阈值
- 大文件处理可能需要较长时间，请耐心等待
- 定期检查和更新API密钥

## 技术架构

- 前端：HTML, CSS, JavaScript
- 后端：Flask (Python)
- 向量数据库：Milvus
- 文本向量化：OpenAI API
- 数据处理：Pandas #   C h e c k - f i l e - c o n t e n t s  
 "# Check-file-contents" 
"# Check-file-contents" 
"# Check-file-contents" 
