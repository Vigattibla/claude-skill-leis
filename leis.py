"""Consulta local ao acervo ctresb/leis (D:/leis) com saída curta.

Uso:
  python leis.py buscar "termos" [--n 10] [--todas]      # ementas/títulos; --todas inclui revogadas
  python leis.py art LEI ART [ART...] [--max 2500]       # texto dos artigos (LEI = número ou apelido; --max 0 = inteiro)
  python leis.py grep LEI "termo" [--n 8]                # artigos da lei que contêm o termo
  python leis.py info LEI                                # cabeçalho (ementa, vigência, fonte)
  python leis.py indexar [--completo]                    # índice incremental (--completo relê tudo)
  python leis.py atualizar                               # git pull + reindexar
  python leis.py instalar [PASTA...]                     # clona o acervo (sparse), indexa e agenda 04:00
"""
import os, re, sys, subprocess, unicodedata

RAIZ = os.environ.get("LEIS_DIR") or ("D:/leis" if os.path.isdir("D:/leis") else os.path.expanduser("~/leis"))
REPO = "https://github.com/ctresb/leis.git"
PASTAS = ["federal/leis-ordinarias", "federal/leis-complementares", "federal/decretos",
          "federal/decretos-lei", "estaduais/MG", "jurisprudencia"]
INDICE = os.path.join(RAIZ, "_indice.tsv")
APELIDOS = {
    "cf": "constituicao", "constituicao": "constituicao",
    "cdc": "8078", "lgpd": "13709", "eca": "8069", "cc": "10406", "codigo-civil": "10406",
    "turismo": "11771", "marco-civil": "12965", "superendividamento": "14181",
    "estatuto-idoso": "10741", "pix": None,
}
ALTERA = ("altera", "acrescenta", "da nova redacao", "revoga", "modifica", "inclui")
ART_RE = re.compile(r"^\*\*Art\. ?(\d+)[ºo°]?(-[A-Z])?\.?\*\*")
sys.stdout.reconfigure(encoding="utf-8")


