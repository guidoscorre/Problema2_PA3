"""
Fase 3 - Arvore AVL feita do zero + indice por linha para R4 e R8.

O sistema usa DUAS arvores AVL, as duas da mesma classe ArvoreAVL:

  por_tempo : chave (data, horario, linha)  -> a arvore principal (R1, R2, R3, R5, R6, R7)
  por_linha : chave (linha, data, horario)  -> indice auxiliar (R4 e R8)

Toda insercao e toda remocao e feita nas DUAS, para nenhuma ficar desatualizada.

Uso:  python fase3/sistema.py ARQUIVO_DE_OPERACOES
"""
import sys
import time
from datetime import datetime, timedelta


# ======================================================================
#  AVL: arvore binaria de busca que se mantem balanceada sozinha
# ======================================================================

class NoAVL:
    __slots__ = ("chave", "esquerda", "direita", "h")

    def __init__(self, chave):
        self.chave = chave
        self.esquerda = None
        self.direita = None
        self.h = 1          # altura do no: uma folha tem h = 1 (arvore vazia = 0)


def altura_de(no):
    """Altura de uma subarvore; a subarvore vazia (None) tem altura 0."""
    return no.h if no is not None else 0


def atualizar_altura(no):
    """Recalcula no.h olhando a altura dos dois filhos."""
    he = no.esquerda.h if no.esquerda is not None else 0
    hd = no.direita.h if no.direita is not None else 0
    no.h = (he if he > hd else hd) + 1


def rotacao_direita(no):
    """
    Rotacao simples a direita (o filho da esquerda sobe):

            no                 filho
           /  \\               /    \\
       filho   C    -->      A      no
       /   \\                        /  \\
      A     B                      B    C

    A ordem das chaves continua a mesma: A < filho < B < no < C.
    """
    filho = no.esquerda
    no.esquerda = filho.direita
    filho.direita = no
    atualizar_altura(no)        # 'no' desceu: atualiza primeiro ele...
    atualizar_altura(filho)     # ...e depois o 'filho', que agora e o topo
    return filho                # quem chamou liga este novo topo ao pai


def rotacao_esquerda(no):
    """Rotacao simples a esquerda (o filho da direita sobe): espelho da anterior."""
    filho = no.direita
    no.direita = filho.esquerda
    filho.esquerda = no
    atualizar_altura(no)
    atualizar_altura(filho)
    return filho


