# 📄 PDF Object Remover

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://github.com/Profhameed/pdf-object-remover)

A powerful, user-friendly desktop application for removing unwanted objects from PDF files. Remove watermarks, images, text, and other elements with precision using an intuitive graphical interface.

## ✨ Features

### 🎯 **Intelligent Object Detection**
- Automatically detects and lists all objects on each page
- Support for **images**, **text blocks**, and **vector graphics**
- Real-time highlighting of selected objects

### 🖼️ **Image Removal**
- Remove images by their unique identifier (xref)
- Batch deletion across all pages
- Preview before deletion

### 📝 **Advanced Text Removal**
Two powerful removal modes:
- **By Location & Content**: Remove text that appears in the same position across multiple pages (perfect for headers, footers, and watermarks)
- **By Content Only**: Remove all instances of specific text throughout the entire document
- **Flexible Scope**: Choose to remove from current page only or all pages

### 🔍 **Smart PDF Navigation & Viewing**
- Page-by-page browsing with prev/next buttons
- Jump to specific pages instantly
- Slider for quick navigation
- **Zoom Controls**: Adjustable zoom slider (10%-500%)
- **Pan & Scroll**: Click and drag to pan when zoomed, mouse wheel to scroll
- **Auto-fit Mode**: Reset zoom to fit page to window

### 💾 **Safe Editing**
- Non-destructive editing (original file remains unchanged)
- "Save As" feature to create modified copies
- Optimized output with compression and cleanup

## 🚀 Quick Start

### 📦 Option 1: Download Executable (Windows - Easiest!)

**No installation required!**

1. Go to the [Latest Release](https://github.com/Profhameed/pdf-object-remover/releases/latest)
2. Download `PDF-Object-Remover.exe`
3. Double-click to run - that's it!

### 🐍 Option 2: Run from Source (All Platforms)

**Prerequisites:**
- Python 3.7 or higher
- pip (Python package manager)

**Installation:**

1. **Clone this repository**
   ```bash
   git clone https://github.com/Profhameed/pdf-object-remover.git
   cd pdf-object-remover
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python pdf_watermark_remover.py
   ```

## 📖 Usage

1. **Upload a PDF**: Click "Upload PDF" and select your file
2. **Navigate**: Browse through pages using the navigation controls
3. **Zoom**: Use the zoom slider to zoom in/out, click and drag to pan when zoomed
4. **Configure Removal**: Set removal options (all pages vs current page, text removal mode)
5. **Select Objects**: Click on any object in the list to highlight it on the page
6. **Remove**: Click "Remove Selected Object" to remove based on your settings
7. **Save**: Use "Save As..." to export your modified PDF

### Example Use Cases

- ✅ Remove watermarks from documents
- ✅ Clean up scanned PDFs
- ✅ Delete unwanted logos or branding
- ✅ Remove headers and footers
- ✅ Eliminate draft stamps or confidential markings

## 🖥️ Screenshots

> *Upload your screenshots here to showcase the application interface*

```
[Screenshot Placeholder]
Main Interface - Object List View
```

```
[Screenshot Placeholder]
Removal Options Panel - Configure Settings
```

## 🛠️ Technical Details

### Built With

- **[PyMuPDF (fitz)](https://pymupdf.readthedocs.io/)** - High-performance PDF manipulation
- **[Pillow (PIL)](https://python-pillow.org/)** - Image processing
- **[Tkinter](https://docs.python.org/3/library/tkinter.html)** - Cross-platform GUI

### Key Features

- **Efficient Memory Usage**: Renders pages on-demand
- **High-Quality Rendering**: Automatic zoom calculation for optimal viewing
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Responsive Design**: Adaptive layout with resizable panes

## 📋 Requirements

```
PyMuPDF>=1.23.0
Pillow>=10.0.0
```

> **Note**: Tkinter usually comes pre-installed with Python. If not, install it via your system's package manager.

## 🤝 Contributing

Contributions are welcome! Feel free to:

- 🐛 Report bugs
- 💡 Suggest new features
- 🔧 Submit pull requests
- 📖 Improve documentation

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is intended for legitimate use only. Please respect copyright laws and only remove content from PDFs that you own or have permission to modify.

## 🙏 Acknowledgments

- Thanks to the PyMuPDF team for their excellent PDF library
- Inspired by the need for a simple, free PDF cleaning tool

## 📬 Contact & Support

- **Issues**: [GitHub Issues](https://github.com/Profhameed/pdf-object-remover/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Profhameed/pdf-object-remover/discussions)

---

<div align="center">

**If you find this project helpful, please consider giving it a ⭐!**

Made with ❤️ by the open-source community

</div>
