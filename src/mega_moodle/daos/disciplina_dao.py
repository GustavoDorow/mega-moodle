from mega_moodle.daos.banco_dados import BancoDados
from mega_moodle.daos.status_persistencia import StatusPersistencia
from mega_moodle.models.disciplina import Disciplina
from mega_moodle.models.tipo_disciplina import TipoDisciplina


class DisciplinaDAO:
    def __init__(self, banco: BancoDados) -> None:
        self.banco = banco

    def cadastrar(self, disciplina: Disciplina) -> StatusPersistencia:
        linhas = self.banco.executar_atualizacao(
            """
            INSERT INTO disciplina (codigo, nome, carga_horaria, fase_sugerida, tipo)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (codigo) DO NOTHING
            """,
            (
                disciplina.codigo,
                disciplina.nome,
                disciplina.carga_horaria,
                disciplina.fase_sugerida,
                disciplina.tipo.value,
            ),
        )
        if linhas == 1:
            return StatusPersistencia.OK
        if linhas == 0:
            return StatusPersistencia.DUPLICADO
        return StatusPersistencia.ERRO

    def listar(self) -> list[Disciplina]:
        linhas = self.banco.consultar("SELECT * FROM disciplina ORDER BY codigo")
        return [
            Disciplina(
                codigo=linha["codigo"],
                nome=linha["nome"],
                carga_horaria=linha["carga_horaria"],
                fase_sugerida=linha["fase_sugerida"],
                tipo=TipoDisciplina(linha["tipo"]),
            )
            for linha in linhas
        ]
