#!/usr/bin/env python3
"""
設計YAML 汎用バリデーションツール（doc_typeディレクトリ版）
meta.category + meta.doc_type からスキーマを自動検出して検証します。
"""

import re
import yaml
import json
import argparse
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

# common/ を import するため
_common_dir = Path(__file__).resolve().parent.parent
if str(_common_dir) not in sys.path:
    sys.path.insert(0, str(_common_dir))
from config import AI_DOCUMENT_SCHEME_JSON, GITHUB_LINK_CHECK_HOSTS, HUMAN_DOCUMENT_MD
from paths import get_categories_dir, get_available_categories, get_doc_types, get_project_root
from md_base import load_yaml

try:
    import jsonschema
    from jsonschema import Draft7Validator, ValidationError
except ImportError:
    print("❌ jsonschema パッケージがインストールされていません")
    print("   pip install jsonschema でインストールしてください")
    sys.exit(1)

try:
    from referencing import Registry, Resource
    from referencing.exceptions import NoSuchResource
    from referencing.jsonschema import DRAFT7
except ImportError:
    print("❌ referencing パッケージがインストールされていません")
    print("   pip install referencing でインストールしてください")
    sys.exit(1)


def get_schema_path(category: str, doc_type: str) -> Optional[Path]:
    """category/doc_typeに対応するスキーマパスを取得"""
    schema_path = get_categories_dir() / category / doc_type / AI_DOCUMENT_SCHEME_JSON
    return schema_path if schema_path.exists() else None


def load_schema(schema_path: Path) -> dict:
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _retrieve_file_uri(uri: str):
    """file: URI で参照される JSON スキーマを読み込み Resource で返す"""
    parsed = urlparse(uri)
    if parsed.scheme != 'file':
        raise NoSuchResource(ref=uri)
    path = Path(parsed.path)
    if not path.exists():
        raise NoSuchResource(ref=uri)
    contents = json.loads(path.read_text(encoding='utf-8'))
    return Resource.from_contents(contents)


def _resolve_refs_to_absolute(schema: dict, base_path: Path) -> None:
    """スキーマ内の相対 $ref を絶対 file: URI に書き換える（in-place）"""
    if not isinstance(schema, dict):
        return
    for key, value in list(schema.items()):
        if key == '$ref' and isinstance(value, str) and not value.startswith('#'):
            if value.startswith('..') or value.startswith('/'):
                ref_path, _, fragment = value.partition('#')
                resolved = (base_path / ref_path).resolve()
                schema[key] = resolved.as_uri() + ('#' + fragment if fragment else '')
        elif isinstance(value, dict):
            _resolve_refs_to_absolute(value, base_path)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    _resolve_refs_to_absolute(item, base_path)


def load_schema_and_registry(schema_path: Path) -> tuple[dict, Registry]:
    """スキーマを読み込み、外部 $ref 解決用の Registry を返す"""
    schema = load_schema(schema_path)
    base_path = schema_path.resolve().parent
    _resolve_refs_to_absolute(schema, base_path)
    main_uri = schema_path.resolve().as_uri()
    resource = DRAFT7.create_resource(schema)
    registry = Registry(retrieve=_retrieve_file_uri).with_resource(uri=main_uri, resource=resource)
    return schema, registry


def detect_category_and_doc_type(yaml_data: dict) -> tuple[Optional[str], Optional[str]]:
    """YAMLデータからcategory, doc_typeを検出"""
    meta = yaml_data.get('meta', {})
    return meta.get('category'), meta.get('doc_type')


def format_error_path(error: ValidationError) -> str:
    if error.absolute_path:
        return ' → '.join(str(p) for p in error.absolute_path)
    return '(ルート)'


def validate_yaml(
    yaml_data: dict,
    schema: dict,
    verbose: bool = False,
    registry: Optional[Registry] = None,
) -> tuple[bool, list[str]]:
    validator = Draft7Validator(schema, registry=registry) if registry else Draft7Validator(schema)
    errors = list(validator.iter_errors(yaml_data))
    
    if not errors:
        return True, []
    
    error_messages = []
    for error in sorted(errors, key=lambda e: str(list(e.absolute_path))):
        path = format_error_path(error)
        message = error.message
        
        if verbose:
            error_messages.append(f"❌ [{path}] {message}")
            if error.context:
                for suberror in error.context:
                    error_messages.append(f"   └─ {suberror.message}")
        else:
            error_messages.append(f"❌ [{path}] {message}")
    
    return False, error_messages


