from mega_moodle.controllers.resultado_operacao import ResultadoOperacao
from mega_moodle.daos.disciplina_dao import DisciplinaDAO
from mega_moodle.daos.status_persistencia import StatusPersistencia
from mega_moodle.models.administrador import Administrador
from mega_moodle.models.tipo_disciplina import TipoDisciplina


class AdministradorController:
    def __init__(self, administrador: Administrador, disciplina_dao: DisciplinaDAO) -> None:
        self.administrador = administrador
        self.disciplina_dao = disciplina_dao
        self.disciplinas = disciplina_dao.listar()

    def cadastrar_disciplina(
        self,
        codigo: str,
        nome: str,
        carga_horaria: int,
        fase_sugerida: int,
        tipo: TipoDisciplina,
    ) -> ResultadoOperacao:
        try:
            disciplina = self.administrador.cadastrar_disciplina(
                codigo.strip().upper(), nome.strip(), carga_horaria, fase_sugerida, tipo
            )
        except ValueError as erro:
            return ResultadoOperacao(False, str(erro))

        status = self.disciplina_dao.cadastrar(disciplina)
        if status is StatusPersistencia.DUPLICADO:
            return ResultadoOperacao(False, "Já existe uma disciplina com esse código.")
        if status is StatusPersistencia.ERRO:
            return ResultadoOperacao(False, "Não foi possível salvar a disciplina.")

        self.disciplinas.append(disciplina)
        self.disciplinas.sort(key=lambda item: item.codigo)
        return ResultadoOperacao(True, "Disciplina cadastrada com sucesso.")
