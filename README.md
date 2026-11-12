# Problema 2 – A que horas passa o próximo ônibus?

Projeto Aplicado 3 – UnDF.
Grupo: Arthur Ornellas Lira, Guilherme de Castro e Iranetes Lopes

O sistema guarda cada chegada de ônibus informada (data, horário e linha) e responde às operações R1 a R8.
A Fase 1 usa uma árvore binária de busca (BST); a Fase 3 usa uma árvore AVL.

## Linguagem e versão

- Python 3.13.3
- Usa apenas a biblioteca padrão. Não é preciso instalar nada nem compilar.

## Estrutura do repositório

```
main.py                     Fase 1: árvore binária de busca (BST)
Fase3/sistema.py            Fase 3: AVL + índice por linha para R4 e R8
medicoes_fase2.py           Fase 2: tabela de medições e validação da Fase 1 (código de teste)
medicoes_fase3.py           Fase 3: validação, comparação Fase 1 x Fase 3 e rotações (código de teste)
dados_teste/                arquivos da professora: pequeno.txt, gabaritos e arquivos de carga
executar.txt                comandos que executam a Fase 1 e a Fase 3
arvore_7_ordenadas.svg      ilustração do relatório: árvore da Fase 1 com chegadas em ordem
arvore_7_pequeno.svg        ilustração do relatório: árvore da Fase 1 com as 7 primeiras chegadas do pequeno.txt
```

## Como executar

Os comandos abaixo são os do `executar.txt`. Rodam a partir da raiz do repositório.
`{arquivo}` é o arquivo de operações; nos exemplos, usamos o `pequeno.txt`.

```
python main.py dados_teste/pequeno.txt              # Fase 1 (BST)
python Fase3/sistema.py dados_teste/pequeno.txt     # Fase 3 (AVL)
```

As respostas saem na saída padrão. O tempo gasto só com as operações sai na saída de erro, na linha `TEMPO_MS valor`.

## Validação

```
python medicoes_fase2.py --validar --pasta dados_teste    # Fase 1 x pequeno_esperado_fase1.txt
python medicoes_fase3.py --validar --pasta dados_teste    # Fase 3 x pequeno_esperado_fase3.txt
```

Na Fase 3, os `ALT` depois da primeira remoção bem-sucedida não são comparados.
## Tabelas e ilustrações do relatório

Cada item abaixo é reproduzido com o comando indicado, a partir da raiz do repositório.
Cada arquivo de carga é executado 5 vezes e a tabela mostra a mediana.

| Item do relatório | Comando | Arquivos gerados |
|---|---|---|
| Tabela da Fase 2 (mediana do tempo, altura e razões entre N = 1.000 e N = 20.000) | `python medicoes_fase2.py --pasta dados_teste --memoria` | `resultados_fase2.md` e `.csv` |
| Tabela comparativa Fase 1 x Fase 3 (tempo, altura e memória) e verificação do limite 1,45 × log₂(n + 2) | `python medicoes_fase3.py --pasta dados_teste` | `resultados_fase3.md` e `.csv` |
| Rotações que a AVL faz ao processar o `pequeno.txt` (ilustração) | `python medicoes_fase3.py --rotacoes dados_teste/pequeno.txt` | só na tela |
| Custo de R4 e R8 conforme os registros crescem (item 3.2) | python experimento_r4_r8.py dados_teste/carga_embaralhada_20000.txt | só na tela |
| Árvore da Fase 1 após as 7 primeiras chegadas (ilustração) |As figuras do relatório foram desenhadas no draw.io(https://app.diagrams.net) e exportadas em formato SVG| `arvore_7_*.svg` |

Os tempos mudam um pouco de máquina para máquina; as alturas e as respostas são sempre as mesmas.

## Resumo das decisões de projeto

- **Chave da árvore principal:** a tupla `(data, horário, linha)`. Data e horário têm tamanho fixo, então comparar os textos equivale a comparar os instantes; a linha desempata, caractere a caractere.
- **Remoção na AVL (3.1):** remoção de verdade. Um nó com dois filhos é trocado pelo sucessor (como na Fase 1), e o caminho até a raiz é rebalanceado. Custo O(log n) no pior caso.
- **R4 e R8 (3.2):** uma segunda AVL, com chave `(linha, data, horário)`, serve de índice. Todo `REG` e todo `REM` atualizam as duas árvores. R4 e R8 passam a custar O(log n) por consulta, à custa de cerca de o dobro de memória.
- **R7:** cada nó guarda a própria altura, então a resposta é lida na raiz em O(1).
