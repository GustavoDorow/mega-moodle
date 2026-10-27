from datetime import datetime

from mega_moodle.controllers.administrador_controller import AdministradorController
from mega_moodle.controllers.cadastro_controller import CadastroController
from mega_moodle.controllers.estudante_controller import EstudanteController
from mega_moodle.models.dia_semana import DiaSemana
from mega_moodle.models.disciplina import Disciplina
from mega_moodle.models.disponibilidade import Disponibilidade
from mega_moodle.models.tipo_disciplina import TipoDisciplina


def exibir_disciplina(disciplina: Disciplina) -> None:
    print(f"Código: {disciplina.codigo}")
    print(f"Nome: {disciplina.nome}")
    print(f"Carga horária: {disciplina.carga_horaria} horas")
    print(f"Fase sugerida: {disciplina.fase_sugerida}")
    print(f"Tipo: {disciplina.tipo.value}")


def cadastrar_disciplina(controller: AdministradorController) -> None:
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

    resultado = controller.cadastrar_disciplina(
        codigo=codigo,
        nome=nome,
        carga_horaria=carga_horaria,
        fase_sugerida=fase_sugerida,
        tipo=tipo,
    )

    print(resultado.mensagem)


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


def informar_disponibilidade(controller: EstudanteController) -> None:
    print("\nDisponibilidade semanal\n------------------------")
    dias = list(DiaSemana)

    for numero, dia in enumerate(dias, start=1):
        print(f"{numero} - {dia.value}")

    numero_dia = int(input("Dia da semana: ").strip())
    if not 1 <= numero_dia <= len(dias):
        print("Selecione um dos dias da lista.")
        return
    dia_semana = dias[numero_dia - 1]
    hora_inicio = ler_horario("Horário inicial (HH:MM): ")
    hora_fim = ler_horario("Horário final (HH:MM): ")

    resultado = controller.registrar_disponibilidade(
        dia_semana,
        hora_inicio,
        hora_fim,
    )
    print(resultado.mensagem)


def exibir_disponibilidades(disponibilidades: list[Disponibilidade]) -> None:
    print("\nDisponibilidades registradas\n-----------------------------")

    if not disponibilidades:
        print("Nenhuma disponibilidade registrada.")
        return

    for numero, disponibilidade in enumerate(disponibilidades, start=1):
        print(f"\nDisponibilidade {numero}")
        print("--------------------")
        exibir_disponibilidade(disponibilidade)


def executar(controller: CadastroController) -> None:
    print("Mega Moodle\n-----------\n")

    resultado = controller.cadastrar_usuario(
        identificacao=int(input("ID do administrador: ")),
        nome=input("Nome do administrador: ").strip(),
        perfil="Administrador",
    )
    if not resultado.sucesso:
        print(resultado.mensagem)
        return

    resultado = controller.cadastrar_usuario(
        identificacao=int(input("ID do estudante: ")),
        nome=input("Nome do estudante: ").strip(),
        perfil="Estudante",
    )
    if not resultado.sucesso:
        print(resultado.mensagem)
        return

    administrador = controller.administrador_controller
    estudante = controller.estudante_controller

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
            try:
                cadastrar_disciplina(administrador)
            except (ValueError, KeyError):
                print("Informe números e um tipo de disciplina válido.")
        elif escolha == "2":
            exibir_disciplinas(administrador.disciplinas)
        elif escolha == "3":
            try:
                informar_disponibilidade(estudante)
            except (ValueError, IndexError):
                print("Informe um dia válido e horários no formato HH:MM.")
        elif escolha == "4":
            exibir_disponibilidades(estudante.estudante.disponibilidades)
        elif escolha == "0":
            print("Programa encerrado.")
            return
        else:
            print("Escolha uma opção entre 0 e 4.")
