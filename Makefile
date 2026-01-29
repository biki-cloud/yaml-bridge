# YAML → MD/Mermaid ビルドツール
# 
# 使い方:
#   make build              # 全doc_typesをビルド
#   make validate           # 全YAMLをバリデーションのみ
#   make list               # 利用可能なcategory/doc_typeを表示
#
# カテゴリ別:
#   make overview           # プロジェクト概要
#   make investigation      # 調査
#   make design             # 設計
#   make development        # 開発
#   make verification       # 動作確認
#
#   make clean              # 出力ファイルを削除
#   make help               # ヘルプ表示

PYTHON := python3
BUILD_SCRIPT := common/tools/build.py

.PHONY: build validate clean help list
.PHONY: overview investigation design development verification

.DEFAULT_GOAL := help

# 全doc_typesをビルド
build:
	@$(PYTHON) $(BUILD_SCRIPT) --all

# 全YAMLをバリデーションのみ
validate:
	@$(PYTHON) $(BUILD_SCRIPT) --all --validate-only

# カテゴリ別ビルド
overview:
	@$(PYTHON) $(BUILD_SCRIPT) --category overview

investigation:
	@$(PYTHON) $(BUILD_SCRIPT) --category investigation

design:
	@$(PYTHON) $(BUILD_SCRIPT) --category design

development:
	@$(PYTHON) $(BUILD_SCRIPT) --category development

verification:
	@$(PYTHON) $(BUILD_SCRIPT) --category verification

# 利用可能なcategory/doc_typeを表示
list:
	@$(PYTHON) $(BUILD_SCRIPT) --list

# 出力ファイルを削除
clean:
	@echo "🗑️  出力ファイルを削除中..."
	@rm -f categories/*/*/human_document.md
	@echo "✅ 完了"

# ヘルプ表示
help:
	@echo ""
	@echo "📘 YAML → MD/Mermaid ビルドツール"
	@echo ""
	@echo "基本コマンド:"
	@echo "  make build              全doc_typesをビルド"
	@echo "  make validate           全YAMLをバリデーションのみ"
	@echo "  make list               利用可能なcategory/doc_typeを表示"
	@echo "  make clean              出力ファイルを削除"
	@echo ""
	@echo "カテゴリ別ビルド:"
	@echo "  make overview           プロジェクト概要"
	@echo "  make investigation      調査"
	@echo "  make design             設計"
	@echo "  make development        開発"
	@echo "  make verification       動作確認"
	@echo ""
	@echo "ディレクトリ構成:"
	@echo "  categories/{category}/{doc_type}/"
	@echo "    ai_document_scheme.json  スキーマ定義"
	@echo "    create_human_document.py  Markdown生成"
	@echo "    to_mermaid.py             Mermaid図生成"
	@echo "    ai_document_guide.yaml    ガイド・テンプレート"
	@echo "    ai_document.yaml          AIが扱うファイル（ビルド対象）"
	@echo "    human_document.md         生成されたMarkdown"
	@echo ""
