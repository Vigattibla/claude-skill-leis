# leis — skill do Claude Code para legislação brasileira

Consulta local e enxuta ao acervo [ctresb/leis](https://github.com/ctresb/leis) (Markdown): devolve só o trecho pedido, sem ler a lei inteira.

## Instalar

```bash
git clone https://github.com/Vigattibla/claude-skill-leis ~/.claude/skills/leis
python ~/.claude/skills/leis/leis.py instalar
```

`instalar` clona o acervo (parcial: federal, MG e jurisprudência) em `D:/leis` (se existir) ou `~/leis` — ou em `LEIS_DIR` —, gera o índice (~25 min na 1ª vez) e agenda a atualização diária às 04:00 (Agendador do Windows; em Linux/macOS mostra a linha do cron). Outras pastas: `leis.py instalar federal estaduais/SP ...`.

Atualizar a skill: `git -C ~/.claude/skills/leis pull`.

## Uso

```
/leis prazo de arrependimento em compra online
python leis.py buscar "proteção do consumidor"
python leis.py art cdc 49 31
python leis.py grep lgpd consentimento --n 3
python leis.py info 11771
```

Apelidos: cf, cdc, lgpd, eca, cc, turismo, marco-civil, superendividamento, estatuto-idoso.

O acervo é conversão automática; não substitui o texto oficial (link `fonte` no `info`) nem revisão jurídica.
