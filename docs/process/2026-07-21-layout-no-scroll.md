# 2026-07-21 页面布局：去掉总体滚动条，三栏各自内部滚动

## 背景
原页面三块（参数填写区、图片列表、识别结果）各自用 `max-height: 70vh` 等计算高度，且未约束页面整体高度，导致页面可能出现总体滚动条、三栏高度不一致。用户要求：三块不应分别计算高度，并去掉页面总体滚动条。

## 改动 (static/index.html CSS)
- `body`：`height:100vh; display:flex; flex-direction:column; overflow:hidden`，整体固定为视口高度、不滚动。
- `.topbar`：`flex:none` 固定高度。
- `.layout`：`flex:1; min-height:0; overflow:hidden`，占满剩余高度。
- `.col`：统一 `display:flex; flex-direction:column; overflow:hidden`，各栏自行管理内部滚动。
- `.col-config`：`overflow-y:auto`（参数多时栏内滚动）。
- `.col-list` / `.col-detail`：作为 flex 列，内部 `.list`（`flex:1; min-height:0; overflow:auto`）与 `#detail`（`flex:1; min-height:0; overflow:auto`）填满并内部滚动。
- `h3`：`flex:none` 固定。

## 验证
- 浏览器打开后页面无总体滚动条；参数区、图片列表、识别结果各自独立滚动。
