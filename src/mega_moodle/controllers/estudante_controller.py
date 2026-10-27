from datetime import time

from mega_moodle.controllers.resultado_operacao import ResultadoOperacao
from mega_moodle.daos.disponibilidade_dao import DisponibilidadeDAO
from mega_moodle.daos.status_persistencia import StatusPersistencia
from mega_moodle.models.dia_semana import DiaSemana
from mega_moodle.models.disponibilidade import Disponibilidade
from mega_moodle.models.estudante import Estudante


class EstudanteController:
    def __init__(
        self, estudante: Estudante, disponibilidade_dao: DisponibilidadeDAO
    ) -> None:
        self.estudante = estudante
        self.disponibilidade_dao = disponibilidade_dao

    def registrar_disponibilidade(
        self, dia_semana: DiaSemana, hora_inicio: time, hora_fim: time
    ) -> ResultadoOperacao:
        try:
            disponibilidade = Disponibilidade(dia_semana, hora_inicio, hora_fim)
        except ValueError as erro:
            return ResultadoOperacao(False, str(erro))

        status = self.disponibilidade_dao.registrar(self.estudante.id, disponibilidade)
        if status is StatusPersistencia.ERRO:
            return ResultadoOperacao(False, "Não foi possível salvar a disponibilidade.")

        # Só altera o estudante depois de confirmar a gravação no banco.
        self.estudante.definir_disponibilidade(dia_semana, hora_inicio, hora_fim)
        return ResultadoOperacao(True, "Disponibilidade registrada com sucesso.")
