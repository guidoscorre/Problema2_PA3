#!/usr/bin/env python3
"""
Fase 2 - medicoes e validacao (codigo de TESTE).

Pode usar estruturas prontas da linguagem: a regra do enunciado vale apenas para
o nucleo (main.py), que este arquivo nunca importa para executar operacoes.

Uso:
    python medicoes_fase2.py                 # tabela da Fase 2 (5 execucoes por carga)
    python medicoes_fase2.py --validar       # confere pequeno.txt com o gabarito da Fase 1
    python medicoes_fase2.py --memoria       # inclui memoria (tracemalloc, so REG)
    python medicoes_fase2.py --execucoes 5 --pasta . --saida resultados

A medicao roda o comando oficial (python main.py ARQUIVO) e le o TEMPO_MS que o
programa escreve na saida de erro. N e o numero de comandos REG do arquivo.
"""
import argparse
import glob
import math
import os
import re
import statistics
import subprocess
import sys
import tracemalloc

AQUI = os.path.dirname(os.path.abspath(__file__))
PROGRAMA = os.path.join(AQUI, "main.py")


# --------------------------------------------------------------------- leitura
def ler_operacoes(caminho):
    ops = []
    with open(caminho, encoding="utf-8-sig") as arquivo:
        for bruta in arquivo:
            linha = bruta.strip()
            if not linha or linha.startswith("#"):
                continue
            partes = linha.split()
            ops.append((partes[0].upper(), partes[1:]))
    return ops


def contar_reg(ops):
    return sum(1 for comando, args in ops if comando == "REG" and len(args) >= 3)


PALAVRAS_EMBARALHADA = ("embaralh", "aleat", "shuffle", "random", "backup", "fora")
PALAVRAS_ORDEM = ("ordem", "quase", "ordenad", "sorted", "order", "seq")


def classificar_versao(nome, ops):
    minusculo = nome.lower()
    if any(p in minusculo for p in PALAVRAS_EMBARALHADA):
        return "Embaralhada"
    if any(p in minusculo for p in PALAVRAS_ORDEM):
        return "Quase em ordem"
    # Sem pista no nome: mede a desordem pela fracao de REG que "volta" no tempo.
    quedas = 0
    total = 0
    anterior = None
    for comando, args in ops:
        if comando != "REG" or len(args) < 3:
            continue
        chave = (args[0], args[1], args[2])
        if anterior is not None and chave < anterior:
            quedas += 1
        anterior = chave
        total += 1
    return "Embaralhada" if quedas > 0.25 * max(1, total) else "Quase em ordem"


def descobrir_cargas(pasta):
    """Cargas sao arquivos com pelo menos 500 comandos REG (podem ter consultas)."""
    cargas = []
    for caminho in sorted(glob.glob(os.path.join(pasta, "*.txt"))):
        nome = os.path.basename(caminho)
        if "esperado" in nome.lower():
            continue
        try:
            ops = ler_operacoes(caminho)
        except (OSError, UnicodeDecodeError):
            continue
        n_reg = contar_reg(ops)
        if n_reg >= 500:
            cargas.append({
                "nome": nome,
                "caminho": caminho,
                "ops": ops,
                "n": n_reg,
                "versao": classificar_versao(nome, ops),
            })
    cargas.sort(key=lambda c: (c["n"], c["versao"]))
    return cargas


# --------------------------------------------------------------------- execucao oficial
def rodar_comando(caminho):
    resultado = subprocess.run(
        [sys.executable, PROGRAMA, caminho],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=900,
    )
    if resultado.returncode != 0:
        raise RuntimeError(
            "codigo de saida %d; stderr: %s"
            % (resultado.returncode, resultado.stderr.strip()[-400:])
        )

    encontrado = re.search(r"TEMPO_MS\s+([0-9]+\.[0-9]{3})", resultado.stderr)
    if not encontrado:
        raise RuntimeError("saida de erro sem a linha TEMPO_MS")

    linhas = [x.strip() for x in resultado.stdout.splitlines() if x.strip()]
    if not linhas:
        raise RuntimeError("saida padrao vazia")
    try:
        altura = int(linhas[-1])
    except ValueError:
        raise RuntimeError("a ultima resposta nao e um ALT (numero inteiro)")

    return float(encontrado.group(1)), altura


