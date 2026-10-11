"""Optional loopback-only, offline background-removal companion. No runtime downloads."""
import io
import hashlib
import os
import threading
import warnings
from pathlib import Path

import numpy as np
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from PIL import Image, ImageOps, UnidentifiedImageError
from starlette.formparsers import MultiPartParser
from models_config import MODELS

ROOT = Path(__file__).resolve().parent
MODEL_NAME = os.environ.get('SELLER_FRAME_MODEL_NAME', 'u2netp')
CONFIG = MODELS[MODEL_NAME]
MODEL = Path(os.environ.get('SELLER_FRAME_MODEL', ROOT / 'models' / f'{MODEL_NAME}.onnx'))
ORIGINS = {'http://127.0.0.1:4173', 'http://localhost:4173'}
MAX_BODY = 15 * 1024 * 1024
MAX_PIXELS = 24_000_000
Image.MAX_IMAGE_PIXELS = MAX_PIXELS
LOCK = threading.Lock()
_session = None

class MemoryMultipartParser(MultiPartParser):
    # Entire HTTP body is already bounded; avoid writing photo uploads to disk.
    spool_max_size = MAX_BODY + 1
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

def fail(code, message):
    return JSONResponse({'error': message}, status_code=code)

@app.middleware('http')
async def boundary(request, call_next):
    if request.headers.get('host') not in {'127.0.0.1:4174', 'localhost:4174'}:
        return fail(403, 'invalid_host')
    origin = request.headers.get('origin')
    if origin is not None and origin not in ORIGINS:
        return fail(403, 'origin_not_allowed')
    headers = {'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'}
    if origin in ORIGINS:
        headers.update({'Access-Control-Allow-Origin': origin, 'Vary': 'Origin'})
    if request.method == 'OPTIONS':
        if origin not in ORIGINS:
            return fail(403, 'origin_required')
        headers.update({'Access-Control-Allow-Methods': 'GET, POST', 'Access-Control-Allow-Headers': 'X-Seller-Frame, Content-Type'})
        return Response(status_code=204, headers=headers)
    if request.method == 'POST':
        if origin not in ORIGINS or request.headers.get('x-seller-frame') != 'local':
            return fail(403, 'local_client_required')
        try:
            if int(request.headers.get('content-length', '0')) > MAX_BODY:
                return fail(413, 'upload_too_large')
        except ValueError:
            return fail(400, 'invalid_content_length')
    response = await call_next(request)
    response.headers.update(headers)
    return response

@app.get('/api/health')
def health():
    return {'ready': MODEL.is_file(), 'model': MODEL_NAME}

def decode_image(data):
    with warnings.catch_warnings():
        warnings.simplefilter('error', Image.DecompressionBombWarning)
        with Image.open(io.BytesIO(data)) as source:
            if source.format not in {'JPEG', 'PNG', 'WEBP'}:
                raise ValueError('unsupported_image')
            if source.width * source.height > MAX_PIXELS or source.width < 2 or source.height < 2:
                raise ValueError('invalid_dimensions')
            if getattr(source, 'n_frames', 1) != 1:
                raise ValueError('animated_image_not_supported')
            source.load()
            result = ImageOps.exif_transpose(source).convert('RGBA')
            result.info.clear()
            return result

def infer(image):
    global _session
    if _session is None:
        with MODEL.open('rb') as model_file:
            if hashlib.file_digest(model_file, 'sha256').hexdigest() != CONFIG['sha256']:
                raise RuntimeError('Unverified model')
        import onnxruntime as ort
        options = ort.SessionOptions()
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1
        options.enable_cpu_mem_arena = False
        options.enable_mem_pattern = False
        options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_BASIC
        _session = ort.InferenceSession(str(MODEL), sess_options=options, providers=['CPUExecutionProvider'])
    # Model-specific fixed square input; ImageNet normalization.
    rgb = image.convert('RGB').resize((CONFIG['resolution'], CONFIG['resolution']), Image.Resampling.LANCZOS)
    array = np.asarray(rgb, dtype=np.float32)
    array /= max(float(array.max()), 1e-6) if MODEL_NAME == 'u2netp' else 255.0
    array = (array - np.array([0.485, 0.456, 0.406], dtype=np.float32)) / np.array([0.229, 0.224, 0.225], dtype=np.float32)
    tensor = array.transpose(2, 0, 1)[None].astype(np.float32)
    logits = _session.run(None, {_session.get_inputs()[0].name: tensor})[0]
    alpha = logits[0, 0] if MODEL_NAME == 'u2netp' else 1.0 / (1.0 + np.exp(-np.clip(logits[0, 0], -80, 80)))
    low, high = float(alpha.min()), float(alpha.max())
    if high - low > 1e-6:
        alpha = (alpha - low) / (high - low)
    mask = Image.fromarray(np.uint8(np.clip(alpha, 0, 1) * 255)).resize(image.size, Image.Resampling.LANCZOS)
    # Never resurrect pixels the source already made transparent.
    original_alpha = np.asarray(image.getchannel('A'), dtype=np.uint16)
    mask = Image.fromarray(((np.asarray(mask, dtype=np.uint16) * original_alpha) // 255).astype(np.uint8))
    image.putalpha(mask)
    result = io.BytesIO()
    image.save(result, format='PNG')
    return result.getvalue()

@app.post('/api/remove-background')
async def remove_background(request: Request):
    if not MODEL.is_file():
        return fail(503, 'model_not_installed')
    if not request.headers.get('content-type', '').lower().startswith('multipart/form-data;'):
        return fail(415, 'multipart_required')
    if not LOCK.acquire(blocking=False):
        return fail(429, 'busy')
    try:
        # Read a bounded body even if Content-Length is absent or dishonest.
        chunks, total = [], 0
        async for chunk in request.stream():
            total += len(chunk)
            if total > MAX_BODY:
                return fail(413, 'upload_too_large')
            chunks.append(chunk)
        request._body = b''.join(chunks)
        try:
            form = await MemoryMultipartParser(request.headers, request.stream(), max_files=1, max_fields=0, max_part_size=MAX_BODY).parse()
            try:
                upload = form.get('image')
                if upload is None or not hasattr(upload, 'read') or len(form) != 1:
                    return fail(400, 'one_image_required')
                data = await upload.read(MAX_BODY + 1)
                if len(data) > MAX_BODY:
                    return fail(413, 'upload_too_large')
                try:
                    image = decode_image(data)
                except ValueError as error:
                    return fail(415, str(error))
                except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning):
                    return fail(400, 'invalid_image')
            finally:
                await form.close()
        except Exception:
            return fail(400, 'invalid_multipart')
        from starlette.concurrency import run_in_threadpool
        try:
            result = await run_in_threadpool(infer, image)
        except Exception:
            return fail(503, 'inference_failed')
        return Response(result, media_type='image/png')
    finally:
        LOCK.release()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=4174, access_log=False, timeout_keep_alive=5)
