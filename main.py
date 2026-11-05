import sys
import time
from datetime import datetime, timedelta


class No:
    __slots__ = ("data", "horario", "linha", "chave", "esquerda", "direita")

    def __init__(self, data, horario, linha):
        self.data = data
        self.horario = horario
        self.linha = linha
        self.chave = (data, horario, linha)
        self.esquerda = None
        self.direita = None


class ArvoreChegadas:
    def __init__(self):
        self.raiz = None

    # R1
    def registrar_chegada(self, data, horario, linha):
        chave = (data, horario, linha)
        if self.raiz is None:
            self.raiz = No(data, horario, linha)
            return "OK"

        atual = self.raiz
        while True:
            if chave == atual.chave:
                return "DUPLICADO"
            if chave < atual.chave:
                if atual.esquerda is None:
                    atual.esquerda = No(data, horario, linha)
                    return "OK"
                atual = atual.esquerda
            else:
                if atual.direita is None:
                    atual.direita = No(data, horario, linha)
                    return "OK"
                atual = atual.direita

    # R2
    def buscar_chegada(self, data, horario, linha):
        chave = (data, horario, linha)
        atual = self.raiz
        while atual is not None:
            if chave == atual.chave:
                return "ACHOU"
            atual = atual.esquerda if chave < atual.chave else atual.direita
        return "NAO"

    def _pilha_a_partir_de(self, chave):
        pilha = []
        atual = self.raiz
        while atual is not None:
            if chave <= atual.chave:
                pilha.append(atual)
                atual = atual.esquerda
            else:
                atual = atual.direita
        return pilha

    def _em_ordem_a_partir_de(self, chave):
        pilha = self._pilha_a_partir_de(chave)
        while pilha:
            no = pilha.pop()
            yield no
            atual = no.direita
            while atual is not None:
                pilha.append(atual)
                atual = atual.esquerda

    # R3
    def proximo(self, data, horario):
        pilha = self._pilha_a_partir_de((data, horario, ""))
        if not pilha:
            return "NENHUM"
        no = pilha[-1]
        return "%s %s %s" % (no.data, no.horario, no.linha)

    # R4
    def proximo_da_linha(self, data, horario, linha):
        for no in self._em_ordem_a_partir_de((data, horario, "")):
            if no.linha == linha:
                return "%s %s" % (no.data, no.horario)
        return "NENHUM"

    # R5
    def entre(self, data1, horario1, data2, horario2):
        if (data1, horario1) > (data2, horario2):
            return "0"

        inicio = (data1, horario1)
        fim = (data2, horario2)
        achados = []
        for no in self._em_ordem_a_partir_de((data1, horario1, "")):
            instante = (no.data, no.horario)
            if instante > fim:
                break
            if instante >= inicio:
                achados.append("%s %s %s" % (no.data, no.horario, no.linha))

        return "\n".join([str(len(achados))] + achados)

    # R6
    def remover_chegada(self, data, horario, linha):
        chave = (data, horario, linha)
        pai = None
        atual = self.raiz
        while atual is not None and atual.chave != chave:
            pai = atual
            atual = atual.esquerda if chave < atual.chave else atual.direita

        if atual is None:
            return "NAO"

        if atual.esquerda is not None and atual.direita is not None:
            # Dois filhos: substitui pelo sucessor.
            pai_sucessor = atual
            sucessor = atual.direita
            while sucessor.esquerda is not None:
                pai_sucessor = sucessor
                sucessor = sucessor.esquerda

            atual.data = sucessor.data
            atual.horario = sucessor.horario
            atual.linha = sucessor.linha
            atual.chave = sucessor.chave

            if pai_sucessor is atual:
                pai_sucessor.direita = sucessor.direita
            else:
                pai_sucessor.esquerda = sucessor.direita
            return "OK"

        filho = atual.esquerda if atual.esquerda is not None else atual.direita
        if pai is None:
            self.raiz = filho
        elif pai.esquerda is atual:
            pai.esquerda = filho
        else:
            pai.direita = filho
        return "OK"

    # R7
    def altura(self):
        if self.raiz is None:
            return 0

        maior = 0
        pilha = [(self.raiz, 1)]
        while pilha:
            no, profundidade = pilha.pop()
            if profundidade > maior:
                maior = profundidade
            if no.esquerda is not None:
                pilha.append((no.esquerda, profundidade + 1))
            if no.direita is not None:
                pilha.append((no.direita, profundidade + 1))
        return maior

    # R8
    def espera_semanal(self, linha, data, horario, k):
        k = int(k)
        base = datetime.strptime(data + " " + horario, "%Y-%m-%d %H:%M:%S")

        linhas = []
        for semanas_atras in range(k - 1, -1, -1):
            instante = base - timedelta(weeks=semanas_atras)
            dia = instante.strftime("%Y-%m-%d")
            hora = instante.strftime("%H:%M:%S")

            espera = None
            for no in self._em_ordem_a_partir_de((dia, hora, "")):
                if no.data != dia:
                    break
                if no.linha == linha:
                    chegada = datetime.strptime(
                        no.data + " " + no.horario, "%Y-%m-%d %H:%M:%S"
                    )
                    espera = int((chegada - instante).total_seconds())
                    break

            if espera is None:
                linhas.append(dia + " NAOPASSOU")
            else:
                linhas.append(dia + " " + str(espera))

        return "\n".join(linhas)


def ler_operacoes(caminho):
    operacoes = []
    with open(caminho, encoding="utf-8") as arquivo:
        for bruta in arquivo:
            linha = bruta.strip()
            if not linha or linha.startswith("#"):
                continue
            operacoes.append(linha.split())
    return operacoes


def executar(operacoes):
    arvore = ArvoreChegadas()
    respostas = []

    inicio = time.perf_counter()
    for partes in operacoes:
        comando = partes[0].upper()
        if comando == "REG":
            respostas.append(arvore.registrar_chegada(partes[1], partes[2], partes[3]))
        elif comando == "BUSCA":
            respostas.append(arvore.buscar_chegada(partes[1], partes[2], partes[3]))
        elif comando == "PROX":
            respostas.append(arvore.proximo(partes[1], partes[2]))
        elif comando == "PROXL":
            respostas.append(arvore.proximo_da_linha(partes[1], partes[2], partes[3]))
        elif comando == "ENTRE":
            respostas.append(arvore.entre(partes[1], partes[2], partes[3], partes[4]))
        elif comando == "REM":
            respostas.append(arvore.remover_chegada(partes[1], partes[2], partes[3]))
        elif comando == "ALT":
            respostas.append(str(arvore.altura()))
        elif comando == "SEMANA":
            respostas.append(
                arvore.espera_semanal(partes[1], partes[2], partes[3], partes[4])
            )
    milissegundos = (time.perf_counter() - inicio) * 1000.0
    return respostas, milissegundos


def main():
    if len(sys.argv) != 2:
        sys.stderr.write("uso: python main.py <arquivo_de_operacoes>\n")
        return 2

    operacoes = ler_operacoes(sys.argv[1])

    # Aquecimento fora da medicao: o primeiro strptime carrega o modulo _strptime.
    datetime.strptime("2000-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")

    respostas, milissegundos = executar(operacoes)
    respostas = [r for r in respostas if r != ""]

    sys.stdout.write("\n".join(respostas))
    if respostas:
        sys.stdout.write("\n")
    sys.stderr.write("TEMPO_MS %.3f\n" % milissegundos)
    return 0


if __name__ == "__main__":
    sys.exit(main())
