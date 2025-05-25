# Ollama環境セットアップガイド

## システム要件
- メモリ: 最低 16GB RAM推奨
- CPU: 4コア以上推奨
- ディスク容量: 各モデルあたり4-8GB

## Ollamaのインストール
### Windows:
1. https://ollama.ai からOllamaをダウンロード
2. インストーラーを実行
3. コマンドプロンプトで `ollama serve` を実行してサーバーを起動

### Linux/macOS:
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve
```

## モデルのインストール
### deepseek-coder
- 説明: コード生成に特化した高性能OSSモデル
- サイズ: 6.7B
- 必要メモリ: 8GB
- インストール: `ollama pull deepseek-coder`
- 用途: code_generation, code_review, debugging

### llama2
- 説明: Metaの汎用LLMモデル
- サイズ: 7B
- 必要メモリ: 6GB
- インストール: `ollama pull llama2`
- 用途: text_generation, qa, summarization

### mistral
- 説明: 高性能でコンパクトなフランス製LLM
- サイズ: 7B
- 必要メモリ: 6GB
- インストール: `ollama pull mistral`
- 用途: text_generation, qa

### codellama
- 説明: Metaのコード生成特化モデル
- サイズ: 7B
- 必要メモリ: 8GB
- インストール: `ollama pull codellama`
- 用途: code_generation, code_completion

## 自動セットアップ
```bash
python scripts/setup_ollama.py
```
