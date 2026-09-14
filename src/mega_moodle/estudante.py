from dataclasses import dataclass, field
from datetime import time

from mega_moodle.dia_semana import DiaSemana
from mega_moodle.disponibilidade import Disponibilidade


@dataclass
class Estudante:
    id: int
    nome: str
    disponibilidades: list[Disponibilidade] = field(default_factory=list)

    def definir_disponibilidade(
        self,
        dia_semana: DiaSemana,
        hora_inicio: time,
        hora_fim: time,
    ) -> Disponibilidade:
        disponibilidade = Disponibilidade(dia_semana, hora_inicio, hora_fim)
        self.disponibilidades.append(disponibilidade)
        return disponibilidade
