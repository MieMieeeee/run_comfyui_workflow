import gradio as gr
import os
import io
import json
import glob
import logging
import PIL.Image
from typing import List, Dict, Tuple, Any
from comfy_api_simplified import ComfyApiWrapper, ComfyWorkflowWrapper

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ComfyUI-WebUI")

# 配置
WORKFLOWS_DIR = "workflows"
OUTPUT_DIR = "results/web_ui"
DEFAULT_COMFY_URL = "http://127.0.0.1:8188/"

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_available_workflows():
    """获取所有可用的工作流文件列表"""
    files = glob.glob(os.path.join(WORKFLOWS_DIR, "*.json"))
    return [os.path.basename(f) for f in files]

def load_workflow_nodes(workflow_filename):
    """加载工作流并返回所有节点标题"""
    if not workflow_filename:
        return [], None
    
    path = os.path.join(WORKFLOWS_DIR, workflow_filename)
    try:
        wf = ComfyWorkflowWrapper(path)
        # 获取所有节点标题并去重
        node_titles = sorted(list(set(wf.list_nodes())))
        return node_titles, wf
    except Exception as e:
        logger.error(f"Failed to load workflow {workflow_filename}: {e}")
        return [], None

def get_node_inputs(workflow_filename, node_title):
    """获取指定节点的可用输入参数"""
    if not workflow_filename or not node_title:
        return []
    
    path = os.path.join(WORKFLOWS_DIR, workflow_filename)
    try:
        wf = ComfyWorkflowWrapper(path)
        # 找到对应节点
        for node in wf.values():
            if node.get("_meta", {}).get("title") == node_title:
                inputs = node.get("inputs", {})
                return list(inputs.keys())
        return []
    except Exception as e:
        logger.error(f"Failed to get inputs for node {node_title}: {e}")
        return []

def handle_upload_file(file_obj):
    """处理上传的工作流文件"""
    if file_obj is None:
        return gr.update()
    
    # 获取文件名
    filename = os.path.basename(file_obj.name)
    target_path = os.path.join(WORKFLOWS_DIR, filename)
    
    # 复制文件到 workflows 目录
    import shutil
    shutil.copy(file_obj.name, target_path)
    
    # 刷新下拉列表
    new_choices = get_available_workflows()
    return gr.update(choices=new_choices, value=filename)

def add_parameter_override(node, param, value, current_list):
    """添加新的参数修改项"""
    if not node or not param:
        return current_list
    
    # Check if current_list is a pandas DataFrame and convert to list
    if hasattr(current_list, 'values'):
        current_list = current_list.values.tolist()
    elif current_list is None:
        current_list = []
        
    # 检查是否已存在，如果存在则更新
    new_entry = [node, param, value]
    
    # current_list 是一个列表的列表 [[node, param, value], ...]
    updated_list = []
    found = False
    if current_list:
        for item in current_list:
            if item[0] == node and item[1] == param:
                updated_list.append(new_entry)
                found = True
            else:
                updated_list.append(item)
    
    if not found:
        updated_list.append(new_entry)
        
    return updated_list

def generate_images(workflow_filename, overrides, batch_count, comfy_url):
    """执行生图任务"""
    if not workflow_filename:
        raise gr.Error("请先选择一个工作流")
    
    try:
        api = ComfyApiWrapper(comfy_url)
    except Exception as e:
        raise gr.Error(f"无法连接到 ComfyUI ({comfy_url}): {e}")

    workflow_path = os.path.join(WORKFLOWS_DIR, workflow_filename)
    all_images = []

    try:
        # 每次生成都重新加载工作流，确保状态重置
        wf = ComfyWorkflowWrapper(workflow_path)

        # 应用所有参数修改
        if overrides is not None and len(overrides) > 0:
            # Dataframe returns a pandas DataFrame or list depending on Gradio version/config
            # But here based on user error "The truth value of a DataFrame is ambiguous", 
            # overrides is likely a DataFrame. We should convert it to list of lists.
            
            # If it's a pandas DataFrame
            if hasattr(overrides, 'values'):
                overrides_list = overrides.values.tolist()
            else:
                overrides_list = overrides

            for item in overrides_list:
                # Ensure item has enough elements
                if len(item) < 3:
                    continue
                    
                node_title, param_name, value = item[0], item[1], item[2]
                
                # 尝试转换数字类型
                try:
                    if value.isdigit():
                        value = int(value)
                    elif value.replace('.', '', 1).isdigit():
                        value = float(value)
                except:
                    pass
                
                try:
                    wf.set_node_param(node_title, param_name, value)
                    logger.info(f"Applied override: {node_title}.{param_name} = {value}")
                except Exception as e:
                    logger.warning(f"Failed to set param {node_title}.{param_name}: {e}")

        # 批量执行
        for i in range(int(batch_count)):
            logger.info(f"Executing batch {i+1}/{batch_count}")
            
            # 如果是多次运行，也许可以改变 seed？
            # 这里简单起见，不自动改 seed，除非用户在参数列表里自己指定了逻辑
            # 但通常用户希望每次不一样，所以我们可以检查是否需要自动增加 seed
            # 暂时保持简单，完全由用户控制
            
            results = api.queue_and_wait_images(wf, output_node_title="Save Image")
            
            for filename, image_data in results.items():
                img = PIL.Image.open(io.BytesIO(image_data))
                all_images.append(img)
                
                # 保存到本地 results 目录备份
                save_path = os.path.join(OUTPUT_DIR, f"{filename}")
                with open(save_path, "wb+") as f:
                    f.write(image_data)

        return all_images

    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise gr.Error(f"生成失败: {str(e)}")