def run_common_checks(yaml_data: dict) -> list[str]:
    warnings = []
    
    meta = yaml_data.get('meta', {})
    if meta.get('status') == 'done' and not meta.get('author'):
        warnings.append("⚠️ ステータスがdoneですが、作成者(author)が定義されていません")
    
    return warnings


def collect_reference_urls(yaml_data: dict) -> list[str]:
    """YAML から references[].url を収集する"""
    urls = []
    for ref in yaml_data.get('references', []):
        url = ref.get('url') if isinstance(ref, dict) else None
        if url and isinstance(url, str) and url.strip():
            urls.append(url.strip())
    return urls


def collect_all_urls_and_paths(yaml_data: dict) -> list[str]:
    """
    YAML から references[].url および related_docs 由来の url/パスを収集する。
    references, overview.related_docs（{ title, url } または文字列）, target.related_docs（文字列配列）を対象とする。
    """
    result = []
    for ref in yaml_data.get('references', []):
        url = ref.get('url') if isinstance(ref, dict) else None
        if url and isinstance(url, str) and url.strip():
            result.append(url.strip())
    for doc in yaml_data.get('overview', {}).get('related_docs', []):
        if isinstance(doc, dict):
            url = doc.get('url')
        elif isinstance(doc, str):
            url = doc
        else:
            url = None
        if url and isinstance(url, str) and url.strip():
            result.append(url.strip())
    for item in yaml_data.get('target', {}).get('related_docs', []):
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
    return result


def is_file_path(value: str) -> bool:
    """http/https で始まらなければファイルパスとみなす。空は呼び元で除外すること。"""
    s = value.strip().lower()
    return not (s.startswith('http://') or s.startswith('https://'))


def check_file_path_exists(path_str: str, base: Path) -> Optional[str]:
    """
    ファイルパスを base 基準で解決し、存在するかチェックする。
    存在しなければエラーメッセージを返す。存在すれば None。
    空・空白はスキップ（None を返す）。絶対パスでプロジェクト外の場合はスキップ（None）。
    """
    s = path_str.strip()
    if not s:
        return None
    if s.lower().startswith('file://'):
        parsed = urlparse(s)
        resolved = Path(parsed.path)
    elif s.startswith('/'):
        resolved = base / s.lstrip('/')
    else:
        resolved = (base / s).resolve()
    try:
        if not resolved.exists():
            return f"ファイルパスが存在しません: {path_str}"
    except OSError:
        return f"ファイルパスを解決できません: {path_str}"
    return None


def run_file_path_check(yaml_data: dict, base_path: Path) -> list[str]:
    """
    references および related_docs 由来の url/パスのうち、ファイルパスとみなすものについて
    実在チェックを行い、存在しないパスのエラーメッセージリストを返す。
    """
    all_values = collect_all_urls_and_paths(yaml_data)
    file_paths = list(dict.fromkeys(v for v in all_values if v.strip() and is_file_path(v)))
    errors = []
    for path_str in file_paths:
        err = check_file_path_exists(path_str, base_path)
        if err:
            errors.append(err)
    return errors


def is_github_url(url: str) -> bool:
    """GitHub の URL かどうか（config.GITHUB_LINK_CHECK_HOSTS で定義されたホスト）"""
    try:
        parsed = urlparse(url)
        netloc = (parsed.netloc or '').lower()
        return any(host in netloc for host in GITHUB_LINK_CHECK_HOSTS)
    except Exception:
        return False


def check_github_url_not_404(url: str, timeout: int = 5) -> Optional[str]:
    """
    GitHub URL に HEAD でアクセスし、404 の場合はエラーメッセージを返す。
    404 でなければ None。ネットワークエラー等は None（警告扱いにする場合は呼び元で対応可能）。
    """
    try:
        req = urllib.request.Request(url, method='HEAD')
        req.add_header('User-Agent', 'Mozilla/5.0 (compatible; doc-validate-link-check/1.0)')
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 404:
                return f"GitHub リンクが 404: {url}"
            return None
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return f"GitHub リンクが 404: {url}"
        return None
    except Exception:
        return None


