import datetime
import logging
import os
import sys
from comfy_api_simplified import ComfyApiWrapper, ComfyWorkflowWrapper

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

api = ComfyApiWrapper("http://127.0.0.1:8188/")

wf = ComfyWorkflowWrapper("workflows/z_image_turbo.json")

sizes = [
    # (1024, 1024, "1024x1024"),
    # (1280, 832, "1280x832"),
    (832, 1280, "832x1280"),
]

base_results_folder = "results/z_image_turbo/"

for _, _, folder_name in sizes:
    os.makedirs(os.path.join(base_results_folder, folder_name), exist_ok=True)

prompts = [
    "Photorealistic, ultra-detailed close-up portrait of a character with long flowing pink hair, wearing round red-tinted sunglasses with gold rims, lifting them slightly with one hand; adorned with a blue rose hair accessory with a black ribbon and a black choker with a heart-shaped turquoise pendant; background features soft glowing hearts and abstract radiant streaks in pastel pink, blue, and gold; bright vibrant lighting with sparkling highlights, 50mm feel, f/1.8, shallow depth of field; emphasize glossy hair strands, reflective lens surfaces, smooth skin texture, and intricate jewelry details; anime-inspired editorial style with playful and dreamy mood."
]

for prompt in prompts:
    wf.set_node_param("CLIP Text Encode (Positive Prompt)", "text", prompt)

    # Generate one image for each target size and save to the corresponding folder
    for width, height, folder_name in sizes:
        wf.set_node_param("EmptySD3LatentImage", "height", height)
        wf.set_node_param("EmptySD3LatentImage", "width", width)

        for i in range(1):
            wf.set_node_param("KSampler", "seed", 77 + i * 1000000)

            results = api.queue_and_wait_images(wf, output_node_title="Save Image")
            for filename, image_data in results.items():
                out_dir = os.path.join(base_results_folder, folder_name)
                out_path = os.path.join(out_dir, f"{datetime.datetime.now().timestamp()}.png")
                with open(out_path, "wb+") as f:
                    f.write(image_data)
