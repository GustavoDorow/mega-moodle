from datetime import time

from mega_moodle.controllers.resultado_operacao import ResultadoOperacao
from mega_moodle.daos.disponibilidade_dao import DisponibilidadeDAO
from mega_moodle.daos.estudante_dao import EstudanteDAO
from mega_moodle.daos.historico_dao import HistoricoDAO
from mega_moodle.daos.status_persistencia import StatusPersistencia
from mega_moodle.models.dia_semana import DiaSemana
from mega_moodle.models.disciplina import Disciplina
from mega_moodle.models.disponibilidade import Disponibilidade
from mega_moodle.models.estudante import MAX_LIMITE_DISCIPLINAS, Estudante


class EstudanteController:
    def __init__(
        self,
        estudante: Estudante,
        disponibilidade_dao: DisponibilidadeDAO,
        estudante_dao: EstudanteDAO,
        historico_dao: HistoricoDAO,
        catalogo_disciplinas: list[Disciplina] | None = None,
    ) -> None:
        self.estudante = estudante
        self.disponibilidade_dao = disponibilidade_dao
        self.estudante_dao = estudante_dao
        self.historico_dao = historico_dao
        self.catalogo_disciplinas: list[Disciplina] = (
            catalogo_disciplinas if catalogo_disciplinas is not None else []
        )

    def carregar_estudante(self) -> None:
        """Carrega disponibilidades e histórico do estudante a partir dos DAOs."""
        self.estudante.disponibilidades = self.disponibilidade_dao.listar(self.estudante.id)
        self.estudante.disciplinas_concluidas = self.historico_dao.listar_concluidas(
            self.estudante.id
        )

    @property
    def disciplinas(self) -> list[Disciplina]:
        return self.catalogo_disciplinas

    def definir_limite_disciplinas(self, limite: int) -> ResultadoOperacao:
        if not self.estudante.validar_limite_disciplinas(limite):
            return ResultadoOperacao(
                False,
                f"Informe um limite de disciplinas inteiro entre 1 e {MAX_LIMITE_DISCIPLINAS}.",
            )

        status = self.estudante_dao.atualizar_limite(self.estudante.id, limite)
        if status is not StatusPersistencia.OK:
            return ResultadoOperacao(False, "Não foi possível salvar o limite de disciplinas.")

        self.estudante.definir_limite_disciplinas(limite)
        return ResultadoOperacao(
            True, "Limite de disciplinas salvo com sucesso.", limite=limite
        )

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

    def registrar_disciplina_concluida(
        self, disciplina: Disciplina
    ) -> ResultadoOperacao:
        status = self.historico_dao.registrar(self.estudante.id, disciplina.codigo)
        if status is StatusPersistencia.DUPLICADO:
            return ResultadoOperacao(False, "Disciplina já registrada como concluída.")
        if status is StatusPersistencia.ERRO:
            return ResultadoOperacao(False, "Não foi possível salvar a disciplina concluída.")

        # Só altera o estudante depois de confirmar a gravação no banco.
        self.estudante.registrar_disciplina_concluida(disciplina)
        return ResultadoOperacao(
            True,
            "Disciplina concluída registrada com sucesso.",
            disciplinas=list(self.estudante.disciplinas_concluidas),
        )