# 构建界面
with gr.Blocks(title="ComfyUI Web Interface", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎨 ComfyUI Web Interface")
    
    with gr.Row():
        with gr.Column(scale=1):
            # --- 工作流选择区 ---
            gr.Markdown("### 1. 工作流设置")
            with gr.Row():
                workflow_dropdown = gr.Dropdown(
                    label="选择工作流 (Select Workflow)", 
                    choices=get_available_workflows(),
                    interactive=True,
                    scale=4
                )
                refresh_btn = gr.Button("🔄", size="sm", scale=0)
                load_workflow_btn = gr.Button("📂 加载", size="sm", scale=0, variant="secondary")
            
            with gr.Accordion("上传新工作流 (Upload JSON)", open=False):
                upload_file = gr.File(label="拖拽或点击上传", file_types=[".json"])
            
            # --- 参数修改区 ---
            gr.Markdown("### 2. 动态参数修改 (Parameter Overrides)")
            with gr.Group():
                with gr.Row():
                    node_dropdown = gr.Dropdown(label="选择节点 (Node)", choices=[], interactive=True)
                    param_dropdown = gr.Dropdown(label="选择参数 (Input)", choices=[], interactive=True)
                
                value_input = gr.Textbox(label="新值 (Value)", placeholder="输入新的参数值...")
                add_param_btn = gr.Button("添加/更新修改 (Add Override)")
            
            # 修改列表展示
            overrides_dataframe = gr.Dataframe(
                headers=["Node Title", "Input Name", "Value"],
                datatype=["str", "str", "str"],
                label="已应用的修改列表 (Applied Overrides)",
                interactive=False,
                col_count=(3, "fixed"),
                value=[]
            )
            
            clear_params_btn = gr.Button("清空修改列表 (Clear All)", variant="secondary")

            # --- 执行控制区 ---
            gr.Markdown("### 3. 执行控制 (Execution)")
            comfy_url_input = gr.Textbox(label="ComfyUI URL", value=DEFAULT_COMFY_URL)
            batch_count_input = gr.Number(label="运行次数 (Batch Count)", value=1, precision=0, minimum=1)
            
            generate_btn = gr.Button("🚀 开始生成 (Generate)", variant="primary", size="lg")

        with gr.Column(scale=2):
            # --- 结果展示区 ---
            gr.Markdown("### 4. 生成结果 (Results)")
            result_gallery = gr.Gallery(
                label="生成的图片", 
                show_label=False, 
                elem_id="gallery", 
                columns=[2], 
                rows=[2], 
                object_fit="contain", 
                height="100vh"
            )

    # --- 事件绑定 ---
    
    # 刷新工作流列表
    def refresh_workflows():
        return gr.update(choices=get_available_workflows())
    
    refresh_btn.click(refresh_workflows, outputs=workflow_dropdown)

    # 上传文件
    upload_file.upload(handle_upload_file, inputs=upload_file, outputs=workflow_dropdown)

    # 点击“加载”按钮后，才更新节点列表（虽然 Dropdown change 也会触发，但显式加载更符合直觉）
    def on_load_workflow(wf_name):
        if not wf_name:
            return gr.update(choices=[], value=None), gr.update(choices=[], value=None)
        nodes, _ = load_workflow_nodes(wf_name)
        return gr.update(choices=nodes, value=None), gr.update(choices=[], value=None)

    load_workflow_btn.click(on_load_workflow, inputs=workflow_dropdown, outputs=[node_dropdown, param_dropdown])

    # 保持原来的 Dropdown change 事件，方便快速切换，如果不想要自动加载，可以注释掉下面这行
    # workflow_dropdown.change(on_workflow_select, inputs=workflow_dropdown, outputs=[node_dropdown, param_dropdown])

    # 选择节点后，更新参数列表
    def on_node_select(wf_name, node_title):
        inputs = get_node_inputs(wf_name, node_title)
        return gr.update(choices=inputs, value=None)

    node_dropdown.change(on_node_select, inputs=[workflow_dropdown, node_dropdown], outputs=param_dropdown)

    # 添加参数修改
    add_param_btn.click(
        add_parameter_override,
        inputs=[node_dropdown, param_dropdown, value_input, overrides_dataframe],
        outputs=overrides_dataframe
    )

    # 清空修改
    clear_params_btn.click(lambda: [], outputs=overrides_dataframe)

    # 执行生成
    generate_btn.click(
        generate_images,
        inputs=[workflow_dropdown, overrides_dataframe, batch_count_input, comfy_url_input],
        outputs=result_gallery
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7878)
