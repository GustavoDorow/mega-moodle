import logging
import sqlite3
from contextlib import closing
from pathlib import Path


class BancoDados:
    def __init__(self, caminho: str | Path) -> None:
        self.caminho = caminho

    def _conectar(self) -> sqlite3.Connection:
        conexao = sqlite3.connect(self.caminho)
        conexao.row_factory = sqlite3.Row
        conexao.execute("PRAGMA foreign_keys = ON")
        return conexao

    def inicializar(self) -> None:
        with closing(self._conectar()) as conexao:
            with conexao:
                conexao.executescript("""
                    CREATE TABLE IF NOT EXISTS estudante (
                        id INTEGER PRIMARY KEY,
                        nome TEXT NOT NULL,
                        limite_disciplinas INTEGER NOT NULL DEFAULT 0
                            CHECK (limite_disciplinas >= 0)
                    );

                    CREATE TABLE IF NOT EXISTS disciplina (
                        codigo TEXT PRIMARY KEY,
                        nome TEXT NOT NULL,
                        carga_horaria INTEGER NOT NULL CHECK (carga_horaria > 0),
                        fase_sugerida INTEGER NOT NULL CHECK (fase_sugerida > 0),
                        tipo TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS disponibilidade (
                        id INTEGER PRIMARY KEY,
                        estudante_id INTEGER NOT NULL REFERENCES estudante(id),
                        dia_semana TEXT NOT NULL,
                        hora_inicio TEXT NOT NULL,
                        hora_fim TEXT NOT NULL
                    );
                """)
                colunas = conexao.execute("PRAGMA table_info(estudante)").fetchall()
                if not any(coluna["name"] == "limite_disciplinas" for coluna in colunas):
                    conexao.execute("""
                        ALTER TABLE estudante
                        ADD COLUMN limite_disciplinas INTEGER NOT NULL DEFAULT 0
                            CHECK (limite_disciplinas >= 0)
                    """)

    def executar_atualizacao(self, sql: str, parametros: tuple = ()) -> int:
        """Retorna as linhas afetadas após o commit, ou -1 em caso de falha."""
        try:
            with closing(self._conectar()) as conexao:
                with conexao:
                    linhas = conexao.execute(sql, parametros).rowcount
            return linhas
        except sqlite3.Error:
            logging.exception("Não foi possível salvar os dados.")
            return -1

    def consultar(self, sql: str, parametros: tuple = ()) -> list[sqlite3.Row]:
        # A falha de leitura é tratada pelo controller; não vira uma lista vazia.
        with closing(self._conectar()) as conexao:
            return conexao.execute(sql, parametros).fetchall()
