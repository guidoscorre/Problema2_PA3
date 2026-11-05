import sys
import time
from main import ArvoreChegadas


def main():
    if len(sys.argv) < 2:
        print("Uso: python sistema.py arquivo_de_operacoes.txt [--altura]", file=sys.stderr)
        return 1

    caminho = sys.argv[1]                       # o endereço do arquivo vem do terminal
    mostrar_altura = "--altura" in sys.argv     # opção extra, usada na Fase 2

    # lê o arquivo inteiro ANTES de executar
    # utf-8-sig ignora o BOM que o Windows às vezes adiciona no início do arquivo
    with open(caminho, encoding="utf-8-sig") as f:
        linhas = f.read().splitlines()

    # parse ANTES do cronômetro: o tempo medido é só das operações,
    # como o enunciado exige
    operacoes = []
    for linha in linhas:
        linha = linha.strip()
        if linha == "" or linha.startswith("#"):
            continue
        operacoes.append(linha.split())

    arvore = ArvoreChegadas()
    respostas = []

    inicio = time.perf_counter()
    for p in operacoes:
        cmd = p[0]

        if cmd == "REG":
            respostas.append(arvore.registrar_chegada(p[1], p[2], p[3]))
        elif cmd == "BUSCA":
            respostas.append(arvore.buscar_chegada(p[1], p[2], p[3]))
        elif cmd == "PROX":
            respostas.append(arvore.proximo(p[1], p[2]))
        elif cmd == "PROXL":
            respostas.append(arvore.proximo_da_linha(p[1], p[2], p[3]))
        elif cmd == "ENTRE":
            respostas.append(arvore.entre(p[1], p[2], p[3], p[4]))
        elif cmd == "REM":
            respostas.append(arvore.remover_chegada(p[1], p[2], p[3]))
        elif cmd == "ALT":
            respostas.append(str(arvore.altura()))   # altura() devolve int: precisa de str()
        elif cmd == "SEMANA":
            respostas.append(arvore.espera_semanal(p[1], p[2], p[3], p[4]))
    fim = time.perf_counter()

    print("\n".join(respostas))
    print(f"TEMPO_MS {(fim - inicio) * 1000:.3f}", file=sys.stderr)
    if mostrar_altura:
        print(f"ALTURA_FINAL {arvore.altura()}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
