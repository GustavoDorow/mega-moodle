from dataclasses import dataclass
from datetime import time

from mega_moodle.dia_semana import DiaSemana


@dataclass
class Disponibilidade:
    dia_semana: DiaSemana
    hora_inicio: time
    hora_fim: time

    def __post_init__(self) -> None:
        if self.hora_inicio >= self.hora_fim:
            raise ValueError("O horário inicial deve ser anterior ao horário final.")
