# Validação dos documentos

A CI documental executa em pull requests e por disparo manual, independentemente dos checks de governança. Para executar localmente, com Python 3 e Git instalados, na raiz do repositório:

```bash
python scripts/validate_markdown.py
```

O comando verifica os arquivos Markdown rastreados pelo Git: leitura em UTF-8, conteúdo não vazio e marcadores comuns de conflito de merge. Arquivos novos precisam estar adicionados ao índice Git para serem incluídos na verificação local. A validação não confere links, sintaxe completa de Markdown ou a correção do conteúdo.