def run_github_link_check(yaml_data: dict, timeout: int = 5, sleep_seconds: float = 1.0) -> list[str]:
    """references[].url のうち GitHub の URL を HEAD で検証し、404 の URL をエラーとして返す"""
    errors = []
    urls = collect_reference_urls(yaml_data)
    github_urls = [u for u in urls if is_github_url(u)]
    for url in github_urls:
        err = check_github_url_not_404(url, timeout=timeout)
        if err:
            errors.append(err)
        time.sleep(sleep_seconds)
    return errors


# --- 生成済み human/document.md 内の相対リンク検証 ---

_MD_LINK_PATTERN = re.compile(r'\]\(([^)]+)\)')


def extract_md_relative_links(content: str) -> list[str]:
    """
    Markdown 本文から相対パスのリンク href を抽出する。
    ](href) の形式で、href が # のみまたは http(s) で始まるものは除外する。
    """
    hrefs = []
    for m in _MD_LINK_PATTERN.finditer(content):
        href = m.group(1).strip()
        if not href:
            continue
        if href.startswith('#'):
            continue
        if href.lower().startswith('http://') or href.lower().startswith('https://'):
            continue
        if href.startswith('mailto:'):
            continue
        hrefs.append(href)
    return hrefs


def check_md_file_links(md_path: Path, project_root: Path) -> list[str]:
    """
    human/document.md 内の相対リンクが、そのファイルの位置（human ディレクトリ）から解決できるか検証する。
    リンクをクリックしたときに正しく飛べるかどうかは、この基準でしか判定できない。
    """
    if not md_path.exists():
        return [f"ファイルが存在しません: {md_path}"]
    try:
        content = md_path.read_text(encoding='utf-8')
    except OSError as e:
        return [f"読み込み失敗 {md_path}: {e}"]
    human_dir = md_path.resolve().parent  # document.md があるディレクトリ = 相対パスの解決基準
    errors = []
    for href in extract_md_relative_links(content):
        try:
            resolved = (human_dir / href).resolve()
            if not resolved.exists():
                errors.append(f"リンク先が存在しません: {md_path} 内の {href} → {resolved}")
        except OSError:
            errors.append(f"リンク先を解決できません: {md_path} 内の {href}")
    return errors


def run_md_links_check(project_root: Optional[Path] = None) -> list[str]:
    """
    categories 配下の全 human/document.md を走査し、
    相対リンクのファイル存在チェックを行う。エラーがあればメッセージリストを返す。
    """
    root = project_root or get_project_root()
    categories_dir = get_categories_dir()
    if not categories_dir.exists():
        return []
    all_errors = []
    for category in get_available_categories():
        for doc_type in get_doc_types(category):
            md_path = categories_dir / category / doc_type / HUMAN_DOCUMENT_MD
            if not md_path.exists():
                continue
            errs = check_md_file_links(md_path, root)
            all_errors.extend(errs)
    return all_errors


def main_md_links_check(args) -> int:
    """--check-md-links 用のエントリ。全 human/document.md のリンク検証を行い exit code を返す。"""
    project_root = get_project_root()
    if args.input and Path(args.input).exists():
        md_path = Path(args.input).resolve()
        if not md_path.is_file():
            print(f"❌ 指定パスはファイルではありません: {md_path}")
            return 1
        errors = check_md_file_links(md_path, project_root)
    else:
        errors = run_md_links_check(project_root)
    if errors:
        print()
        print("=== MD リンクエラー ===")
        for err in errors:
            print(err)
        print()
        print("=" * 40)
        print(f"❌ MD リンク検証失敗（{len(errors)} 件）")
        return 1
    print()
    print("=" * 40)
    print("✅ MD リンク検証成功")
    return 0


