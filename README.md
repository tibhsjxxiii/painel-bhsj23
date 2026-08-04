# Painel Executivo — Barco Hospital São João XXIII

## Arquivos deste pacote

| Arquivo | Papel |
|---|---|
| `template.html` | Modelo do painel (código-fonte, não abra diretamente) |
| `parser.py` | Lê a planilha `.ods` e extrai os dados |
| `gerar_dashboard.py` | Script principal — roda o parser, verifica qualidade dos dados, gera o `dashboard.html` final |
| `worker.js` | Proxy opcional para a IA responder qualquer pergunta (Cloudflare Workers) |
| `dashboard.html` | **O arquivo pronto para publicar** — gerado automaticamente, não edite à mão |

## Uso

```
python gerar_dashboard.py planilha.ods
```

Isso gera `dashboard.html`, já com verificação automática de qualidade impressa no terminal.

## Recomendação: versionar com Git

Como este painel vai ser usado por vários anos, é importante conseguir voltar a uma versão anterior se algo sair errado numa atualização futura. Sugestão simples (gratuita, leva 10 minutos):

1. Crie uma conta em https://github.com (se ainda não tiver)
2. Crie um repositório **privado** (ex: `bhsjxxiii-painel`)
3. Na pasta com estes arquivos:
   ```
   git init
   git add template.html parser.py gerar_dashboard.py worker.js README.md
   git commit -m "Versão inicial do painel"
   git remote add origin https://github.com/SEU-USUARIO/bhsjxxiii-painel.git
   git push -u origin main
   ```
4. A cada atualização de verdade (não o `dashboard.html` gerado, que muda toda expedição — só os scripts/template quando eu te mandar uma versão nova):
   ```
   git add .
   git commit -m "Descrição da mudança"
   git push
   ```

Isso não afeta o funcionamento do painel — é só uma rede de segurança para o código-fonte. A planilha `.ods` e o `dashboard.html` gerado **não precisam** ir para o Git (mudam toda expedição); só os arquivos de código.

## Segurança

- Nunca coloque a chave da API da Anthropic em nenhum destes arquivos — ela vai apenas nas variáveis secretas do Cloudflare Worker (veja `worker.js`)
- O `dashboard.html` gerado não contém nenhum dado pessoal de pacientes — apenas contagens agregadas
