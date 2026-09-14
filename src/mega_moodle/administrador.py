from dataclasses import dataclass

from mega_moodle.disciplina import Disciplina
from mega_moodle.tipo_disciplina import TipoDisciplina


@dataclass
class Administrador:
    id: int
    nome: str

    def cadastrar_disciplina(
        self,
        codigo: str,
        nome: str,
        carga_horaria: int,
        fase_sugerida: int,
        tipo: TipoDisciplina,
    ) -> Disciplina:
        return Disciplina(codigo, nome, carga_horaria, fase_sugerida, tipo)
