# Chat RAG — testar com um documento

Sobe um documento (.txt ou .pdf), indexa no Azure AI Search e permite
conversar com ele usando o Azure OpenAI já provisionado pelo Terraform.

## 1. Instalar dependências

No Cloud Shell (ou seu terminal local, se preferir):

```bash
cd terraform-rag-demo/app
pip install -r requirements.txt
```

## 2. Pegar as chaves e configurar o `.env`

Copie o template:

```bash
cp .env.example .env
```

Pegue as chaves com os comandos abaixo (rode de dentro da pasta
`terraform-rag-demo`, onde está o state do Terraform):

```bash
cd ..
terraform output   # confirma os nomes/endpoints atuais

az cognitiveservices account keys list \
  --name <openai_name_do_output> \
  -g demo_terraform \
  --query key1 -o tsv

az search admin-key show \
  --service-name <search_name_do_output> \
  -g demo_terraform \
  --query primaryKey -o tsv
```

Abra `app/.env` e preencha `AZURE_SEARCH_KEY` e `AZURE_OPENAI_KEY` com
os valores retornados (os endpoints/nomes de deployment já vêm
preenchidos com os padrões do projeto — confira contra o `terraform
output` se você mudou algo).

## 3. Subir um documento

```bash
cd app
python rag_chat.py ingest /caminho/do/seu/documento.pdf
```

Isso quebra o documento em pedaços (chunks), gera o embedding de cada
um e envia pro índice do Azure AI Search. Na primeira execução, o
índice é criado automaticamente.

## 4. Conversar com o documento

```bash
python rag_chat.py chat
```

Digite suas perguntas normalmente. O script busca os trechos mais
relevantes no Search e manda pro modelo de chat junto com a pergunta.
Digite `sair` para encerrar.

## Notas para a demo

- Pra subir mais de um documento, é só rodar `ingest` de novo com
  outro arquivo — eles se acumulam no mesmo índice.
- Se quiser recomeçar do zero, apague o índice pelo Portal (Azure AI
  Search → Índices) e rode `ingest` novamente.
- O `.env` tem as chaves em texto puro — não commitar esse arquivo
  (já está no `.gitignore` do projeto principal, mas confirme se não
  criou um novo repo só para essa pasta).
