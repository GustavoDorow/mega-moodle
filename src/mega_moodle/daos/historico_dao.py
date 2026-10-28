from mega_moodle.daos.banco_dados import BancoDados
from mega_moodle.daos.status_persistencia import StatusPersistencia
from mega_moodle.models.disciplina import Disciplina
from mega_moodle.models.tipo_disciplina import TipoDisciplina


class HistoricoDAO:
    def __init__(self, banco: BancoDados) -> None:
        self.banco = banco

    def registrar(self, estudante_id: int, codigo_disciplina: str) -> StatusPersistencia:
        linhas = self.banco.executar_atualizacao(
            """
            INSERT INTO disciplina_concluida (
                estudante_id,
                disciplina_codigo
            )
            VALUES (?, ?)
            ON CONFLICT (estudante_id, disciplina_codigo) DO NOTHING
            """,
            (estudante_id, codigo_disciplina),
        )
        if linhas == 1:
            return StatusPersistencia.OK
        if linhas == 0:
            return StatusPersistencia.DUPLICADO
        return StatusPersistencia.ERRO

    def listar_concluidas(self, estudante_id: int) -> list[Disciplina]:
        linhas = self.banco.consultar(
            """
            SELECT d.codigo, d.nome, d.carga_horaria, d.fase_sugerida, d.tipo
            FROM disciplina_concluida dc
            JOIN disciplina d ON d.codigo = dc.disciplina_codigo
            WHERE dc.estudante_id = ?
            ORDER BY d.codigo
            """,
            (estudante_id,),
        )
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
