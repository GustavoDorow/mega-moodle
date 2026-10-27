from mega_moodle.daos.banco_dados import BancoDados
from mega_moodle.daos.status_persistencia import StatusPersistencia
from mega_moodle.models.estudante import Estudante


class EstudanteDAO:
    def __init__(self, banco: BancoDados) -> None:
        self.banco = banco

    def salvar(self, estudante: Estudante) -> StatusPersistencia:
        linhas = self.banco.executar_atualizacao(
            """
            INSERT INTO estudante (id, nome) VALUES (?, ?)
            ON CONFLICT (id) DO UPDATE SET nome = excluded.nome
            """,
            (estudante.id, estudante.nome),
        )
        return StatusPersistencia.OK if linhas == 1 else StatusPersistencia.ERRO

    def buscar_por_id(self, identificacao: int) -> Estudante | None:
        linhas = self.banco.consultar(
            "SELECT id, nome FROM estudante WHERE id = ?", (identificacao,)
        )
        if not linhas:
            return None
        return Estudante(id=linhas[0]["id"], nome=linhas[0]["nome"])
