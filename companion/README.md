# Optional local AI cutout

The main app works without this service. To enable AI background removal, install and start this companion yourself on the same computer as your browser. It binds only to `127.0.0.1:4174`; pictures remain local. The default lightweight U2NetP model completed a synthetic 768px example in 0.76 seconds here; real images and computers vary. Optional BiRefNet can require much more time and RAM. It is a foreground process; Ctrl+C stops it. No login, API key, cloud upload, telemetry, startup service or automatic model download.

Requires Python 3.11–3.13, approximately 4.6 MB for the default U2NetP weights (optional BiRefNet: 224 MB), space for Python dependencies, and available RAM for inference (BiRefNet requires substantially more). CPU-only ONNX Runtime is used. This is not a hosted/public API.

## Explicit setup

From this directory on macOS/Linux:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python setup_model.py
python server.py
```

Windows: use `py -m venv .venv`, then `.venv\Scripts\activate`, then the same `python` commands. The model downloader contacts the rembg GitHub release only for weights; it sends no pictures. It verifies size and pinned SHA-256. If verification fails, it refuses the file.

In a separate terminal, serve the app from its root with `python3 -m http.server 4173 --bind 127.0.0.1`, then visit `http://127.0.0.1:4173`. The service accepts exactly this origin or `http://localhost:4173`. File URLs and arbitrary websites cannot access it. Do not proxy it publicly or broaden its origins.

## Protocol

- `GET /api/health` returns `{ "ready": true/false, "model": "u2netp" }`. `ready` indicates model file presence, not a completed inference/warmup. The first request checks its SHA-256 and loads it.
- `POST /api/remove-background`: multipart field `image`; JPEG/PNG/WebP; exactly one non-animated image; max 15 MiB request and 24 million pixels. Returns transparent `image/png` at EXIF-corrected original dimensions.
- Browser requests must include `X-Seller-Frame: local`. Exact Origin, Host and preflight checks prevent other websites issuing simple form requests. This is browser cross-origin protection, not authentication against malicious software already on your computer.
- One inference at a time. 429 `busy` means wait for your first request. 503 `model_not_installed` means run explicit setup. 503 `inference_failed` means model verification/loading/inference failed (check installation and memory). 400/415 mean malformed or unsupported input; 413 means too large; 403 means invalid client/host/origin.
- No images are saved by the service. Output drops metadata and multiplies the model mask by existing alpha. Inspect fine edges before selling/publishing: transparent objects, hair, wires and shadows can be imperfect.

## Model selection

Default setup downloads **U2NetP**, 4.57 MB, for broad CPU availability. It is a coarse salient-object model: inspect edges; it is not equivalent to studio retouching.

BiRefNet-General-Lite is an optional larger alternative, not required:

```sh
python setup_model.py --model birefnet-general-lite
SELLER_FRAME_MODEL_NAME=birefnet-general-lite python server.py
```

On PowerShell, set `$env:SELLER_FRAME_MODEL_NAME="birefnet-general-lite"` before `python server.py`. Unset that variable to return to U2NetP. The runtime never downloads either model. `SELLER_FRAME_MODEL` optionally overrides the model file path but its bytes must still match the selected model's pinned hash.

## Model provenance and licenses

### Default U2NetP

- Original authors' repository: https://github.com/xuebinqin/U-2-Net — Apache-2.0 project license, bundled in `licenses/U-2-Net-LICENSE.txt`.
- Original README distributes pretrained U2NetP weights: https://github.com/xuebinqin/U-2-Net#usage-for-salient-object-detection.
- ONNX conversion distributed by official rembg release: https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx.
- Reviewed rembg session: https://github.com/danielgatis/rembg/blob/cd8f3665dda6c246b5baecb85fda6a2acd644c2a/rembg/sessions/u2netp.py.
- Size: 4574861 bytes. SHA-256: `309c8469258dda742793dce0ebea8e6dd393174f89934733ecc8b14c76f4ddd8`.
- Upstream rembg MD5 matched: `8e83ca70e441ab06c318d82300c84806`.

The original repository's Apache-2.0 license is the upstream licensing basis; no separate restrictive weight license was found in its published README. The ONNX file is rembg's conversion, not claimed byte-identical to the original PyTorch file. Repository licensing is not an independent warranty of training-data rights.

### Optional BiRefNet-General-Lite

Optional model: **BiRefNet-General-Lite**, ONNX export maintained by rembg, fixed release asset `BiRefNet-general-bb_swin_v1_tiny-epoch_232.onnx`.

- Upstream code: https://github.com/ZhengPeng7/BiRefNet (MIT, copyright 2024 ZhengPeng)
- Official light model card: https://huggingface.co/ZhengPeng7/BiRefNet_lite/tree/aa62cd87eafb9cc43056d08ef3615a14628b831d (declares MIT)
- ONNX distributor: https://github.com/danielgatis/rembg/releases/tag/v0.0.0
- Reviewed loader/preprocessing reference: https://github.com/danielgatis/rembg/tree/cd8f3665dda6c246b5baecb85fda6a2acd644c2a/rembg/sessions
- Asset size: 224005088 bytes
- SHA-256: `5600024376f572a557870a5eb0afb1e5961636bef4e1e22132025467d0f03333`
- Upstream rembg loader MD5: `4fab47adc4ff364be1713e97b7e66334`; independently matched downloaded bytes during development.

The ONNX release is a third-party conversion associated by rembg with the upstream project; it is not claimed byte-identical to the Hugging Face PyTorch weights. Pinned bytes are used rather than mutable latest downloads. This service executes our small reviewed preprocessing code plus PyPI ONNX Runtime, not downloaded model-repository Python. It never uses `trust_remote_code`, pickle, or rembg's default model. BRIA/RMBG noncommercial weights are not used.

Bundled upstream notices are in `licenses/`. Python dependencies retain their own licenses. Model weights are not bundled in the source ZIP. Model license metadata is not a warranty of training-data rights or result suitability.

## Checks

```sh
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
```

Contract tests stub inference and do not demonstrate model quality. See `validation.md` for the actual execution result and limitations.
