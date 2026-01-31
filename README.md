# Run ComfyUI Workflow

本项目旨在通过 Python 脚本方便地调用和运行 ComfyUI 工作流。它提供了一个简化的 API 包装器，允许用户加载 ComfyUI 的 API 格式工作流，动态修改参数（如提示词、种子、图像尺寸等），并获取生成结果。

> **说明**：本项目为了方便使用，直接集成了 [comfy_api_simplified](https://github.com/deimos-deimos/comfy_api_simplified) 的核心代码。感谢原作者 [deimos-deimos](https://github.com/deimos-deimos) 以及所有贡献者（本项目作者也曾参与贡献了该项目的部分代码）。

## 目录结构

- `comfy_api_simplified/`: 核心 API 包装库。
- `workflows/`: 存放 ComfyUI 导出的 API 格式工作流文件（.json）。
- `run/`: 存放运行脚本，用于加载工作流并执行任务。
- `results/`: 默认的结果输出目录。

## 快速开始

### 1. 环境准备

确保你已经安装了 Python 3.x。建议使用虚拟环境。

```bash
# Windows
.\.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate
```

### 2. 安装依赖

本项目包含一个 `pyproject.toml` 文件，你可以直接安装本项目及其依赖：

```bash
pip install -e .
```

或者手动安装所需的第三方库：

```bash
pip install requests websockets
```

### 3. 准备工作流

1. 打开 ComfyUI 网页界面。
2. 搭建好你的工作流。
3. 点击设置（齿轮图标），勾选 **"Enable Dev mode Options"**。
4. 点击菜单栏的 **"Save (API Format)"** 按钮，将工作流保存为 JSON 文件。
5. 将保存的 JSON 文件放置在 `workflows/` 目录下。

### 4. 编写运行脚本

你可以复制 `run/get_zimage.py` 作为模板，并根据你的需求进行修改。

**示例脚本解析 (`run/get_zimage.py`)：**

```python
import datetime
import os
from comfy_api_simplified import ComfyApiWrapper, ComfyWorkflowWrapper

# 初始化 API 连接，确保 ComfyUI 已在运行
api = ComfyApiWrapper("http://127.0.0.1:8188/")

# 加载工作流文件
wf = ComfyWorkflowWrapper("workflows/z_image_turbo.json")

# 定义要生成的参数配置（例如尺寸）
sizes = [
    (832, 1280, "832x1280"),
]

base_results_folder = "results/z_image_turbo/"

# 动态修改参数并运行
for width, height, folder_name in sizes:
    # 修改节点参数：根据节点的 title 修改
    wf.set_node_param("EmptySD3LatentImage", "height", height)
    wf.set_node_param("EmptySD3LatentImage", "width", width)
    
    # 修改提示词
    wf.set_node_param("CLIP Text Encode (Positive Prompt)", "text", "Your prompt here...")

    # 修改种子（可选）
    wf.set_node_param("KSampler", "seed", 123456789)

    # 提交任务并等待结果
    # output_node_title 对应工作流中保存图片的节点标题
    results = api.queue_and_wait_images(wf, output_node_title="Save Image")

    # 保存结果
    for filename, image_data in results.items():
        out_dir = os.path.join(base_results_folder, folder_name)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"{datetime.datetime.now().timestamp()}.png")
        with open(out_path, "wb+") as f:
            f.write(image_data)
```

### 5. 运行脚本

确保 ComfyUI 正在运行（通常在 `http://127.0.0.1:8188/`），然后执行你的脚本：

```bash
python run/your_script.py
```

## 🖥️ Web 界面 (Gradio)

本项目提供了一个可视化的 Web 界面，无需编写代码即可运行和调试工作流。

### 启动方式

确保已安装 `gradio` 和 `pillow`（运行 `pip install -e .` 即可），然后执行：

```bash
python run/web_ui.py
```

界面将在 **http://127.0.0.1:7878** 启动。

### 功能特性

1.  **工作流管理**：
    *   自动读取 `workflows/` 目录下的所有 JSON 文件。
    *   支持直接上传新的 API 格式 JSON 文件（上传后自动保存）。
2.  **动态参数修改**：
    *   无需修改代码，在界面上通过下拉菜单选择任意节点 (Node) 和参数 (Input)。
    *   输入新值后点击 "添加/更新修改"，即可覆盖原工作流参数。
    *   支持添加多个修改项，所有修改会在生图时统一应用。
3.  **批量生成**：
    *   设置 "运行次数 (Batch Count)"，可一次性循环执行多次任务。
4.  **结果预览**：
    *   生成的图片会实时展示在界面的画廊中，并自动保存到 `results/web_ui/` 目录。

## 常用功能

- **修改节点参数**：使用 `wf.set_node_param(node_title, param_name, value)`。
  - `node_title`: 对应 ComfyUI 中节点的标题（Title）。
  - `param_name`: 对应节点输入的参数名（如 `text`, `seed`, `width`, `height` 等）。
  - `value`: 要设置的新值。

- **提交任务**：使用 `api.queue_and_wait_images(wf, output_node_title="Save Image")`。
  - 会阻塞直到图片生成完成并返回图片数据。

## 注意事项

- 导出的工作流必须是 **API Format**，而不是普通的 Save。
- 脚本中的节点标题（如 "KSampler", "Save Image"）必须与 ComfyUI 中的节点标题完全一致。如果修改了节点标题，脚本中也需同步修改。
