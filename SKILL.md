---
name: leis
description: Consulta a legislação brasileira local (acervo ctresb/leis em D:\leis, Markdown) com saída curta. Use quando o usuário digitar /leis ou quando precisar embasar texto jurídico, condições de promoção, termos, política de privacidade, regras de cancelamento, direito do consumidor, LGPD, ECA, turismo/hotelaria ou qualquer citação de lei.
argument-hint: "[pergunta, termo ou lei+artigo]"
---

# /leis — consulta enxuta à legislação

Argumentos: `$ARGUMENTS`

Nunca ler arquivo de lei inteiro (`Read`/`cat`): sempre pelo script, que devolve só o trecho.

```
python ~/.claude/skills/leis/leis.py buscar "termos"          # acha a norma pela ementa
python ~/.claude/skills/leis/leis.py art cdc 49 31            # só os artigos pedidos (corta em 2500 chars; --max 0 = inteiro)
python ~/.claude/skills/leis/leis.py grep lgpd "consentimento" --n 5
python ~/.claude/skills/leis/leis.py info 11771               # ementa, vigência, fonte
python ~/.claude/skills/leis/leis.py atualizar                # git pull + reindexa
```

LEI aceita número (`8078`, `8078/1990`), caminho relativo ou apelido:
`cf` · `cdc` (8.078) · `lgpd` (13.709) · `eca` (8.069) · `cc` (10.406) · `turismo` (11.771) ·
`marco-civil` (12.965) · `superendividamento` (14.181) · `estatuto-idoso` (10.741).

Fluxo: `buscar` (se não souber a norma) → `grep` para localizar artigos → `art` para o texto exato.
Busca padrão ignora revogadas (`--todas` inclui). Usar frase da ementa ("proteção do consumidor")
em vez de palavra solta: frase inteira sobe no ranking; leis que só alteram outra vão para o fim.
Índice `_indice.tsv` (no acervo) incremental; tarefa do Agendador "Leis atualizar" roda `atualizar` às 04:00.

Ao citar: número da lei + artigo + aviso de que o acervo é conversão automática; texto oficial
no link `fonte` (via `info`). Não substitui revisão jurídica — dizer isso ao entregar texto legal.

Normas já mapeadas para landing/promoção de resort:
- CDC art. 6º III (informação clara), 30–31 (oferta vincula e deve ser precisa), 35, 37 (publicidade
  enganosa), 46, 49 (arrependimento 7 dias fora do estabelecimento), 51 (cláusulas abusivas), 54 §3º–4º
  (contrato de adesão: destaque em cláusula restritiva).
- Decreto 7.962/2013 (comércio eletrônico: identificação, informação, arrependimento).
- LGPD arts. 7º, 8º, 9º (consentimento e informação no formulário de captura).
- ECA (hospedagem de menor) e Lei 11.771/2008 (Lei Geral do Turismo).

Acervo (`LEIS_DIR`, senão `D:/leis` se existir, senão `~/leis`): clone parcial (`--depth 1 --filter=blob:none`, sparse) com constituição, federal
(leis ordinárias/complementares, decretos, decretos-lei), `estaduais/MG` e `jurisprudencia`.
Para incluir outra pasta: `git -C <acervo> sparse-checkout add <pasta>` e depois `leis.py indexar`.
Máquina nova: `python ~/.claude/skills/leis/leis.py instalar` (clona, indexa ~25 min, agenda 04:00).
