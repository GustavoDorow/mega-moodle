from datetime import datetime

from mega_moodle.administrador import Administrador
from mega_moodle.dia_semana import DiaSemana
from mega_moodle.disciplina import Disciplina
from mega_moodle.disponibilidade import Disponibilidade
from mega_moodle.estudante import Estudante
from mega_moodle.tipo_disciplina import TipoDisciplina


def exibir_disciplina(disciplina: Disciplina) -> None:
    print(f"Código: {disciplina.codigo}")
    print(f"Nome: {disciplina.nome}")
    print(f"Carga horária: {disciplina.carga_horaria} horas")
    print(f"Fase sugerida: {disciplina.fase_sugerida}")
    print(f"Tipo: {disciplina.tipo.value}")


def cadastrar_disciplina(administrador: Administrador) -> Disciplina:
    print("\nCadastro de disciplina\n-----------------------")

    codigo = input("Código da disciplina: ").strip()
    nome = input("Nome da disciplina: ").strip()
    carga_horaria = int(input("Carga horária: "))
    fase_sugerida = int(input("Fase sugerida: "))

    print("\n1 - Obrigatória\n2 - Optativa")
    tipo = {
        "1": TipoDisciplina.OBRIGATORIA,
        "2": TipoDisciplina.OPTATIVA,
    }[input("Tipo da disciplina: ").strip()]

    disciplina = administrador.cadastrar_disciplina(
        codigo=codigo,
        nome=nome,
        carga_horaria=carga_horaria,
        fase_sugerida=fase_sugerida,
        tipo=tipo,
    )

    print("\nDisciplina cadastrada com sucesso!")
    exibir_disciplina(disciplina)
    return disciplina


def exibir_disciplinas(disciplinas: list[Disciplina]) -> None:
    print("\nDisciplinas cadastradas\n------------------------")

    if not disciplinas:
        print("Nenhuma disciplina cadastrada.")
        return

    for numero, disciplina in enumerate(disciplinas, start=1):
        print(f"\nDisciplina {numero}")
        print("--------------------")
        exibir_disciplina(disciplina)


def ler_horario(mensagem: str):
    return datetime.strptime(input(mensagem).strip(), "%H:%M").time()


def exibir_disponibilidade(disponibilidade: Disponibilidade) -> None:
    print(f"Dia: {disponibilidade.dia_semana.value}")
    print(f"Início: {disponibilidade.hora_inicio:%H:%M}")
    print(f"Fim: {disponibilidade.hora_fim:%H:%M}")


def informar_disponibilidade(estudante: Estudante) -> None:
    print("\nDisponibilidade semanal\n------------------------")
    dias = list(DiaSemana)

    for numero, dia in enumerate(dias, start=1):
        print(f"{numero} - {dia.value}")

    dia_semana = dias[int(input("Dia da semana: ").strip()) - 1]
    hora_inicio = ler_horario("Horário inicial (HH:MM): ")
    hora_fim = ler_horario("Horário final (HH:MM): ")

    disponibilidade = estudante.definir_disponibilidade(
        dia_semana,
        hora_inicio,
        hora_fim,
    )
    print("\nDisponibilidade registrada com sucesso!")
    exibir_disponibilidade(disponibilidade)


def exibir_disponibilidades(estudante: Estudante) -> None:
    print("\nDisponibilidades registradas\n-----------------------------")

    if not estudante.disponibilidades:
        print("Nenhuma disponibilidade registrada.")
        return

    for numero, disponibilidade in enumerate(estudante.disponibilidades, start=1):
        print(f"\nDisponibilidade {numero}")
        print("--------------------")
        exibir_disponibilidade(disponibilidade)


def main() -> None:
    print("Mega Moodle\n-----------\n")

    administrador = Administrador(
        id=int(input("ID do administrador: ")),
        nome=input("Nome do administrador: ").strip(),
    )
    estudante = Estudante(
        id=int(input("ID do estudante: ")),
        nome=input("Nome do estudante: ").strip(),
    )
    disciplinas: list[Disciplina] = []

    while True:
        print(
            "\n------------------------\n"
            "1 - Cadastrar disciplina\n"
            "2 - Listar disciplinas\n"
            "3 - Informar disponibilidade\n"
            "4 - Listar disponibilidades\n"
            "0 - Sair\n"
            "------------------------"
        )
        escolha = input("Escolha: ").strip()

        if escolha == "1":
            disciplinas.append(cadastrar_disciplina(administrador))
        elif escolha == "2":
            exibir_disciplinas(disciplinas)
        elif escolha == "3":
            informar_disponibilidade(estudante)
        elif escolha == "4":
            exibir_disponibilidades(estudante)
        elif escolha == "0":
            print("Programa encerrado.")
            return
        else:
            print("Escolha uma opção entre 0 e 4.")
