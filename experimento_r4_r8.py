

# Uso: python experimento_r4_r8.py dados_teste/carga_embaralhada_20000.txt

import importlib.util
import os
import random
import sys
from datetime import datetime, timedelta

FORMATO = "%Y-%m-%d %H:%M:%S"
TAMANHOS = (1000, 2500, 5000, 10000, 20000)
CONSULTAS = 300
K = 4

AQUI = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("fase3", os.path.join(AQUI, "Fase3", "sistema.py"))
fase3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fase3)


def ler_chegadas(caminho):
    chegadas = []
    with open(caminho, encoding="utf-8-sig") as f:
        for bruta in f:
            p = bruta.split()
            if p and p[0] == "REG":
                chegadas.append((p[1], p[2], p[3]))
    return sorted(set(chegadas))


def contar_descida(avl, chave):
    atual, melhor, vistos = avl.raiz, None, 0
    while atual is not None:
        vistos += 1
        if chave <= atual.chave:
            melhor = atual.chave
            atual = atual.esquerda
        else:
            atual = atual.direita
    return melhor, vistos


def contar_em_ordem(avl, chave, parar):
    pilha, atual, vistos = [], avl.raiz, 0
    while atual is not None:
        vistos += 1
        if chave <= atual.chave:
            pilha.append(atual)
            atual = atual.esquerda
        else:
            atual = atual.direita
    while pilha:
        no = pilha.pop()
        if parar(no.chave):
            return vistos
        atual = no.direita
        while atual is not None:
            vistos += 1
            pilha.append(atual)
            atual = atual.esquerda
    return vistos


def semanas(data, horario, k):
    base = datetime.strptime(data + " " + horario, FORMATO)
    for w in range(k):
        t = base - timedelta(weeks=w)
        yield t.strftime("%Y-%m-%d"), t.strftime("%H:%M:%S")


def r4_uma_arvore(por_tempo, data, horario, linha):
    return contar_em_ordem(por_tempo, (data, horario, ""), lambda c: c[2] == linha)


def r8_uma_arvore(por_tempo, linha, data, horario, k):
    total = 0
    for dia, hora in semanas(data, horario, k):
        total += contar_em_ordem(por_tempo, (dia, hora, ""),
                                 lambda c, dia=dia: c[0] != dia or c[2] == linha)
    return total


def r4_indice(por_linha, data, horario, linha):
    return contar_descida(por_linha, (linha, data, horario))[1]


def r8_indice(por_linha, linha, data, horario, k):
    return sum(contar_descida(por_linha, (linha, dia, hora))[1]
               for dia, hora in semanas(data, horario, k))


def main():
    if len(sys.argv) != 2:
        print("uso: python experimento_r4_r8.py ARQUIVO_DE_CARGA")
        return 2
    chegadas = ler_chegadas(sys.argv[1])
    linhas = sorted({c[2] for c in chegadas})
    rng = random.Random(42)

    print("Nos visitados em media por consulta (%d consultas sorteadas por tamanho)\n" % CONSULTAS)
    cab = ("n", "periodo", "R4 1 arv.", "R4 indice", "R4 pior 1 arv.", "R4 pior indice",
           "R8 1 arv.", "R8 indice")
    print("%-6s | %-23s | %9s | %9s | %14s | %14s | %9s | %9s" % cab)
    print("-" * 112)

    for n in TAMANHOS:
        n = min(n, len(chegadas))
        prefixo = chegadas[:n]
        por_tempo, por_linha = fase3.ArvoreAVL(), fase3.ArvoreAVL()
        for d, h, l in prefixo:
            por_tempo.inserir((d, h, l))
            por_linha.inserir((l, d, h))
        dias = sorted({c[0] for c in prefixo})

        s4a = s4b = s8a = s8b = 0
        for _ in range(CONSULTAS):
            dia = rng.choice(dias)
            hora = "%02d:%02d:00" % (rng.randrange(6, 23), rng.randrange(60))
            linha = rng.choice(linhas)
            s4a += r4_uma_arvore(por_tempo, dia, hora, linha)
            s4b += r4_indice(por_linha, dia, hora, linha)
            s8a += r8_uma_arvore(por_tempo, linha, dia, hora, K)
            s8b += r8_indice(por_linha, linha, dia, hora, K)

        pior_a = r4_uma_arvore(por_tempo, dias[0], "00:00:00", "LINHAFIM")
        pior_b = r4_indice(por_linha, dias[0], "00:00:00", "LINHAFIM")

        print("%-6d | %s a %s | %9.1f | %9.1f | %14d | %14d | %9.1f | %9.1f" % (
            n, dias[0], dias[-1], s4a / CONSULTAS, s4b / CONSULTAS, pior_a, pior_b,
            s8a / CONSULTAS, s8b / CONSULTAS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
