# YAML → MD/Mermaid ビルドツール
# 
# 使い方:
#   make build          # 全YAMLをビルド
#   make validate       # 全YAMLをバリデーションのみ
#   make build FILE=xxx # 特定ファイルをビルド
#   make clean          # 出力ファイルを削除
#   make help           # ヘルプ表示

PYTHON := python3
TOOLS_DIR := tools
INPUT_DIR := yaml_created_from_ai
OUTPUT_DIR := output_for_human_read

.PHONY: build validate clean help watch

# デフォルトターゲット
.DEFAULT_GOAL := help

# 全YAMLをビルド
build:
ifdef FILE
	@$(PYTHON) $(TOOLS_DIR)/build.py $(FILE)
else
	@$(PYTHON) $(TOOLS_DIR)/build.py --all
endif

# 全YAMLをバリデーションのみ
validate:
ifdef FILE
	@$(PYTHON) $(TOOLS_DIR)/build.py $(FILE) --validate-only
else
	@$(PYTHON) $(TOOLS_DIR)/build.py --all --validate-only
endif

# 特定のタイプのみビルド（例: make api, make bugfix）
api:
	@$(PYTHON) $(TOOLS_DIR)/build.py $(INPUT_DIR)/user_api_redesign.yaml

bugfix:
	@$(PYTHON) $(TOOLS_DIR)/build.py $(INPUT_DIR)/bugfix_sample.yaml

feature:
	@$(PYTHON) $(TOOLS_DIR)/build.py $(INPUT_DIR)/feature_design_sample.yaml

infra:
	@$(PYTHON) $(TOOLS_DIR)/build.py $(INPUT_DIR)/infrastructure_sample.yaml

# 出力ファイルを削除
clean:
	@echo "🗑️  出力ファイルを削除中..."
	@rm -f $(OUTPUT_DIR)/*.md
	@echo "✅ 完了"

# ヘルプ表示
help:
	@echo ""
	@echo "📘 YAML → MD/Mermaid ビルドツール"
	@echo ""
	@echo "使い方:"
	@echo "  make build              全YAMLをビルド（validate → MD → Mermaid）"
	@echo "  make validate           全YAMLをバリデーションのみ"
	@echo "  make build FILE=path    特定ファイルをビルド"
	@echo "  make clean              出力ファイルを削除"
	@echo ""
	@echo "ショートカット:"
	@echo "  make api                API設計サンプルをビルド"
	@echo "  make bugfix             バグ修正サンプルをビルド"
	@echo "  make feature            新機能設計サンプルをビルド"
	@echo "  make infra              インフラ設計サンプルをビルド"
	@echo ""
	@echo "ディレクトリ:"
	@echo "  入力: $(INPUT_DIR)/"
	@echo "  出力: $(OUTPUT_DIR)/"
	@echo ""
