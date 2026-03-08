# PDF Editor

<div align="center">
  <img src="src-tauri/icons/icon.png" alt="PDF Editor Logo" width="120" height="120">

  <h3>简洁高效的Windows桌面PDF编辑器</h3>

  <p>
    <strong>合并 · 分拆 · 图片转PDF · 文字编辑</strong>
  </p>

  <p>
    <a href="#功能特性">功能特性</a> •
    <a href="#技术栈">技术栈</a> •
    <a href="#安装">安装</a> •
    <a href="#开发">开发</a> •
    <a href="#项目结构">项目结构</a>
  </p>
</div>

---

## 功能特性

### ✅ 已完成功能

#### 📄 PDF合并
- 支持多个PDF文件合并为一个
- 实时预览每个文件的首页缩略图
- 拖拽排序调整文件顺序
- 自动生成默认输出文件名（如：`test.pdf` → `test_merge.pdf`）
- 点击合并后自动弹出保存对话框

#### ✂️ PDF分拆
支持三种分拆模式：
- **按页码范围分拆**：自定义多个页码范围
- **按固定页数分拆**：每隔N页生成一个新文件
- **提取选中页面**：通过缩略图预览选择需要的页面

智能功能：
- 自动显示PDF总页数
- 范围校验：
  - 结束页必须大于等于开始页
  - 最大页码不能超过文档总页数
  - 多个范围之间不允许交叉
- 智能添加范围：
  - 自动从上一范围的结束页+1开始
  - 超出总页数时自动查找空白区域
  - 所有页面被覆盖时显示提示
- 自动生成输出文件名（如：`test.pdf` → `test_split_1.pdf`）
- 点击分拆后自动弹出目录选择对话框

#### 🖼️ 图片转PDF
- 支持JPG、PNG、BMP、TIFF、WebP、GIF格式
- 批量添加多张图片
- 拖拽排序调整顺序
- 实时PDF预览效果：
  - 预览页面大小、方向与实际输出一致
  - 根据图片尺寸自动判断页面方向
  - 支持预览多种适应模式
- 多种转换选项：
  - 页面大小：A4 / Letter
  - 页面方向：自动 / 纵向 / 横向
  - 边距：可调节（0-100px）
  - 图片质量：可调节（1-100%）
  - 适应模式：保持比例 / 填充页面 / 拉伸
- 自动EXIF旋转
- 自动生成默认输出文件名（如：`photo.jpg` → `photo.pdf`）
- 点击转换后自动弹出保存对话框

#### ✏️ 文字编辑
- 功能开发中，敬请期待
- 计划支持：替换、添加、删除文字

---

## 技术栈

### 前端层
- **SvelteKit** 2.9.0 - 前端框架
- **Svelte** 5.0.0 - UI组件库（使用 Runes API）
- **TypeScript** 5.6.2 - 类型系统
- **TailwindCSS** 4.2.1 - 样式框架
- **Vite** 6.0.3 - 构建工具

### 后端层
- **Tauri** 2.x - 桌面应用框架
- **Rust** Edition 2021 - 系统编程语言

### PDF处理层
- **Python** 3.11+ - Sidecar进程
- **PyMuPDF** 1.24.0+ (fitz) - PDF操作库
- **Pillow** 11.0.0+ - 图像处理

---

## 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                    前端层 (WebView)                              │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  SvelteKit 2.x + TypeScript 5.x + TailwindCSS v4           ││
│  │  ┌─────────┬─────────┬──────────┬─────────┐                ││
│  │  │ PDF合并 │ PDF分拆 │ 图片转PDF │ 文字编辑│                ││
│  │  │   ✅    │   ✅    │   ✅     │   🚧    │                ││
│  │  └─────────┴─────────┴──────────┴─────────┘                ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                           ↕ Tauri IPC (invoke/events)
┌─────────────────────────────────────────────────────────────────┐
│                  后端层 (Rust Main Process)                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Tauri 2.x Plugins: dialog, fs, shell                       ││
│  │  Commands: pdf_merge, pdf_split, pdf_convert_images, etc.   ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                           ↕ JSON-RPC 2.0 (stdio)
┌─────────────────────────────────────────────────────────────────┐
│               PDF处理层 (Python Sidecar)                         │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  PyMuPDF 1.24+ (fitz) - PDF Operations                       ││
│  │  Handlers: merge, split, convert, edit, thumbnails          ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## 安装

### 系统要求

