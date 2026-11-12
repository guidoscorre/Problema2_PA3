#!/usr/bin/env python3
"""
Fase 3 - validacao e comparacao Fase 1 x Fase 3 (codigo de TESTE).

Pode usar estruturas prontas da linguagem: a regra do enunciado vale so para o nucleo.
Este arquivo fica na mesma pasta de medicoes_fase2.py (ele reaproveita a leitura das cargas).

Uso, a partir da raiz do repositorio:
    python medicoes_fase3.py --validar --pasta dados_teste        # pequeno.txt x gabarito da Fase 3
    python medicoes_fase3.py --pasta dados_teste                  # tabela Fase 1 x Fase 3 (5 execucoes)
    python medicoes_fase3.py --rotacoes dados_teste/pequeno.txt   # mostra as rotacoes que a AVL faz
Opcoes: --execucoes 5  --fase1 main.py  --fase3 fase3/sistema.py  --saida .
"""
import argparse
import importlib.util
import math
import os
import re
import statistics
import subprocess
import sys
import tracemalloc

from medicoes_fase2 import descobrir_cargas, ler_operacoes

AQUI = os.path.dirname(os.path.abspath(__file__))
COM_UMA_LINHA = ("REG", "BUSCA", "PROX", "PROXL", "REM", "ALT")


# ------------------------------------------------------------ execucao oficial
def rodar(programa, caminho):
    """Roda 'python programa arquivo' como a professora vai rodar. Devolve (tempo_ms, saida)."""
    r = subprocess.run([sys.executable, programa, caminho], capture_output=True,
                       text=True, encoding="utf-8", timeout=3600)
    if r.returncode != 0:
        raise RuntimeError("codigo de saida %d; stderr: %s" % (r.returncode, r.stderr.strip()[-400:]))
    m = re.search(r"TEMPO_MS\s+([0-9]+\.[0-9]{3})", r.stderr)
    if not m:
        raise RuntimeError("saida de erro sem a linha TEMPO_MS")
    return float(m.group(1)), r.stdout.splitlines()


def carregar(programa):
    spec = importlib.util.spec_from_file_location("prog_" + str(abs(hash(programa))), programa)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def estatisticas(programa, ops):
    """Aplica so os REG e REM em processo e mede: n final, altura final e memoria (tracemalloc)."""
    arvore = carregar(programa).ArvoreChegadas()
    n = 0
    tracemalloc.start()
    for comando, args in ops:
        if comando == "REG" and len(args) >= 3:
            if arvore.registrar_chegada(args[0], args[1], args[2]) == "OK":
                n += 1
        elif comando == "REM" and len(args) >= 3:
            if arvore.remover_chegada(args[0], args[1], args[2]) == "OK":
                n -= 1
    atual, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return n, int(arvore.altura()), atual / 1024.0, pico / 1024.0


# ------------------------------------------------- separar a saida por operacao
def alinhar(ops, linhas):
    """Divide a saida em blocos, um por operacao (ENTRE e SEMANA ocupam varias linhas)."""
    blocos = []
    p = 0
    for comando, args in ops:
        if comando == "ENTRE":
            ok = p < len(linhas) and linhas[p].strip().isdigit()
            n = 1 + (int(linhas[p]) if ok else 0)
        elif comando == "SEMANA":
            n = int(args[3])
        elif comando in COM_UMA_LINHA:
            n = 1
        else:
            n = 0
        blocos.append([x.strip() for x in linhas[p:p + n]])
        p += n
    return blocos


def comparar(ops, obtido, esperado, ignorar_todos_alt=False):
    """
    Compara operacao por operacao. As respostas de ALT dadas depois da primeira remocao
    bem-sucedida nao sao comparadas (regra do enunciado para a Fase 3).
    Devolve a lista de diferencas (numero da operacao, texto da operacao, obtido, esperado).
    """
    bo, be = alinhar(ops, obtido), alinhar(ops, esperado)
    removeu = False
    difs = []
    for i, (comando, args) in enumerate(ops):
        if comando == "ALT" and (removeu or ignorar_todos_alt):
            continue
        if bo[i] != be[i]:
            difs.append((i + 1, " ".join([comando] + args), " | ".join(bo[i]), " | ".join(be[i])))
        if comando == "REM" and be[i] == ["OK"]:
            removeu = True
    return difs


