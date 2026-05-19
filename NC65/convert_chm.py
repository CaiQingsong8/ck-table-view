#!/usr/bin/env python3
"""
Convert CHM extracted files to UTF-8 and generate a browsable index page.
"""
import os
import re
import codecs
from html.parser import HTMLParser

CHM_DIR = "/Users/apple/Aohua/ck-table-view/65数据字典_html"
OUTPUT_DIR = "/Users/apple/Aohua/ck-table-view/65数据字典_browsable"

class HHCTocParser(HTMLParser):
    """Parse .hhc file to extract table of contents structure."""
    def __init__(self):
        super().__init__()
        self.toc_items = []
        self.current_item = {}
        self.in_param = False
        self.current_param_name = None

    def handle_starttag(self, tag, attrs):
        if tag == 'object':
            self.current_item = {}
        elif tag == 'param':
            for name, value in attrs:
                if name.lower() == 'name':
                    self.current_param_name = value.lower()
                elif name.lower() == 'value' and self.current_param_name:
                    self.current_item[self.current_param_name] = value

    def handle_endtag(self, tag):
        if tag == 'object' and self.current_item:
            if 'name' in self.current_item:
                self.toc_items.append(self.current_item.copy())
            self.current_item = {}

def convert_html_file(input_path, output_path):
    """Convert a single HTML file from GB2312 to UTF-8."""
    try:
        with open(input_path, 'rb') as f:
            raw_content = f.read()

        # Try different encodings
        for encoding in ['gb2312', 'gbk', 'gb18030', 'utf-8']:
            try:
                content = raw_content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            content = raw_content.decode('gb2312', errors='replace')

        # Update charset meta tag
        content = re.sub(
            r'<meta\s+http-equiv="Content-Type"\s+content="text/html;\s*charset=[^"]*"\s*/?>',
            '<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />',
            content,
            flags=re.IGNORECASE
        )

        # Ensure UTF-8 charset is set
        if 'charset=utf-8' not in content.lower():
            content = content.replace('<head>', '<head>\n<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />')

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error converting {input_path}: {e}")
        return False

def parse_hhc_file(hhc_path):
    """Parse the .hhc table of contents file."""
    parser = HHCTocParser()
    try:
        with open(hhc_path, 'rb') as f:
            raw_content = f.read()

        for encoding in ['gb2312', 'gbk', 'gb18030', 'utf-8']:
            try:
                content = raw_content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            content = raw_content.decode('gb2312', errors='replace')

        parser.feed(content)
    except Exception as e:
        print(f"Error parsing HHC file: {e}")

    return parser.toc_items

