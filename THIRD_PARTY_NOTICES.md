# Third-party notices and model provenance

## Browser application

The shipped browser runtime uses only standard browser APIs. There are no bundled npm dependencies, icon libraries, fonts, models, third-party images, or downloaded code. The ZIP writer and image-processing implementation were authored for this project. Demo illustrations were drawn for this project and are covered by the repository MIT license.

Optional development tool: [Playwright](https://github.com/microsoft/playwright), Apache-2.0. It is not bundled in the application and does not execute in user sessions.

## Optional model distinction

This app's MIT license does not license external weights or their dependencies. Model code and weights must be reviewed separately.

Checked 2026-10-10 against primary sources:

- Default U2NetP: original [U-2-Net](https://github.com/xuebinqin/U-2-Net) project is Apache-2.0 and distributes pretrained U2NetP weights in its README. The companion uses the pinned ONNX conversion from the official rembg release. Exact hash, origin, and bundled upstream notices are in [companion/README.md](companion/README.md). Model weights are downloaded separately and are not included in this repository.

- Official [BiRefNet code](https://github.com/ZhengPeng7/BiRefNet/blob/main/LICENSE): MIT.
- Official [ZhengPeng7/BiRefNet_lite model card](https://huggingface.co/ZhengPeng7/BiRefNet_lite): declares MIT and identifies itself as the authors' official weights.
- The model card contains examples using `trust_remote_code=True`. The core app does not execute these examples or download model code.

No BRIA RMBG weights are bundled. Do not assume every model supported by a background-removal package permits commercial use.

See `companion/` for the exact optional inference implementation, model origin, artifact checksum, license notices, and setup instructions. Installing a separately obtained model is an explicit local action. The browser core must continue working when the companion or model is absent.