def medir_memoria(ops):
    """Memoria da arvore ao final, inserindo apenas os REG (tracemalloc)."""
    import importlib.util

    especificacao = importlib.util.spec_from_file_location("main_do_projeto", PROGRAMA)
    modulo = importlib.util.module_from_spec(especificacao)
    especificacao.loader.exec_module(modulo)

    arvore = modulo.ArvoreChegadas()
    tracemalloc.start()
    for comando, args in ops:
        if comando == "REG" and len(args) >= 3:
            arvore.registrar_chegada(args[0], args[1], args[2])
    atual, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return atual / 1024.0, pico / 1024.0


# --------------------------------------------------------------------- validacao
def validar(pasta):
    arquivo_ops = os.path.join(pasta, "pequeno.txt")
    arquivo_esperado = os.path.join(pasta, "pequeno_esperado_fase1.txt")
    if not os.path.exists(arquivo_ops) or not os.path.exists(arquivo_esperado):
        print("[ERRO] pequeno.txt ou pequeno_esperado_fase1.txt nao encontrado em: %s" % pasta)
        return 2

    resultado = subprocess.run(
        [sys.executable, PROGRAMA, arquivo_ops],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=300,
    )
    obtido = resultado.stdout.splitlines()
    with open(arquivo_esperado, encoding="utf-8-sig") as arquivo:
        esperado = arquivo.read().splitlines()
    while esperado and not esperado[-1].strip():
        esperado.pop()

    diferencas = []
    for i in range(max(len(obtido), len(esperado))):
        o = obtido[i] if i < len(obtido) else "<faltando>"
        e = esperado[i] if i < len(esperado) else "<faltando>"
        if o.strip() != e.strip():
            diferencas.append((i + 1, o, e))

    tempo = re.search(r"TEMPO_MS\s+([0-9]+\.[0-9]{3})", resultado.stderr)
    print("Operacoes : %s" % arquivo_ops)
    print("Esperado  : %s" % arquivo_esperado)
    print("Tempo das operacoes: %s ms | linhas obtidas: %d | esperadas: %d"
          % (tempo.group(1) if tempo else "?", len(obtido), len(esperado)))

    if not diferencas:
        print("SUCESSO! A saida e identica ao gabarito da Fase 1.")
        return 0

    print("FALHA! %d linha(s) diferente(s). Primeiras 15:" % len(diferencas))
    print("%6s | %-30s | esperado" % ("linha", "obtido"))
    for n, o, e in diferencas[:15]:
        print("%6d | %-30s | %s" % (n, o, e))
    return 1


# --------------------------------------------------------------------- tabela
def escrever_tabela(linhas, execucoes, saida, com_memoria):
    cabecalho = ["Arquivo", "N (REG)", "Versao", "Mediana (ms)", "Minimo (ms)",
                 "Maximo (ms)", "Altura final"]
    if com_memoria:
        cabecalho += ["Memoria final (KiB)", "Pico (KiB)"]

    titulo = (
        "**Tabela 1 - Fase 2: arvore binaria de busca sem balanceamento. "
        "Tempos em milissegundos, mediana de %d execucoes, medindo apenas as operacoes "
        "(sem leitura do arquivo). Altura final em numero de niveis. "
        "N e o numero de comandos REG.**" % execucoes
    )

    md = [titulo, "", "| " + " | ".join(cabecalho) + " |",
          "|" + "|".join(["---"] * len(cabecalho)) + "|"]
    csv = [";".join(cabecalho)]

    for linha in linhas:
        celulas = [
            linha["nome"],
            str(linha["n"]),
            linha["versao"],
            "%.3f" % linha["mediana"],
            "%.3f" % linha["minimo"],
            "%.3f" % linha["maximo"],
            str(linha["altura"]),
        ]
        if com_memoria:
            celulas += ["%.1f" % linha["mem_kib"], "%.1f" % linha["mem_pico_kib"]]
        md.append("| " + " | ".join(celulas) + " |")
        csv.append(";".join(celulas))

    caminho_md = os.path.join(saida, "resultados_fase2.md")
    caminho_csv = os.path.join(saida, "resultados_fase2.csv")
    with open(caminho_md, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(md) + "\n")
    with open(caminho_csv, "w", encoding="utf-8-sig") as arquivo:
        arquivo.write("\n".join(csv) + "\n")
    return caminho_md, caminho_csv


