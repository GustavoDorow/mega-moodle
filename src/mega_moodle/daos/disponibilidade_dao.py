from datetime import time

from mega_moodle.daos.banco_dados import BancoDados
from mega_moodle.daos.status_persistencia import StatusPersistencia
from mega_moodle.models.dia_semana import DiaSemana
from mega_moodle.models.disponibilidade import Disponibilidade


class DisponibilidadeDAO:
    def __init__(self, banco: BancoDados) -> None:
        self.banco = banco

    def registrar(
        self, estudante_id: int, disponibilidade: Disponibilidade
    ) -> StatusPersistencia:
        linhas = self.banco.executar_atualizacao(
            """
            INSERT INTO disponibilidade
                (estudante_id, dia_semana, hora_inicio, hora_fim)
            VALUES (?, ?, ?, ?)
            """,
            (
                estudante_id,
                disponibilidade.dia_semana.value,
                disponibilidade.hora_inicio.isoformat(),
                disponibilidade.hora_fim.isoformat(),
            ),
        )
        return StatusPersistencia.OK if linhas == 1 else StatusPersistencia.ERRO

    def listar(self, estudante_id: int) -> list[Disponibilidade]:
        linhas = self.banco.consultar(
            "SELECT * FROM disponibilidade WHERE estudante_id = ? ORDER BY id",
            (estudante_id,),
        )
        return [
            Disponibilidade(
                dia_semana=DiaSemana(linha["dia_semana"]),
                hora_inicio=time.fromisoformat(linha["hora_inicio"]),
                hora_fim=time.fromisoformat(linha["hora_fim"]),
            )
            for linha in linhas
        ]
