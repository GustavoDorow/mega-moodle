# Mega Moodle

Aplicação desktop em Python e PySide6. A interface gráfica permite cadastrar
disciplinas, informar disponibilidade semanal e definir o limite de disciplinas.
O terminal mantém os dois primeiros casos de uso.

## Executar

Na pasta do projeto, com o `uv` instalado:

```bash
uv run mega-moodle
```

A interface de terminal usa os mesmos controllers e DAOs:

```bash
uv run mega-moodle-cli
```

Informe identificação, nome e perfil. Não há autenticação. Para recuperar as
disponibilidades de um estudante, use a mesma identificação ao abrir novamente.
O catálogo de disciplinas é compartilhado entre os administradores.

O SQLite cria `megamoodle.db` na pasta de onde o comando foi executado. Rode
sempre da pasta do projeto para usar o mesmo banco. Não é preciso instalar um
servidor de banco, nem adicionar dependências além das que o projeto já tinha.

## Organização

```text
src/mega_moodle/
├── main.py                         # Cria o banco, os DAOs e os controllers
├── views/
│   ├── gui.py                      # Telas PySide6
│   └── cli.py                      # Entrada e saída no terminal
├── controllers/
│   ├── cadastro_controller.py      # Abre o perfil e carrega os dados
│   ├── administrador_controller.py # Coordena o cadastro de disciplina
│   ├── estudante_controller.py     # Coordena disponibilidade e limite
│   └── resultado_operacao.py       # Sucesso, mensagem e limite para a tela
├── models/                         # Entidades, enums e regras de domínio
│   ├── administrador.py
│   ├── estudante.py
│   ├── disciplina.py
│   ├── disponibilidade.py
│   ├── dia_semana.py
│   └── tipo_disciplina.py
└── daos/
    ├── banco_dados.py              # Conexões, tabelas, commit e rollback
    ├── disciplina_dao.py           # SQL do catálogo
    ├── estudante_dao.py            # SQL do cadastro de estudantes
    ├── disponibilidade_dao.py      # SQL da disponibilidade
    └── status_persistencia.py      # OK, DUPLICADO ou ERRO
```

O caminho de uma operação é:

```text
View → Controller → Model (validar) → DAO → BancoDados → SQLite
                 ← ResultadoOperacao ← confirmação da gravação
```

- A **View** lê os campos e apresenta o resultado. Não executa SQL nem altera a entidade.
- O **Controller** coordena o caso de uso e só atualiza o estado em memória após salvar.
- O **Model** guarda o estado e valida regras. Não importa Qt nem DAOs.
- O **DAO** contém SQL parametrizado e transforma linhas em objetos.
- O **BancoDados** abre e fecha as conexões, ativa as chaves estrangeiras e confirma
  a transação antes de devolver sucesso. Erros de escrita causam rollback;
  erros de leitura impedem abrir o perfil com dados incompletos.

Os DAOs fazem parte da persistência da camada Model no MVC. A pasta `models`
contém especificamente as entidades e suas regras, como nas raias dos diagramas.
Não há ORM, classes base ou uma camada de serviços.

## Entrega 3

**Gustavo — definir limite de disciplinas:** implementado na interface gráfica.
O Model valida sem alterar o estudante e retorna um booleano. O controller chama
o DAO e, somente após o commit, atualiza a entidade e devolve o limite no
`ResultadoOperacao`. A View usa esse resultado para atualizar o valor mostrado.

O limite aceito é um inteiro de **1 a 2.147.483.647**, intervalo de representação
compartilhado pelo Model, DAO e campo numérico da tela. Booleanos são recusados.
O valor inicial `0` significa “Não definido” e não pode ser escolhido como novo
limite. Bancos antigos recebem a coluna automaticamente. Se um banco já contiver
um limite incompatível, a abertura do perfil é recusada sem apagar esse valor.

**David — registrar disciplinas concluídas:** pendente. Adicionar a coleção e a
regra de duplicidade em `models/estudante.py`, criar `HistoricoDAO` e a tabela com
chave composta, o método no `EstudanteController` e a seleção do catálogo na View.

As novas dependências devem ser montadas em `main.py`, mantendo o fluxo do
`v5.eap`. Os nomes dos métodos em Python usam `snake_case`.

## Verificar

Os testes usam bancos temporários e não alteram o banco da aplicação:

```bash
uv run python -m unittest discover -s tests -v
```

Cobrem persistência após reabrir, duplicidade, validação, isolamento entre
estudantes, falha de gravação, migração e limites extremos. Os testes da interface
gráfica executam sem abrir janelas na área de trabalho.