- **操作系统**：Windows 10/11
- **运行时**：Python 3.11+
- **包管理器**：[pnpm](https://pnpm.io/)（推荐）

### 开发环境设置

1. **克隆仓库**
```bash
git clone https://github.com/your-username/pdf-editor.git
cd pdf-editor
```

2. **安装前端依赖**
```bash
pnpm install
```

3. **安装Python依赖**
```bash
cd pdf-sidecar
pip install -r requirements.txt
```

4. **安装Rust**
- 访问 [rustup.rs](https://rustup.rs/)
- 按照说明安装Rust

---

## 开发

### 开发模式

启动前端开发服务器（端口 1420）：
```bash
pnpm dev
```

启动Tauri桌面应用（开发模式）：
```bash
pnpm tauri dev
```

### 构建生产版本

构建前端：
```bash
pnpm build
```

构建桌面应用：
```bash
pnpm tauri build
```

### 类型检查
```bash
pnpm check
```

---

## 项目结构

```
pdf-editor/
├── src/                        # SvelteKit前端
│   ├── lib/
│   │   ├── types.ts           # TypeScript接口定义
│   │   └── components/
│   │       └── Layout/
│   │           └── Sidebar.svelte
│   └── routes/
│       ├── +layout.svelte     # 根布局
│       ├── +page.svelte       # PDF合并 (/)
│       ├── split/
│       │   └── +page.svelte   # PDF分拆 (/split)
│       ├── convert/
│       │   └── +page.svelte   # 图片转PDF (/convert)
│       └── edit/
│           └── +page.svelte   # 文字编辑 (/edit)
├── src-tauri/                  # Rust后端
│   ├── src/
│   │   ├── main.rs            # 入口点
│   │   ├── lib.rs             # Tauri命令
│   │   └── sidecar/mod.rs     # JSON-RPC客户端
│   ├── Cargo.toml
│   ├── tauri.conf.json
│   └── capabilities/default.json
├── pdf-sidecar/                # Python PDF处理器
│   ├── src/
│   │   ├── __main__.py        # JSON-RPC服务器入口
│   │   ├── core/pdf_ops.py    # 工具函数
│   │   ├── handlers/
│   │   │   ├── merge.py       # pdf.merge
│   │   │   ├── split.py       # pdf.split
│   │   │   ├── convert.py     # pdf.convert_images
│   │   │   ├── edit.py        # pdf.edit_text
│   │   │   └── thumbnails.py  # pdf.get_thumbnails, pdf.get_file_preview
│   │   └── utils/temp.py
│   └── requirements.txt
└── static/
```

---

## API参考

### Python处理器（JSON-RPC方法）

| 方法 | 处理器 | 描述 |
|------|--------|------|
| `pdf.merge` | merge.py | 合并多个PDF |
| `pdf.split` | split.py | 分拆PDF（range/fixed/extract模式）|
| `pdf.convert_images` | convert.py | 图片转PDF |
| `pdf.edit_text` | edit.py | 编辑PDF文字 |
| `pdf.get_thumbnails` | thumbnails.py | 生成页面缩略图 |
| `pdf.get_file_preview` | thumbnails.py | 生成首页预览 |
| `system.ping` | __main__.py | 健康检查 |
| `system.info` | __main__.py | 系统信息 |

### Tauri命令（IPC接口）

所有命令返回 `Result<T, String>` 类型。

---

## 开发规范

### 前端
- **Svelte 5 Runes**: 使用 `$state()` 进行响应式状态管理
- **SSR**: 已禁用（`ssr = false`）
- **UI语言**: 中文界面
- **样式**: TailwindCSS v4 内联类
- **路由**: 文件系统路由

### 后端
- **命令**: 返回 `Result<T, String>`
- **错误传播**: Sidecar → JSON-RPC错误 → Rust错误 → 前端捕获

### Python Sidecar
- **响应格式**: `{'success': bool, ...}` 或 `{'success': False, 'error': str}`
- **页面索引**: 参数使用1-based，PyMuPDF使用0-based
- **日志**: `logging.getLogger(__name__)` 输出到stderr

### 文件命名规则
- **合并**: `{原文件名}_merge.pdf`（取第一个文件名）
- **分拆**: `{原文件名}_split_1.pdf`, `{原文件名}_split_2.pdf`, ...
- **图片转PDF**: `{第一张图片名}.pdf`

---

## 已知问题

- [ ] 书签分拆模式未实现（`split.py`）
- [ ] CSP已禁用（安全性待加强）
- [ ] PyMuPDF AGPL-3.0许可证兼容性检查
- [ ] Sidecar未配置打包（需添加`externalBin`）
- [ ] 无单元/集成测试
- [ ] 无CI/CD流程

---

## 许可证

MIT License

---

## 致谢

- [Tauri](https://tauri.app/) - 跨平台桌面应用框架
- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF处理库
- [Svelte](https://svelte.dev/) - 前端框架

---

<div align="center">
  <p>Made with ❤️ by Fan Jiayu</p>
</div>