def norm(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def cabecalho(caminho):
    meta = {}
    with open(caminho, encoding="utf-8", errors="replace") as f:
        if f.readline().strip() != "---":
            return meta
        for linha in f:
            if linha.strip() == "---":
                break
            if ":" in linha:
                k, v = linha.split(":", 1)
                meta[k.strip()] = v.strip().strip('"')
    return meta


def indexar(completo=False):
    """Incremental: reaproveita linhas de arquivos não modificados desde o último índice."""
    antigo, t0 = {}, 0
    if os.path.exists(INDICE) and not completo:
        t0 = os.path.getmtime(INDICE)
        with open(INDICE, encoding="utf-8") as f:
            for l in f:
                antigo[l.split("\t", 1)[0]] = l
    n, tmp = 0, INDICE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as out:
        for base, dirs, files in os.walk(RAIZ):
            dirs[:] = [d for d in dirs if not d.startswith((".", "_"))]
            for nome in files:
                if not nome.endswith(".md") or nome.startswith("_") or nome.isupper():
                    continue
                p = os.path.join(base, nome)
                rel = os.path.relpath(p, RAIZ).replace("\\", "/")
                if rel in antigo and os.path.getmtime(p) < t0:
                    out.write(antigo[rel])
                    n += 1
                    continue
                m = cabecalho(p)
                if not m.get("titulo"):
                    continue
                campos = [rel, m.get("tipo", ""), m.get("numero", ""), m.get("data", ""),
                          m.get("revogada", ""), m.get("titulo", ""), m.get("ementa", "")]
                out.write("\t".join(c.replace("\t", " ").replace("\n", " ") for c in campos) + "\n")
                n += 1
    os.replace(tmp, INDICE)
    print(f"indice: {n} normas")


def linhas_indice():
    if not os.path.exists(INDICE):
        indexar()
    with open(INDICE, encoding="utf-8") as f:
        for l in f:
            yield l.rstrip("\n").split("\t")


def achar(lei):
    """Resolve número/apelido/caminho → caminho do arquivo. Prioriza federal vigente."""
    alvo = APELIDOS.get(lei.lower(), lei)
    if alvo == "constituicao":
        return os.path.join(RAIZ, "constituicao.md")
    if os.path.exists(os.path.join(RAIZ, lei)):
        return os.path.join(RAIZ, lei)
    num, _, ano = alvo.replace(".", "").partition("/")
    cands = [c for c in linhas_indice() if c[2] == num and (not ano or c[3].startswith(ano))]
    if not cands:
        sys.exit(f"nao achei: {lei}")
    cands.sort(key=lambda c: (not c[0].startswith("federal/leis-"), c[4] == "true", c[0]))
    if len(cands) > 1 and not cands[0][0].startswith("federal/leis-"):
        print("# outras: " + "; ".join(c[0] for c in cands[1:4]))
    return os.path.join(RAIZ, cands[0][0])


def titulo(p):
    return cabecalho(p).get("titulo") or os.path.relpath(p, RAIZ).replace("\\", "/")


def artigos(caminho):
    """Gera (numero, texto) de cada artigo."""
    atual, buf = None, []
    with open(caminho, encoding="utf-8", errors="replace") as f:
        for linha in f:
            m = ART_RE.match(linha)
            if m or linha.startswith("#"):
                if atual:
                    yield atual, "".join(buf).strip()
                atual, buf = (m.group(1) + (m.group(2) or "")) if m else None, []
            if atual:
                buf.append(linha)
    if atual:
        yield atual, "".join(buf).strip()


def prioridade(rel):
    for i, p in enumerate(("federal/leis-", "federal/decretos-lei", "federal/", "constituicao")):
        if rel.startswith(p):
            return i
    return 9


def cmd_buscar(termos, n=10, todas=False):
    ts = [norm(t) for t in termos.split() if len(t) > 2]
    frase = norm(termos)
    res = []
    for c in linhas_indice():
        if not todas and c[4] == "true":
            continue
        txt = norm(c[5] + " " + c[6])
        hits = sum(t in txt for t in ts)
        if hits:
            ementa = norm(c[6])
            hits += ementa.find(" ".join(ts)) >= 0 or ementa.find(frase) >= 0  # frase inteira
            alteradora = ementa.startswith(ALTERA)  # norma que só altera outra vai depois
            res.append((-hits, alteradora, prioridade(c[0]), c))
    # mais termos > lei federal > decreto-lei > decreto > estadual/juris; empate: mais recente
    res.sort(key=lambda r: r[-1][3], reverse=True)
    res.sort(key=lambda r: r[:3])
    for *_, c in res[:n]:
        rev = " [REVOGADA]" if c[4] == "true" else ""
        print(f"{c[0]} | {c[5]}{rev} | {c[6][:160]}")
    print(f"# {len(res)} resultados")


def instalar(pastas):
    if not os.path.isdir(os.path.join(RAIZ, ".git")):
        subprocess.run(["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse", REPO, RAIZ], check=True)
    subprocess.run(["git", "-C", RAIZ, "sparse-checkout", "set"] + (pastas or PASTAS), check=True)
    with open(os.path.join(RAIZ, ".git", "info", "exclude"), "a", encoding="utf-8") as f:
        f.write("_indice.tsv\n_indice.tsv.tmp\n")
    indexar(True)
    cmd = f'"{sys.executable}" "{os.path.abspath(__file__)}" atualizar'
    if os.name == "nt":
        subprocess.run(["schtasks", "/create", "/tn", "Leis atualizar", "/sc", "daily", "/st", "04:00",
                        "/tr", cmd, "/f"], check=False)
    else:
        print(f"agendar (crontab -e): 0 4 * * * {cmd}")
    print(f"acervo: {RAIZ}")


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    op = a[0]
    flag_n = int(a[a.index("--n") + 1]) if "--n" in a else None
    flag_max = int(a[a.index("--max") + 1]) if "--max" in a else None
    if op == "indexar":
        indexar("--completo" in a)
    elif op == "atualizar":
        subprocess.run(["git", "-C", RAIZ, "pull", "--depth", "1"], check=False)
        indexar()
    elif op == "instalar":
        instalar([x for x in a[1:] if not x.startswith("--")])
    elif op == "buscar":
        cmd_buscar(a[1], flag_n or 10, "--todas" in a)
    elif op == "info":
        p = achar(a[1])
        m = cabecalho(p)
        print(os.path.relpath(p, RAIZ).replace("\\", "/"))
        for k in ("titulo", "ementa", "revogada", "versao_texto", "fonte"):
            print(f"{k}: {m.get(k, '')}")
    elif op == "art":
        p = achar(a[1])
        args = [x for i, x in enumerate(a[2:], 2) if not x.startswith("--") and a[i - 1] != "--max"]
        quer = {x.upper() for x in args}
        lim = 2500 if flag_max is None else flag_max
        print(f"# {titulo(p)}")
        for num, txt in artigos(p):
            if num.upper() in quer:
                quer.discard(num.upper())  # 1ª ocorrência (corpo); evita repetir em ADCT/anexos
                corta = lim and len(txt) > lim
                print(txt[:lim] if corta else txt)
                print(f"# … +{len(txt) - lim} chars (--max 0 = inteiro)\n" if corta else "")
                if not quer:
                    break
        if quer:
            print("# nao achei art. " + ", ".join(sorted(quer)))
    elif op == "grep":
        p = achar(a[1])
        t = norm(a[2])
        print(f"# {titulo(p)}")
        n = 0
        for num, txt in artigos(p):
            if t in norm(txt):
                print(txt[:700] + ("…" if len(txt) > 700 else "") + "\n")
                n += 1
                if n >= (flag_n or 8):
                    print("# limite atingido (--n)")
                    break
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
