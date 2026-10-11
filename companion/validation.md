# Validation report — 2026-10-10 UTC

## Actual default U2NetP inference: passed

After two resource-killed BiRefNet attempts, the default was changed to the much smaller U2NetP model. With the final local API and actual ONNX Runtime CPU inference:

- HTTP 200 transparent PNG, 768×768, 0.76 seconds including first model load.
- Alpha range 0–255; top-left background mean alpha 0.0; central subject mean alpha 254.0003.
- Visually inspected `examples/synthetic-bottle-comparison.jpg`: the bottle is retained while background and cast shadow are removed. Fine soft outline remains and should be inspected for real use.
- Input was an original synthetic bottle illustration created by `validate_inference.py`. This proves the real model/API path works, not broad real-photo quality.
- Output: `examples/synthetic-bottle-cutout.png`; metrics: `examples/inference-result.json`.
- U2NetP asset size 4574861 bytes; SHA-256 `309c8469258dda742793dce0ebea8e6dd393174f89934733ecc8b14c76f4ddd8`; matches upstream rembg MD5 `8e83ca70e441ab06c318d82300c84806`.

## API and setup checks: passed

- Downloaded the exact 224005088-byte BiRefNet-General-Lite ONNX asset from rembg's GitHub release.
- SHA-256 `5600024376f572a557870a5eb0afb1e5961636bef4e1e22132025467d0f03333` recorded; upstream rembg MD5 `4fab47adc4ff364be1713e97b7e66334` matched.
- Installed pinned dependencies in a temporary isolated Python 3.12 environment from PyPI.
- 14 unittest cases passed using those dependencies: good/bad origin, required custom header, hostile Host, preflight, missing model, malformed image, unsupported GIF, upload-size and pixel limits, concurrency rejection, health, and PNG response contract.
- No downloaded Python model code is executed; model loading uses ONNX Runtime CPU only.

## Optional larger BiRefNet output: not verified

Two actual multipart API inference attempts on the included original synthetic bottle illustration were terminated by the execution environment with exit code 137 before any PNG output was returned. This is consistent with a memory/resource kill, but the process emitted no definitive diagnostic. The second attempt disabled the CPU memory arena and memory pattern optimization, limited execution to one thread, and used basic graph optimizations. Both failed to complete.

Therefore: **the optional larger BiRefNet model is not validated in this environment**. Default U2NetP real inference succeeded as described above. Contract tests use a labeled stub and must not be mistaken for successful AI inference. There is no claimed BiRefNet before/after output. CPU latency is unknown. The sample input is a synthetic illustration, not a real photograph or a quality benchmark.

Run `python validate_inference.py` after explicit model setup to obtain a real output and measurements. This script generates its own non-personal input and calls the same multipart API. A successful run saves a PNG, comparison JPEG and JSON metrics under `examples/`. Even a successful synthetic example is not proof of quality on real product photography.

The main app's local Canvas workflows do not require this companion.