# ----------------------------------------------------------------- --validar
def validar(args):
    entrada = os.path.join(args.pasta, "pequeno.txt")
    gabarito = os.path.join(args.pasta, "pequeno_esperado_fase3.txt")
    if not os.path.exists(entrada) or not os.path.exists(gabarito):
        print("[ERRO] pequeno.txt ou pequeno_esperado_fase3.txt nao encontrado em: %s" % args.pasta)
        return 2
    ops = ler_operacoes(entrada)
    tempo, obtido = rodar(args.fase3, entrada)
    with open(gabarito, encoding="utf-8-sig") as f:
        esperado = [x for x in f.read().splitlines()]
    while esperado and not esperado[-1].strip():
        esperado.pop()
    difs = comparar(ops, obtido, esperado)
    print("Operacoes: %s | Esperado: %s | TEMPO_MS %.3f" % (entrada, gabarito, tempo))
    if not difs:
        print("SUCESSO! Saida identica ao gabarito da Fase 3 (ALT depois da 1a remocao nao e comparado).")
        return 0
    print("FALHA! %d operacao(oes) diferente(s). Primeiras 15:" % len(difs))
    for n, op, o, e in difs[:15]:
        print("  operacao %d (%s)\n     obtido  : %s\n     esperado: %s" % (n, op, o, e))
    return 1