class ArvoreAVL:
    def __init__(self):
        self.raiz = None
        self.tamanho = 0            # quantidade de nos
        self.rot_simples = 0        # contadores, so para medir/relatar
        self.rot_duplas = 0
        self.log_rotacoes = None    # se for uma lista, cada rotacao e anotada nela (usado so nos testes)

    # ---------------------------------------------------------------- consultas
    def altura(self):
        return self.raiz.h if self.raiz is not None else 0

    def contem(self, chave):
        atual = self.raiz
        while atual is not None:
            c = atual.chave
            if chave == c:
                return True
            atual = atual.esquerda if chave < c else atual.direita
        return False

    def primeiro_a_partir_de(self, chave):
        """Menor chave que seja >= 'chave' (ou None se nao existir). Custo: uma descida, O(log n)."""
        atual = self.raiz
        melhor = None
        while atual is not None:
            if chave <= atual.chave:
                melhor = atual.chave        # candidata; pode haver uma menor ainda, entao vai a esquerda
                atual = atual.esquerda
            else:
                atual = atual.direita       # este no e pequeno demais: a resposta esta a direita
        return melhor

    def em_ordem_a_partir_de(self, chave):
        """Gera, em ordem crescente, todas as chaves >= 'chave' (sem recursao, usando uma pilha)."""
        pilha = []
        atual = self.raiz
        while atual is not None:
            if chave <= atual.chave:
                pilha.append(atual)
                atual = atual.esquerda
            else:
                atual = atual.direita
        while pilha:
            no = pilha.pop()
            yield no.chave
            atual = no.direita
            while atual is not None:
                pilha.append(atual)
                atual = atual.esquerda

    # ------------------------------------------------------------- balanceamento
    def _anotar(self, tipo, no):
        if self.log_rotacoes is not None:
            self.log_rotacoes.append((tipo, no.chave))

    def _rebalancear(self, no):
        """
        Recalcula a altura de 'no' e, se o fator de balanceamento (altura da esquerda
        menos altura da direita) sair de -1..+1, faz a rotacao certa.
        Devolve o no que ficou no topo desta subarvore (e o proprio 'no' se nao houve rotacao).
        """
        atualizar_altura(no)
        fator = altura_de(no.esquerda) - altura_de(no.direita)

        if fator > 1:                                   # pesado a esquerda
            filho = no.esquerda
            if altura_de(filho.esquerda) >= altura_de(filho.direita):
                self.rot_simples += 1                   # caso esquerda-esquerda
                self._anotar("simples a direita", no)
                return rotacao_direita(no)
            self.rot_duplas += 1                        # caso esquerda-direita
            self._anotar("dupla esquerda-direita", no)
            no.esquerda = rotacao_esquerda(filho)
            return rotacao_direita(no)

        if fator < -1:                                  # pesado a direita
            filho = no.direita
            if altura_de(filho.direita) >= altura_de(filho.esquerda):
                self.rot_simples += 1                   # caso direita-direita
                self._anotar("simples a esquerda", no)
                return rotacao_esquerda(no)
            self.rot_duplas += 1                        # caso direita-esquerda
            self._anotar("dupla direita-esquerda", no)
            no.direita = rotacao_direita(filho)
            return rotacao_esquerda(no)

        return no

    def _corrigir_caminho(self, caminho):
        """
        'caminho' e a lista de nos da raiz ate o pai do ponto que mudou.
        Sobe do fim para o comeco rebalanceando cada no. Se a altura de uma subarvore
        ficou igual a que era antes, os nos de cima nao sao afetados e podemos parar.
        """
        i = len(caminho) - 1
        while i >= 0:
            no = caminho[i]
            altura_antes = no.h
            topo = self._rebalancear(no)
            if topo is not no:                          # houve rotacao: liga o novo topo ao pai
                if i == 0:
                    self.raiz = topo
                else:
                    pai = caminho[i - 1]
                    if pai.esquerda is no:
                        pai.esquerda = topo
                    else:
                        pai.direita = topo
            if topo.h == altura_antes:
                break
            i -= 1

    # ---------------------------------------------------------------- insercao
    def inserir(self, chave):
        """Insere a chave. Devolve False (sem mexer na arvore) se ela ja existir."""
        caminho = []
        atual = self.raiz
        while atual is not None:
            c = atual.chave
            if chave == c:
                return False
            caminho.append(atual)
            atual = atual.esquerda if chave < c else atual.direita

        novo = NoAVL(chave)
        if not caminho:
            self.raiz = novo
        else:
            pai = caminho[-1]
            if chave < pai.chave:
                pai.esquerda = novo
            else:
                pai.direita = novo
        self.tamanho += 1
        self._corrigir_caminho(caminho)
        return True

    # ------------------------------------------------------------------ remocao
    def remover(self, chave):
        """
        Remove a chave. Devolve False se ela nao existir.
        No com dois filhos: troca pela chave do sucessor (menor da subarvore da direita),
        como pede o enunciado, e remove o no do sucessor. Depois rebalanceia o caminho.
        """
        caminho = []
        atual = self.raiz
        while atual is not None and atual.chave != chave:
            caminho.append(atual)
            atual = atual.esquerda if chave < atual.chave else atual.direita
        if atual is None:
            return False

        if atual.esquerda is not None and atual.direita is not None:
            caminho.append(atual)
            sucessor = atual.direita
            while sucessor.esquerda is not None:
                caminho.append(sucessor)
                sucessor = sucessor.esquerda
            atual.chave = sucessor.chave
            alvo = sucessor                             # este e o no que sai de fato
        else:
            alvo = atual

        filho = alvo.esquerda if alvo.esquerda is not None else alvo.direita
        if not caminho:
            self.raiz = filho
        else:
            pai = caminho[-1]
            if pai.esquerda is alvo:
                pai.esquerda = filho
            else:
                pai.direita = filho
        self.tamanho -= 1
        self._corrigir_caminho(caminho)
        return True


