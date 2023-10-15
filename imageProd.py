import requests
import json
apikey='weppFbVWLCpW5kcuWEXuY7dC1brpdNMftAbnYXrvMEdTFPGFxzpwtxfZ5TDL'
url = "https://stablediffusionapi.com/api/v3/text2img"

def generateImageForResponse(chatgpt_output_text) -> str:
    payload = json.dumps({
    "key": apikey,
    "prompt":"Create a clean simple image and include no text" + chatgpt_output_text,
    "negative_prompt": None,
    "init_image": "Verizon_promo_code.png",
    "width": "512",
    "height": "512",
    "samples": "1",
    "num_inference_steps": "20",
    "seed": None,
    "guidance_scale": 7.5,
    "safety_checker": "yes",
    "multi_lingual": "no",
    "panorama": "no",
    "self_attention": "no",
    "upscale": "no",
    "embeddings_model": None,
    "webhook": None,
    "track_id": None
    })

    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.text)

    return response.json()['output'][0] if len(response.json()['output']) > 0 else ""