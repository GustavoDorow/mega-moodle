from dataclasses import dataclass

from mega_moodle.tipo_disciplina import TipoDisciplina


@dataclass
class Disciplina:
    codigo: str
    nome: str
    carga_horaria: int
    fase_sugerida: int
    tipo: TipoDisciplina