# --------------------------------------------------------------------- tabela
def tabela(args):
    cargas = descobrir_cargas(args.pasta)
    if not cargas:
        print("[ERRO] Nenhuma carga (arquivo com 500+ REG) encontrada em: %s" % args.pasta)
        return 2

    print("Cargas encontradas:")
    for c in cargas:
        print("  %-32s N=%-6d %s" % (c["nome"], c["n"], c["versao"]))
    print("\n%d execucoes por arquivo e por fase (mediana).\n" % args.execucoes)

    linhas = []
    for c in cargas:
        t1, t3 = [], []
        for rep in range(args.execucoes):
            tempo1, saida1 = rodar(args.fase1, c["caminho"])
            tempo3, saida3 = rodar(args.fase3, c["caminho"])
            t1.append(tempo1)
            t3.append(tempo3)
            print("  %-32s %d/%d: Fase 1 %10.3f ms | Fase 3 %10.3f ms"
                  % (c["nome"], rep + 1, args.execucoes, tempo1, tempo3), flush=True)

        # as duas fases precisam dar as mesmas respostas (ALT e' a unica que muda: alturas diferentes)
        difs = comparar(c["ops"], saida3, saida1, ignorar_todos_alt=True)
        n_final, altura3, mem3, pico3 = estatisticas(args.fase3, c["ops"])
        _, altura1, mem1, pico1 = estatisticas(args.fase1, c["ops"])
        limite = 1.45 * math.log2(n_final + 2)
        linhas.append({
            "nome": c["nome"], "versao": c["versao"], "n_reg": c["n"], "n_final": n_final,
            "t1": statistics.median(t1), "t3": statistics.median(t3),
            "h1": altura1, "h3": altura3, "limite": limite, "ok": altura3 <= limite,
            "mem1": mem1, "mem3": mem3, "iguais": not difs,
        })
        print("  -> F1 %.3f ms (h=%d) | F3 %.3f ms (h=%d, limite %.2f) | respostas Fase1 = Fase3: %s\n"
              % (linhas[-1]["t1"], altura1, linhas[-1]["t3"], altura3, limite,
                 "SIM" if not difs else "NAO (%d diferencas, ex.: %s)" % (len(difs), difs[0])))

    cab = ["Arquivo", "Versao", "N (REG)", "n final", "Tempo F1 (ms)", "Tempo F3 (ms)", "F1/F3",
           "Altura F1", "Altura F3", "Limite AVL", "Respeita", "Mem F1 (KiB)", "Mem F3 (KiB)"]
    md = ["**Tabela - Fase 1 (BST) x Fase 3 (AVL + indice por linha), mesmos arquivos de carga. "
          "Tempos em milissegundos (mediana de %d execucoes, so as operacoes); altura em niveis; "
          "memoria em KiB (tracemalloc, apos aplicar os REG/REM; so as arvores). "
          "Limite AVL = 1,45 x log2(n + 2), com n = nos ao final.**" % args.execucoes, "",
          "| " + " | ".join(cab) + " |", "|" + "|".join(["---"] * len(cab)) + "|"]
    csv = [";".join(cab)]
    for r in linhas:
        cel = [r["nome"], r["versao"], str(r["n_reg"]), str(r["n_final"]),
               "%.3f" % r["t1"], "%.3f" % r["t3"], "%.2f" % (r["t1"] / r["t3"] if r["t3"] else float("nan")),
               str(r["h1"]), str(r["h3"]), "%.2f" % r["limite"], "SIM" if r["ok"] else "NAO",
               "%.1f" % r["mem1"], "%.1f" % r["mem3"]]
        md.append("| " + " | ".join(cel) + " |")
        csv.append(";".join(cel))

    os.makedirs(args.saida, exist_ok=True)
    caminho_md = os.path.join(args.saida, "resultados_fase3.md")
    caminho_csv = os.path.join(args.saida, "resultados_fase3.csv")
    with open(caminho_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    with open(caminho_csv, "w", encoding="utf-8-sig") as f:
        f.write("\n".join(csv) + "\n")

    print("\n" + "\n".join(md))
    print("\nAltura final da AVL respeita o limite em todos os arquivos: %s"
          % ("SIM" if all(r["ok"] for r in linhas) else "NAO"))
    print("Respostas da Fase 1 e da Fase 3 iguais em todos os arquivos: %s"
          % ("SIM" if all(r["iguais"] for r in linhas) else "NAO"))
    print("Arquivos gerados: %s | %s" % (caminho_md, caminho_csv))
    return 0


# ------------------------------------------------------------------ --rotacoes
def desenhar(no, nivel=0, linhas=None):
    """Desenha a arvore de lado (raiz a esquerda, filho da direita em cima)."""
    if linhas is None:
        linhas = []
    if no is not None:
        desenhar(no.direita, nivel + 1, linhas)
        linhas.append("    " * nivel + "%s %s %s  (h=%d)" % (no.chave + (no.h,)))
        desenhar(no.esquerda, nivel + 1, linhas)
    return linhas


def rotacoes(args):
    ops = ler_operacoes(args.rotacoes)
    arvore = carregar(args.fase3).ArvoreChegadas()
    avl = arvore.por_tempo
    contagem = 0
    for i, (comando, a) in enumerate(ops, 1):
        if comando not in ("REG", "REM") or len(a) < 3:
            continue
        antes = desenhar(avl.raiz)
        avl.log_rotacoes = []
        if comando == "REG":
            arvore.registrar_chegada(a[0], a[1], a[2])
        else:
            arvore.remover_chegada(a[0], a[1], a[2])
        if avl.log_rotacoes:
            contagem += 1
            print("=" * 70)
            print("Operacao %d: %s  ->  %d rotacao(oes)" % (i, " ".join([comando] + a), len(avl.log_rotacoes)))
            for tipo, chave in avl.log_rotacoes:
                print("   rotacao %s no no %s %s %s" % ((tipo,) + chave))
            print("\n--- ANTES (arvore principal, de lado) ---")
            print("\n".join(antes) if antes else "(vazia)")
            print("\n--- DEPOIS ---")
            print("\n".join(desenhar(avl.raiz)))
    avl.log_rotacoes = None
    print("\nTotal: %d operacoes provocaram rotacao | rotacoes simples: %d | duplas: %d | altura final: %d"
          % (contagem, avl.rot_simples, avl.rot_duplas, avl.altura()))
    return 0


def main():
    p = argparse.ArgumentParser(description="Fase 3: validacao e comparacao Fase 1 x Fase 3")
    p.add_argument("--validar", action="store_true", help="compara pequeno.txt com o gabarito da Fase 3")
    p.add_argument("--rotacoes", metavar="ARQUIVO", help="mostra as rotacoes da AVL ao processar o arquivo")
    p.add_argument("--execucoes", type=int, default=5, help="execucoes por arquivo (padrao 5)")
    p.add_argument("--pasta", default="dados_teste", help="pasta dos arquivos de carga (padrao: dados_teste)")
    p.add_argument("--saida", default=".", help="pasta de saida (padrao: a atual)")
    p.add_argument("--fase1", default=os.path.join(AQUI, "main.py"), help="programa da Fase 1")
    p.add_argument("--fase3", default=os.path.join(AQUI, "fase3", "sistema.py"), help="programa da Fase 3")
    args = p.parse_args()

    if args.validar:
        return validar(args)
    if args.rotacoes:
        return rotacoes(args)
    return tabela(args)


if __name__ == "__main__":
    sys.exit(main())
