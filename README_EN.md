# Run ComfyUI Workflow

![Run ComfyUI Workflow](assets/github封面-英文.png)

[中文](README.md) | [English](README_EN.md)

This project aims to easily call and run ComfyUI workflows via Python scripts. It provides a simplified API wrapper that allows users to load ComfyUI API-format workflows, dynamically modify parameters (such as prompts, seeds, image dimensions, etc.), and retrieve generation results.

> **Note**: This project directly integrates the core code of [comfy_api_simplified](https://github.com/deimos-deimos/comfy_api_simplified) for convenience and includes some modifications. Thanks to the original author [deimos-deimos](https://github.com/deimos-deimos) and all contributors (the author of this project also contributed to the original repository).

## Directory Structure

- `comfy_api_simplified/`: Core API wrapper library.
- `workflows/`: Stores ComfyUI exported API-format workflow files (.json).
- `run/`: Stores running scripts for loading workflows and executing tasks.
- `cmd/`: Stores command-line tools and Web UI startup scripts.
- `results/`: Default output directory for results.

## 🚀 Quick Start

### 1. Environment Preparation

Ensure you have Python 3.x installed. Using a virtual environment is recommended.

```bash
# Windows
.\.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate
```

### 2. Install Dependencies

This project includes a `pyproject.toml` file. You can install the project and its dependencies directly:

```bash
pip install -e .
```

Or manually install the required third-party libraries:

```bash
pip install requests websockets gradio pillow
```

## 📖 Usage

### Method 1: Run via Python Code

Suitable for developers who need flexible logic for batch generation or automated testing.

#### 1. Export API Workflow

1. Open the ComfyUI web interface.
2. Click Settings (gear icon) and check **"Enable Dev mode Options"**.
3. Click the **"Save (API Format)"** button in the menu bar to save the workflow as a JSON file.

![Export Workflow](assets/export_workflow.png)

#### 2. Place Workflow File

Place the exported JSON file into the `workflows/` directory of the project.

![Place Workflow](assets/place_workflow.png)

#### 3. Write Running Script

Create a new Python script referencing `run/get_zimage.py`.

```python
from comfy_api_simplified import ComfyApiWrapper, ComfyWorkflowWrapper

api = ComfyApiWrapper("http://127.0.0.1:8188/")
wf = ComfyWorkflowWrapper("workflows/your_workflow.json")

# Modify parameters
wf.set_node_param("KSampler", "seed", 12345)

# Run and save
results = api.queue_and_wait_images(wf, output_node_title="Save Image")
# ... save logic ...
```

#### 4. Run and Check Results

Run the script in the terminal:

```bash
python run/your_script.py
```

Results will be saved in the `results/` directory.

![Run Python](assets/run_python.png)
![Check Result](assets/check_result.png)

---

### Method 2: Web Interface (Gradio)

Run and debug workflows directly through a visual interface without writing code.

#### 1. Start Web UI

Execute the following command to start the interface:

```bash
python cmd/web_ui.py
```

The interface will start at **http://127.0.0.1:7878**.

![Start Gradio](assets/start_gradio.png)

#### 2. Set Parameters and Run

1. **Select Workflow**: Select from the dropdown menu or upload a new JSON file.
2. **Load Parameters**: Click the "Load" button to read workflow node information.
3. **Modify Parameters**: Select a node and parameter, enter a new value, and click "Add/Update Override".
4. **Start Generation**: Set the batch count and click "Generate". Results will be displayed in real-time in the gallery on the right.

![Gradio Exec](assets/gradio_exec.png)

## Common Functions

- **Modify Node Parameter**: Use `wf.set_node_param(node_title, param_name, value)`.
- **Submit Task**: Use `api.queue_and_wait_images(wf, output_node_title="Save Image")`.

## Notes

- The exported workflow must be in **API Format**, not the standard Save format.
- Node titles in the script (e.g., "KSampler", "Save Image") must match the node titles in ComfyUI exactly.
