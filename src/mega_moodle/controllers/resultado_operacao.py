from dataclasses import dataclass

from mega_moodle.models.disciplina import Disciplina


@dataclass
class ResultadoOperacao:
    sucesso: bool
    mensagem: str
    limite: int | None = None
    disciplinas: list[Disciplina] | None = None