def relatar_razoes(linhas):
    print("\nRazoes entre o menor e o maior N (pergunta (a)):")
    for versao in ("Quase em ordem", "Embaralhada"):
        grupo = [l for l in linhas if l["versao"] == versao]
        if len(grupo) < 2:
            continue
        inicio, fim = grupo[0], grupo[-1]
        razao_n = fim["n"] / inicio["n"]
        razao_t = fim["mediana"] / inicio["mediana"] if inicio["mediana"] > 0 else float("nan")
        razao_h = fim["altura"] / inicio["altura"]
        referencia_n2 = razao_n ** 2
        referencia_nlogn = (
            fim["n"] * math.log2(fim["n"]) / (inicio["n"] * math.log2(inicio["n"]))
        )
        print("  %-14s N x%.0f | tempo x%.2f | altura %d -> %d (x%.2f)"
              % (versao, razao_n, razao_t, inicio["altura"], fim["altura"], razao_h))
        print("                 referencias: N^2 = x%.0f | N*log2(N) = x%.1f"
              % (referencia_n2, referencia_nlogn))


def main():
    parser = argparse.ArgumentParser(description="Medicoes da Fase 2 e validacao")
    parser.add_argument("--validar", action="store_true", help="compara pequeno.txt com o gabarito")
    parser.add_argument("--memoria", action="store_true", help="mede memoria com tracemalloc")
    parser.add_argument("--execucoes", type=int, default=5, help="execucoes por arquivo (padrao 5)")
    parser.add_argument("--pasta", default=AQUI, help="pasta dos arquivos (padrao: a do script)")
    parser.add_argument("--saida", default=AQUI, help="pasta de saida (padrao: a do script)")
    args = parser.parse_args()

    if args.validar:
        return validar(args.pasta)

    cargas = descobrir_cargas(args.pasta)
    if not cargas:
        print("[ERRO] Nenhuma carga (arquivo com 500+ REG) encontrada em: %s" % args.pasta)
        return 2

    print("Cargas encontradas:")
    for carga in cargas:
        print("  %-32s N=%-6d %s" % (carga["nome"], carga["n"], carga["versao"]))
    print("\n%d execucoes por arquivo (mediana).\n" % args.execucoes)

    linhas = []
    for carga in cargas:
        tempos = []
        altura = None
        falha = None
        for repeticao in range(args.execucoes):
            try:
                tempo, altura = rodar_comando(carga["caminho"])
            except Exception as erro:
                falha = "%s: %s" % (type(erro).__name__, erro)
                break
            tempos.append(tempo)
            print("  %-32s %d/%d: %9.3f ms" % (carga["nome"], repeticao + 1, args.execucoes, tempo))

        if falha:
            print("  [FALHA] %s\n" % falha)
            continue

        linha = {
            "nome": carga["nome"],
            "n": carga["n"],
            "versao": carga["versao"],
            "mediana": statistics.median(tempos),
            "minimo": min(tempos),
            "maximo": max(tempos),
            "altura": altura,
        }
        if args.memoria:
            atual, pico = medir_memoria(carga["ops"])
            linha["mem_kib"] = atual
            linha["mem_pico_kib"] = pico
        linhas.append(linha)
        print("  -> mediana %.3f ms | altura %d\n" % (linha["mediana"], altura))

    os.makedirs(args.saida, exist_ok=True)
    caminho_md, caminho_csv = escrever_tabela(linhas, args.execucoes, args.saida, args.memoria)

    with open(caminho_md, encoding="utf-8") as arquivo:
        print("\n" + arquivo.read())
    relatar_razoes(linhas)
    print("\nArquivos gerados: %s | %s" % (caminho_md, caminho_csv))
    return 0


if __name__ == "__main__":
    sys.exit(main())
