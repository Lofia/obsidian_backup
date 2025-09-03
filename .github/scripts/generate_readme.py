#!/usr/bin/env python3
"""
Safer generate_readme.py
Usage:
  python generate_readme.py --source "." --dest README.md --count 3
"""

import re
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
import frontmatter
import urllib.parse

DATE_RE = re.compile(r'(\d{4}-\d{2}-\d{2})')

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--source', default='.', help='Source folder to scan for notes')
    p.add_argument('--dest', default='README.md', help='README file to update')
    p.add_argument('--count', type=int, default=3, help='How many latest notes to include')
    return p.parse_args()

def find_markdown_files(src):
    p = Path(src)
    if not p.exists():
        return []
    # ignore .git and .github folders
    files = [f for f in p.rglob('*.md') if f.is_file() and not any(part.startswith('.git') or part == '.github' for part in f.parts)]
    return files

def extract_date_from_filename(name):
    m = DATE_RE.search(name)
    if m:
        try:
            return datetime.strptime(m.group(1), '%Y-%m-%d')
        except Exception:
            return None
    return None

def extract_frontmatter_date(path):
    try:
        post = frontmatter.load(path)
        if 'date' in post.metadata:
            try:
                return datetime.fromisoformat(str(post.metadata['date']))
            except Exception:
                try:
                    return datetime.strptime(str(post.metadata['date']), '%Y-%m-%d')
                except Exception:
                    return None
    except Exception:
        return None
    return None

def get_title(path):
    # Try first heading
    try:
        text = path.read_text(encoding='utf-8')
        for line in text.splitlines():
            line = line.strip()
            if line.startswith('#'):
                return re.sub(r'^#+\s*', '', line).strip()
    except Exception:
        pass
    # fallback: filename without extension
    return path.stem

def file_mtime(path):
    return datetime.fromtimestamp(path.stat().st_mtime)

def infer_date(path):
    # 1) filename
    d = extract_date_from_filename(path.name)
    if d:
        return d
    # 2) frontmatter date
    d = extract_frontmatter_date(path)
    if d:
        return d
    # 3) file mtime
    return file_mtime(path)

def escape_md_text(text):
    """
    Escape characters that would break the Markdown link text.
    We escape closing/opening square brackets so the [text] part is safe.
    """
    return text.replace('\\', '\\\\').replace('[', '\\[').replace(']', '\\]')

def url_encode_path(relpath):
    """
    Percent-encode the path but keep '/' so links remain relative.
    """
    return urllib.parse.quote(relpath, safe="/")

def build_list(files, count, repo_root, dest_name):
    items = []
    seen = set()
    for f in files:
        rel = os.path.relpath(str(f), repo_root).replace('\\', '/')
        # skip the destination README and skip files inside .github
        if Path(rel).name.lower() == dest_name.lower() or rel.startswith('.github/'):
            continue
        if rel in seen:
            continue
        seen.add(rel)

        date = infer_date(f)
        title = get_title(f)
        items.append((date, title, rel))
    # sort desc
    items.sort(key=lambda t: t[0] or datetime.min, reverse=True)
    lines = []
    for date, title, rel in items[:count]:
        date_str = date.strftime('%Y-%m-%d') if date else ''
        safe_title = escape_md_text(f"{date_str} — {title}")
        safe_link = url_encode_path(rel)
        lines.append(f"- [{safe_title}]({safe_link})")
    return '\n'.join(lines)

def replace_section(readme_path, new_md, start_marker='<!-- DAILY_NOTES:START -->', end_marker='<!-- DAILY_NOTES:END -->'):
    if not readme_path.exists():
        # create with marker
        content = f"{start_marker}\n{new_md}\n{end_marker}\n"
        readme_path.write_text(content, encoding='utf-8')
        return True
    content = readme_path.read_text(encoding='utf-8')
    pattern = re.compile(re.escape(start_marker) + r'.*?' + re.escape(end_marker), re.DOTALL)
    replacement = f"{start_marker}\n{new_md}\n{end_marker}"
    if pattern.search(content):
        new_content = pattern.sub(replacement, content)
    else:
        # append markers at end
        new_content = content + "\n\n" + replacement
    if new_content != content:
        readme_path.write_text(new_content, encoding='utf-8')
        return True
    return False

def main():
    args = parse_args()
    repo_root = Path('.').resolve()
    files = find_markdown_files(args.source)
    if not files:
        print(f"No markdown files found in {args.source}")
        sys.exit(0)
    new_md = build_list(files, args.count, repo_root, args.dest)
    changed = replace_section(Path(args.dest), new_md)
    if changed:
        print(f"Updated {args.dest}")
    else:
        print("No change to README")

if __name__ == '__main__':
    main()
