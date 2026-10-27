from dataclasses import dataclass

from mega_moodle.models.tipo_disciplina import TipoDisciplina


@dataclass
class Disciplina:
    codigo: str
    nome: str
    carga_horaria: int
    fase_sugerida: int
    tipo: TipoDisciplina

    def __post_init__(self) -> None:
        if not self.codigo or not self.nome:
            raise ValueError("Informe o código e o nome.")
        if self.carga_horaria <= 0 or self.fase_sugerida <= 0:
            raise ValueError("A carga horária e a fase devem ser maiores que zero.")
