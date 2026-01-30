#!/usr/bin/env python3
"""document YAML → Markdown 変換（共通ロジックは common/md_base.generate_document_markdown）"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / 'common'))
from md_base import generate_document_markdown, run_create_human_document

if __name__ == '__main__':
    run_create_human_document(generate_document_markdown)