def main():
    parser = argparse.ArgumentParser(description='設計YAMLをバリデートします')
    parser.add_argument('input', nargs='?', help='入力YAMLファイルのパス（--check-md-links 時は human/document.md のパス、省略時は --all で全件）')
    parser.add_argument('-s', '--schema', default=None, help='JSON Schemaファイルのパス')
    parser.add_argument('-v', '--verbose', action='store_true', help='詳細なエラー情報を表示')
    parser.add_argument('--strict', action='store_true', help='警告もエラーとして扱う')
    parser.add_argument('--list', action='store_true', help='利用可能なcategory/doc_typeを表示')
    parser.add_argument('--skip-link-check', action='store_true', help='GitHub リンクの 404 チェックをスキップ')
    parser.add_argument('--skip-file-path-check', action='store_true', help='related_docs/references のファイルパス存在チェックをスキップ')
    parser.add_argument('--check-md-links', action='store_true', help='生成済み human/document.md 内の相対リンクのファイル存在を検証')
    parser.add_argument('--all', '-a', action='store_true', help='--check-md-links 時: 全 human/document.md を対象にする')
    
    args = parser.parse_args()
    
    if args.check_md_links:
        if args.all or not args.input:
            # 全 human/document.md を対象
            code = main_md_links_check(argparse.Namespace(input=None))
        else:
            code = main_md_links_check(args)
        sys.exit(code)
    
    if args.list:
        print("利用可能なcategory/doc_type:")
        for category in get_available_categories():
            print(f"\n📦 {category}")
            for doc_type in get_doc_types(category):
                print(f"   └─ {doc_type}")
        sys.exit(0)
    
    if not args.input:
        print("❌ 入力YAMLファイルを指定してください")
        sys.exit(1)
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 入力ファイルが見つかりません: {input_path}")
        sys.exit(1)
    
    try:
        yaml_data = load_yaml(args.input)
    except yaml.YAMLError as e:
        print(f"❌ YAMLの解析に失敗しました:")
        print(f"   {e}")
        sys.exit(1)
    
    # スキーマパスの解決
    if args.schema:
        schema_path = Path(args.schema)
        category, doc_type = detect_category_and_doc_type(yaml_data)
    else:
        category, doc_type = detect_category_and_doc_type(yaml_data)
        
        if not category or not doc_type:
            print("❌ category/doc_typeを検出できません")
            print("   meta.category, meta.doc_type フィールドを指定してください")
            sys.exit(1)
        
        schema_path = get_schema_path(category, doc_type)
        
        if not schema_path:
            print(f"❌ スキーマが見つかりません: {category}/{doc_type}")
            sys.exit(1)
    
    if not schema_path.exists():
        print(f"❌ スキーマファイルが見つかりません: {schema_path}")
        sys.exit(1)
    
    print(f"📄 検証対象: {input_path}")
    print(f"📋 スキーマ: {schema_path}")
    print(f"📁 パス: {category}/{doc_type}")
    print()
    
    try:
        schema, registry = load_schema_and_registry(schema_path)
    except json.JSONDecodeError as e:
        print(f"❌ スキーマの解析に失敗しました:")
        print(f"   {e}")
        sys.exit(1)
    
    print("🔍 スキーマ検証中...")
    is_valid, errors = validate_yaml(yaml_data, schema, args.verbose, registry=registry)
    
    if errors:
        print()
        print("=== エラー ===")
        for error in errors:
            print(error)
    
    print()
    print("🔍 追加チェック中...")
    warnings = run_common_checks(yaml_data)
    
    if warnings:
        print()
        print("=== 警告 ===")
        for warning in warnings:
            print(warning)
    
    link_errors = []
    if not args.skip_link_check:
        print()
        print("🔍 GitHub リンク確認中...")
        link_errors = run_github_link_check(yaml_data, timeout=5, sleep_seconds=1.0)
        if link_errors:
            print()
            print("=== リンクエラー ===")
            for err in link_errors:
                print(err)
    
    file_path_errors = []
    if not args.skip_file_path_check:
        print()
        print("🔍 ファイルパス確認中...")
        file_path_errors = run_file_path_check(yaml_data, get_project_root())
        if file_path_errors:
            print()
            print("=== ファイルパスエラー ===")
            for err in file_path_errors:
                print(err)
    
    print()
    print("=" * 40)
    
    if is_valid and (not warnings or not args.strict) and not link_errors and not file_path_errors:
        if warnings:
            print(f"✅ バリデーション成功（警告 {len(warnings)} 件）")
        else:
            print("✅ バリデーション成功")
        sys.exit(0)
    else:
        error_count = len(errors) + len(link_errors) + len(file_path_errors)
        warning_count = len(warnings)
        if args.strict:
            print(f"❌ バリデーション失敗（エラー {error_count} 件、警告 {warning_count} 件）")
        else:
            print(f"❌ バリデーション失敗（エラー {error_count} 件）")
        sys.exit(1)


if __name__ == '__main__':
    main()
