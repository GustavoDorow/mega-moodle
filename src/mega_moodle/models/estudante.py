from dataclasses import dataclass, field
from datetime import time

from mega_moodle.models.dia_semana import DiaSemana
from mega_moodle.models.disciplina import Disciplina
from mega_moodle.models.disponibilidade import Disponibilidade


# Limite de representação adotado pela aplicação: inteiro de 32 bits com sinal.
MAX_LIMITE_DISCIPLINAS = 2_147_483_647


@dataclass
class Estudante:
    id: int
    nome: str
    disponibilidades: list[Disponibilidade] = field(default_factory=list)
    limite_disciplinas: int = 0
    disciplinas_concluidas: list[Disciplina] = field(default_factory=list)

    def registrar_disciplina_concluida(self, disciplina: Disciplina) -> bool:
        if any(d.codigo == disciplina.codigo for d in self.disciplinas_concluidas):
            return False
        self.disciplinas_concluidas.append(disciplina)
        return True

    def definir_disponibilidade(
        self,
        dia_semana: DiaSemana,
        hora_inicio: time,
        hora_fim: time,
    ) -> Disponibilidade:
        disponibilidade = Disponibilidade(dia_semana, hora_inicio, hora_fim)
        self.disponibilidades.append(disponibilidade)
        return disponibilidade

    @staticmethod
    def validar_limite_disciplinas(limite: int) -> bool:
        return (
            isinstance(limite, int)
            and not isinstance(limite, bool)
            and 1 <= limite <= MAX_LIMITE_DISCIPLINAS
        )

    def definir_limite_disciplinas(self, limite: int) -> bool:
        if not self.validar_limite_disciplinas(limite):
            return False
        self.limite_disciplinas = limite
        return True
