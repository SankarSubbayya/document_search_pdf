# 📚 MkDocs Documentation Guide

This guide shows you how to build and serve documentation using MkDocs with the Material theme.

## 🚀 Quick Start

### Install MkDocs (if not already installed)
```bash
# Using UV (recommended - already in pyproject.toml)
uv sync

# Or using pip
pip install mkdocs mkdocs-material mkdocstrings[python]
```

## 📖 Basic MkDocs Commands

### 1. **Serve Documentation Locally** (Development)
```bash
# Using UV
uv run mkdocs serve

# Or directly if mkdocs is in PATH
mkdocs serve

# With custom port
uv run mkdocs serve -a localhost:8001

# With live reload disabled
uv run mkdocs serve --no-livereload
```

**Default URL**: http://localhost:8000

The development server includes:
- ✅ Live reload (auto-refresh on file changes)
- ✅ Error messages in browser
- ✅ Fast build times

### 2. **Build Static Documentation**
```bash
# Build the documentation
uv run mkdocs build

# Build with verbose output
uv run mkdocs build --verbose

# Build with strict mode (fail on warnings)
uv run mkdocs build --strict

# Clean build (remove old files first)
uv run mkdocs build --clean
```

This creates a `site/` directory with static HTML files.

### 3. **Deploy to GitHub Pages**
```bash
# Deploy to gh-pages branch
uv run mkdocs gh-deploy

# Deploy with custom commit message
uv run mkdocs gh-deploy -m "Update documentation"

# Force push (overwrite history)
uv run mkdocs gh-deploy --force

# Deploy with verbose output
uv run mkdocs gh-deploy --verbose
```

## 🎨 MkDocs Material Theme Features

Your project uses **Material for MkDocs**, which includes:

### Search
- Full-text search automatically included
- Search suggestions and highlighting

### Navigation
- Tabs for main sections
- Collapsible sidebar sections
- Breadcrumb navigation

### Code Features
- Syntax highlighting
- Copy button on code blocks
- Line numbers
- Code annotations

## 📁 Documentation Structure

```
document_search_pdf/
├── mkdocs.yml          # Configuration file
├── docs/               # Documentation source
│   ├── index.md        # Homepage
│   ├── README.md       # Documentation index
│   ├── PROJECT_STRUCTURE.md
│   ├── INSTALLATION.md
│   └── ...
└── site/               # Built documentation (generated)
    └── index.html
```

## 🛠️ Common Tasks

### Add a New Page

1. Create a new Markdown file in `docs/`:
```bash
echo "# New Feature" > docs/new-feature.md
```

2. Add it to `mkdocs.yml` navigation:
```yaml
nav:
  - Home: index.md
  - New Feature: new-feature.md  # Add this line
```

3. View changes:
```bash
uv run mkdocs serve
```

### Change Theme Colors

Edit `mkdocs.yml`:
```yaml
theme:
  palette:
    primary: blue      # Change primary color
    accent: light-blue # Change accent color
```

Available colors: red, pink, purple, deep-purple, indigo, blue, light-blue, cyan, teal, green, light-green, lime, yellow, amber, orange, deep-orange, brown, grey, blue-grey

### Enable Dark Mode Toggle

Already configured in your `mkdocs.yml`:
```yaml
theme:
  palette:
    - scheme: default  # Light mode
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    - scheme: slate    # Dark mode
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
```

## 📝 Writing Documentation

### Admonitions (Callout Boxes)

```markdown
!!! note "Optional Title"
    This is a note admonition.

!!! warning
    This is a warning.

!!! danger
    This is dangerous!

!!! success
    Operation completed successfully!

!!! info
    Additional information here.

!!! tip
    Pro tip: Use UV for faster builds!
```

### Code Blocks with Syntax Highlighting

````markdown
```python
def hello_world():
    """Say hello."""
    print("Hello, MkDocs!")
```

```bash
# Install dependencies
uv sync
```
````

### Tabs

```markdown
=== "Python"

    ```python
    print("Hello")
    ```

=== "JavaScript"

    ```javascript
    console.log("Hello");
    ```
```

### Tables

```markdown
| Feature | Status | Description |
|---------|--------|-------------|
| Search  | ✅     | Full-text search |
| PDF Upload | ✅  | Upload and index PDFs |
| OCR     | ⚠️     | Optional (needs Tesseract) |
```

## 🔧 Troubleshooting

### Port Already in Use
```bash
# Use a different port
uv run mkdocs serve -a localhost:8001
```

### Build Warnings
```bash
# See detailed warnings
uv run mkdocs build --verbose

# Fail on warnings
uv run mkdocs build --strict
```

### Missing Dependencies
```bash
# Install all documentation dependencies
uv sync
# or
pip install mkdocs mkdocs-material mkdocstrings[python]
```

### Broken Links
```bash
# Check for broken internal links
uv run mkdocs build --strict
```

## 🚢 Production Deployment Options

### 1. GitHub Pages (Easiest)
```bash
# Deploy to GitHub Pages
uv run mkdocs gh-deploy
```
URL: `https://yourusername.github.io/document_search_pdf/`

### 2. Netlify
1. Build documentation: `mkdocs build`
2. Deploy `site/` directory to Netlify

### 3. Docker
```dockerfile
FROM squidfunk/mkdocs-material
COPY . /docs
WORKDIR /docs
EXPOSE 8000
CMD ["serve", "--dev-addr=0.0.0.0:8000"]
```

### 4. Static Hosting (S3, Firebase, etc.)
```bash
# Build static files
uv run mkdocs build

# Upload site/ directory to your host
```

## 📊 Your Current Configuration

Your `mkdocs.yml` includes:
- ✅ Material theme
- ✅ Dark/light mode toggle
- ✅ Search plugin
- ✅ Code highlighting
- ✅ Navigation tabs
- ✅ Python docstrings support

## 🎯 Quick Commands Reference

| Command | Description |
|---------|-------------|
| `uv run mkdocs serve` | Start development server |
| `uv run mkdocs build` | Build static site |
| `uv run mkdocs gh-deploy` | Deploy to GitHub Pages |
| `uv run mkdocs new [dir]` | Create new project |
| `uv run mkdocs --help` | Show all commands |

## 🔗 Useful Resources

- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [Material Icons](https://squidfunk.github.io/mkdocs-material/reference/icons-emojis/)
- [Python Markdown Extensions](https://python-markdown.github.io/extensions/)

## 🏃 Start Now!

```bash
# Start the documentation server
uv run mkdocs serve

# Open in browser
# http://localhost:8000
```

Your documentation will be available at http://localhost:8000 with live reload enabled!