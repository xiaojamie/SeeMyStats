# SeeMyStats - apple watch数据分析平台 

#注意
此项目不再维护
不支持英文


## ✨ 核心特色

### 🔬 技术分析创新
- **移动平均线分析**：7日、14日、30日SMA识别健康趋势
- **相对强弱指数(RSI)**：检测健康指标的异常波动
- **布林带分析**：基于标准差识别数据异常区间
- **平均真实范围(ATR)**：量化健康数据的波动性

### 📈 交互式可视化
- **框选工具(Box Select)**：精确选择数据区间进行分析
- **自由套索选择**：任意形状的数据点选择
- **多层次缩放**：从宏观趋势到微观细节

### 🧠 智能数据分析
- **多维相关性分析**：发现不同健康指标间的关联
- **统计显著性检验**：科学验证数据关联性

## 🚀 功能模块

### 📊 仪表板系统
- 实时健康数据概览
- 多指标综合展示
- 趋势变化预警

### 📱 数据管理
- Apple Health XML数据导入
- 多格式数据支持
- 数据清洗与预处理

## 🛠️ 技术架构

### 后端技术栈
```
Flask 2.3.3          # Web框架
Pandas 2.0.3         # 数据处理
NumPy 1.24.3         # 数值计算
Matplotlib 3.7.2     # 基础绘图
Plotly 5.16.1        # 交互式可视化
```

### 前端技术
```
Bootstrap 5          # 响应式UI框架
Plotly.js           # 交互式图表
JavaScript ES6+      # 现代前端交互
```

### 数据处理
```
XMLtoDict 0.13.0     # XML解析
BeautifulSoup 4.12.2 # HTML/XML处理
LXML 4.9.3          # 高性能XML处理
```

## 📦 快速开始

### 环境要求
- Python 3.8+
- 8GB+ RAM (推荐)
- 现代浏览器支持

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/yourusername/healthweb.git
cd healthweb
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **启动应用**
```bash
python run.py
```

5. **访问应用**
```
打开浏览器访问: http://localhost:5000
```

## 📋 使用指南

### 数据导入流程

1. **导出Apple健康数据**
   - 打开iPhone健康应用
   - 点击右上角头像
   - 选择"导出所有健康数据"
   - 等待导出完成并分享文件

2. **上传数据**
   - 在HealthWeb中点击"上传数据"
   - 选择导出的ZIP文件或解压后的export.xml
   - 等待数据解析完成

3. **开始分析**
   - 访问仪表板查看数据概览
   - 使用分析页面进行深度分析
   - 利用技术指标发现健康模式

## 📊 支持的数据类型

### 生理指标
- ❤️ 心率 & 心率变异性
- 🌡️ 体温

### 活动数据
- 👟 步数 & 距离

### 睡眠健康
- 😴 睡眠时长




## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- Apple Health团队提供的健康数据标准
- Plotly团队的优秀可视化库
- Flask社区的Web框架支持
- 所有贡献者和用户的支持

---
