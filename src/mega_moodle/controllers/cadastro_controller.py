import sqlite3

from mega_moodle.controllers.administrador_controller import AdministradorController
from mega_moodle.controllers.estudante_controller import EstudanteController
from mega_moodle.controllers.resultado_operacao import ResultadoOperacao
from mega_moodle.daos.disciplina_dao import DisciplinaDAO
from mega_moodle.daos.disponibilidade_dao import DisponibilidadeDAO
from mega_moodle.daos.estudante_dao import EstudanteDAO
from mega_moodle.daos.status_persistencia import StatusPersistencia
from mega_moodle.models.administrador import Administrador
from mega_moodle.models.estudante import Estudante


class CadastroController:
    def __init__(
        self,
        disciplina_dao: DisciplinaDAO,
        estudante_dao: EstudanteDAO,
        disponibilidade_dao: DisponibilidadeDAO,
    ) -> None:
        self.disciplina_dao = disciplina_dao
        self.estudante_dao = estudante_dao
        self.disponibilidade_dao = disponibilidade_dao
        self.administrador_controller: AdministradorController | None = None
        self.estudante_controller: EstudanteController | None = None

    def cadastrar_usuario(
        self, identificacao: int, nome: str, perfil: str
    ) -> ResultadoOperacao:
        nome = nome.strip()
        if not nome:
            return ResultadoOperacao(False, "Informe o nome.")
        if perfil not in ("Administrador", "Estudante"):
            return ResultadoOperacao(False, "Selecione um perfil válido.")

        try:
            if perfil == "Administrador":
                administrador = Administrador(identificacao, nome)
                self.administrador_controller = AdministradorController(
                    administrador, self.disciplina_dao
                )
            else:
                estudante = Estudante(identificacao, nome)
                if self.estudante_dao.salvar(estudante) is StatusPersistencia.ERRO:
                    return ResultadoOperacao(False, "Não foi possível salvar o estudante.")
                estudante.disponibilidades = self.disponibilidade_dao.listar(identificacao)
                self.estudante_controller = EstudanteController(
                    estudante, self.disponibilidade_dao
                )
        except (sqlite3.Error, ValueError):
            return ResultadoOperacao(False, "Não foi possível carregar os dados do perfil.")

        return ResultadoOperacao(True, "Perfil carregado.")