# ======================================================================
#  O SISTEMA: usa as duas arvores para responder R1 a R8
# ======================================================================

class ArvoreChegadas:
    def __init__(self):
        self.por_tempo = ArvoreAVL()    # chave (data, horario, linha): arvore principal, responde R7
        self.por_linha = ArvoreAVL()    # chave (linha, data, horario): indice de R4 e R8

    # R1
    def registrar_chegada(self, data, horario, linha):
        if not self.por_tempo.inserir((data, horario, linha)):
            return "DUPLICADO"
        self.por_linha.inserir((linha, data, horario))      # mantem o indice atualizado
        return "OK"

    # R2
    def buscar_chegada(self, data, horario, linha):
        if self.por_tempo.contem((data, horario, linha)):
            return "ACHOU"
        return "NAO"

    # R3  ("" e menor que qualquer linha, entao a busca comeca no primeiro onibus daquele instante)
    def proximo(self, data, horario):
        c = self.por_tempo.primeiro_a_partir_de((data, horario, ""))
        if c is None:
            return "NENHUM"
        return "%s %s %s" % c

    # R4  (c = (linha, data, horario); se a linha achada for outra, a nossa nao tem mais chegadas)
    def proximo_da_linha(self, data, horario, linha):
        c = self.por_linha.primeiro_a_partir_de((linha, data, horario))
        if c is None or c[0] != linha:
            return "NENHUM"
        return "%s %s" % (c[1], c[2])

    # R5
    def entre(self, data1, horario1, data2, horario2):
        if (data1, horario1) > (data2, horario2):
            return "0"
        fim = (data2, horario2)
        achados = []
        for c in self.por_tempo.em_ordem_a_partir_de((data1, horario1, "")):
            if (c[0], c[1]) > fim:
                break
            achados.append("%s %s %s" % c)
        return "\n".join([str(len(achados))] + achados)

    # R6
    def remover_chegada(self, data, horario, linha):
        if not self.por_tempo.remover((data, horario, linha)):
            return "NAO"
        self.por_linha.remover((linha, data, horario))      # mantem o indice atualizado
        return "OK"

    # R7  (a altura fica guardada na raiz: custo O(1))
    def altura(self):
        return self.por_tempo.altura()

    # R8  (uma consulta de R4 por semana, aceitando so chegada do MESMO dia)
    def espera_semanal(self, linha, data, horario, k):
        k = int(k)
        base = datetime.strptime(data + " " + horario, "%Y-%m-%d %H:%M:%S")

        linhas = []
        for semanas_atras in range(k - 1, -1, -1):
            instante = base - timedelta(weeks=semanas_atras)
            dia = instante.strftime("%Y-%m-%d")
            hora = instante.strftime("%H:%M:%S")

            c = self.por_linha.primeiro_a_partir_de((linha, dia, hora))
            if c is not None and c[0] == linha and c[1] == dia:
                chegada = datetime.strptime(c[1] + " " + c[2], "%Y-%m-%d %H:%M:%S")
                espera = int((chegada - instante).total_seconds())
                linhas.append(dia + " " + str(espera))
            else:
                linhas.append(dia + " NAOPASSOU")
        return "\n".join(linhas)


# ======================================================================
#  LEITURA DO ARQUIVO, EXECUCAO E SAIDA (mesmo formato da Fase 1)
# ======================================================================

def ler_operacoes(caminho):
    operacoes = []
    with open(caminho, encoding="utf-8-sig") as arquivo:    # utf-8-sig ignora o BOM do Windows
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
        sys.stderr.write("uso: python fase3/sistema.py <arquivo_de_operacoes>\n")
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
