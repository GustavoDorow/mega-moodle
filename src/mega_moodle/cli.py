from mega_moodle.administrador import Administrador
from mega_moodle.disciplina import Disciplina
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


def main() -> None:
    print("Mega Moodle\n-----------\n")

    administrador = Administrador(
        id=int(input("ID do administrador: ")),
        nome=input("Nome do administrador: ").strip(),
    )
    disciplinas: list[Disciplina] = []

    while True:
        print(
            "\n------------------------\n"
            "1 - Cadastrar disciplina\n"
            "2 - Listar disciplinas\n"
            "0 - Sair\n"
            "------------------------"
        )
        escolha = input("Escolha: ").strip()

        if escolha == "1":
            disciplinas.append(cadastrar_disciplina(administrador))
        elif escolha == "2":
            exibir_disciplinas(disciplinas)
        elif escolha == "0":
            print("Programa encerrado.")
            return
        else:
            print("Escolha 1, 2 ou 0.")
