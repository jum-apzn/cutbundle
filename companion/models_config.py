"""Allowlisted data-only ONNX assets. No executable model repository code."""
MODELS = {
 'u2netp': {
  'url': 'https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx',
  'sha256': '309c8469258dda742793dce0ebea8e6dd393174f89934733ecc8b14c76f4ddd8',
  'size': 4574861, 'resolution': 320,
 },
 'birefnet-general-lite': {
  'url': 'https://github.com/danielgatis/rembg/releases/download/v0.0.0/BiRefNet-general-bb_swin_v1_tiny-epoch_232.onnx',
  'sha256': '5600024376f572a557870a5eb0afb1e5961636bef4e1e22132025467d0f03333',
  'size': 224005088, 'resolution': 1024,
 },
}