def generate_index_html(toc_items, output_path):
    """Generate a browsable index.html with table of contents."""
    # Group items by module
    modules = {}
    current_module = None

    for item in toc_items:
        name = item.get('name', '')
        local = item.get('local', '')
        image_number = item.get('imagenumber', '')

        if image_number == '1' or not local:  # Module header
            current_module = name
            if current_module not in modules:
                modules[current_module] = []
        elif local and current_module:
            modules[current_module].append({'name': name, 'file': local})

    # Generate HTML
    html_content = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NC65 数据字典</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .subtitle {
            font-size: 1.1em;
            opacity: 0.9;
        }
        .search-box {
            margin: 20px 0;
            position: relative;
        }
        .search-box input {
            width: 100%;
            padding: 15px 20px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 8px;
            outline: none;
            transition: border-color 0.3s;
        }
        .search-box input:focus {
            border-color: #667eea;
        }
        .stats {
            display: flex;
            gap: 20px;
            margin: 15px 0;
            flex-wrap: wrap;
        }
        .stat-item {
            background: rgba(255,255,255,0.2);
            padding: 8px 16px;
            border-radius: 5px;
        }
        .toc-container {
            display: flex;
            gap: 20px;
        }
        .sidebar {
            width: 300px;
            flex-shrink: 0;
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            max-height: calc(100vh - 300px);
            overflow-y: auto;
            position: sticky;
            top: 20px;
        }
        .sidebar h3 {
            color: #667eea;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }
        .module-list {
            list-style: none;
        }
        .module-list li {
            margin-bottom: 5px;
        }
        .module-list a {
            color: #555;
            text-decoration: none;
            padding: 8px 12px;
            display: block;
            border-radius: 5px;
            transition: all 0.2s;
        }
        .module-list a:hover {
            background: #f0f0f0;
            color: #667eea;
        }
        .module-list a.active {
            background: #667eea;
            color: white;
        }
        .content {
            flex: 1;
            min-width: 0;
        }
        .module-section {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .module-section h2 {
            color: #667eea;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
            font-size: 1.3em;
        }
        .table-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 10px;
        }
        .table-item {
            padding: 10px 15px;
            background: #f9f9f9;
            border-radius: 5px;
            border-left: 3px solid #667eea;
            transition: all 0.2s;
        }
        .table-item:hover {
            background: #f0f0f0;
            transform: translateX(5px);
        }
        .table-item a {
            color: #333;
            text-decoration: none;
            display: block;
        }
        .table-item .table-name {
            font-weight: bold;
            color: #667eea;
        }
        .table-item .table-desc {
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }
        .hidden {
            display: none;
        }
        .back-to-top {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #667eea;
            color: white;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            cursor: pointer;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            opacity: 0;
            transition: opacity 0.3s;
        }
        .back-to-top.visible {
            opacity: 1;
        }
        @media (max-width: 768px) {
            .toc-container {
                flex-direction: column;
            }
            .sidebar {
                width: 100%;
                max-height: 300px;
                position: static;
            }
            .table-list {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>NC65 数据字典</h1>
            <div class="subtitle">用友 NC65 系统数据字典浏览器</div>
            <div class="stats">
                <div class="stat-item">模块数: <strong>MODULE_COUNT</strong></div>
                <div class="stat-item">数据表: <strong>TABLE_COUNT</strong></div>
            </div>
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="搜索表名或描述...">
            </div>
        </header>

        <div class="toc-container">
            <nav class="sidebar">
                <h3>模块列表</h3>
                <ul class="module-list" id="moduleList">
                    MODULE_LIST_ITEMS
                </ul>
            </nav>

            <main class="content" id="content">
                MODULE_SECTIONS
            </main>
        </div>
    </div>

    <div class="back-to-top" id="backToTop" onclick="window.scrollTo({top:0,behavior:'smooth'})">↑</div>

    <script>
        // Search functionality
        const searchInput = document.getElementById('searchInput');
        searchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase();
            const sections = document.querySelectorAll('.module-section');
            const items = document.querySelectorAll('.table-item');

            if (!query) {
                sections.forEach(s => s.classList.remove('hidden'));
                items.forEach(i => i.classList.remove('hidden'));
                return;
            }

            items.forEach(item => {
                const text = item.textContent.toLowerCase();
                if (text.includes(query)) {
                    item.classList.remove('hidden');
                } else {
                    item.classList.add('hidden');
                }
            });

            sections.forEach(section => {
                const visibleItems = section.querySelectorAll('.table-item:not(.hidden)');
                if (visibleItems.length === 0) {
                    section.classList.add('hidden');
                } else {
                    section.classList.remove('hidden');
                }
            });
        });

        // Sidebar navigation
        document.querySelectorAll('.module-list a').forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
                document.querySelectorAll('.module-list a').forEach(l => l.classList.remove('active'));
                this.classList.add('active');
            });
        });

        // Back to top button
        const backToTop = document.getElementById('backToTop');
        window.addEventListener('scroll', function() {
            if (window.scrollY > 300) {
                backToTop.classList.add('visible');
            } else {
                backToTop.classList.remove('visible');
            }
        });
    </script>
</body>
</html>'''

    # Generate module list items
    module_list_html = ""
    module_sections_html = ""
    module_count = 0
    table_count = 0

    for module_name, tables in modules.items():
        if not tables:
            continue

        module_id = f"module-{module_count}"
        module_list_html += f'<li><a href="#{module_id}">{module_name} ({len(tables)})</a></li>\n'

        module_sections_html += f'''
        <section class="module-section" id="{module_id}">
            <h2>{module_name}</h2>
            <div class="table-list">
        '''

        for table in tables:
            # Extract table code and description
            parts = table['name'].split(' ', 1)
            table_code = parts[0] if parts else ''
            table_desc = parts[1] if len(parts) > 1 else ''

            module_sections_html += f'''
                <div class="table-item">
                    <a href="{table['file']}" target="_blank">
                        <div class="table-name">{table_code}</div>
                        <div class="table-desc">{table_desc}</div>
                    </a>
                </div>
            '''
            table_count += 1

        module_sections_html += '''
            </div>
        </section>
        '''

        module_count += 1

    # Replace placeholders
    html_content = html_content.replace('MODULE_COUNT', str(module_count))
    html_content = html_content.replace('TABLE_COUNT', str(table_count))
    html_content = html_content.replace('MODULE_LIST_ITEMS', module_list_html)
    html_content = html_content.replace('MODULE_SECTIONS', module_sections_html)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

def main():
    print("开始转换 CHM 文件...")

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Parse table of contents
    hhc_file = os.path.join(CHM_DIR, "000_toc.hhc")
    print("解析目录文件...")
    toc_items = parse_hhc_file(hhc_file)
    print(f"找到 {len(toc_items)} 个条目")

    # Convert HTML files
    print("转换 HTML 文件...")
    html_files = [f for f in os.listdir(CHM_DIR) if f.endswith('.html')]
    converted = 0
    for html_file in html_files:
        input_path = os.path.join(CHM_DIR, html_file)
        output_path = os.path.join(OUTPUT_DIR, html_file)
        if convert_html_file(input_path, output_path):
            converted += 1

    print(f"转换完成: {converted}/{len(html_files)} 个文件")

    # Generate index page
    print("生成目录页面...")
    index_path = os.path.join(OUTPUT_DIR, "index.html")
    generate_index_html(toc_items, index_path)
    print(f"目录页面已生成: {index_path}")

    print("\n完成！请在浏览器中打开以下文件查看数据字典:")
    print(f"  {index_path}")

if __name__ == "__main__":
    main()
