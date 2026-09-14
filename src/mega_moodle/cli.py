from mega_moodle.administrador import Administrador
from mega_moodle.disciplina import Disciplina
from mega_moodle.tipo_disciplina import TipoDisciplina


def ler_texto(mensagem: str) -> str:
    while not (valor := input(mensagem).strip()):
        print("Este campo não pode ficar vazio.")
    return valor


def ler_inteiro_positivo(mensagem: str) -> int:
    while True:
        entrada = input(mensagem).strip()

        if entrada.isdigit() and int(entrada) > 0:
            return int(entrada)

        print("Digite um número inteiro positivo.")


def ler_tipo_disciplina() -> TipoDisciplina:
    opcoes = {
        "1": TipoDisciplina.OBRIGATORIA,
        "2": TipoDisciplina.OPTATIVA,
    }

    while True:
        print("\n1 - Obrigatória")
        print("2 - Optativa")
        escolha = input("Tipo da disciplina: ").strip()

        if escolha in opcoes:
            return opcoes[escolha]

        print("Escolha 1 ou 2.")


def exibir_disciplina(disciplina: Disciplina) -> None:
    print(f"Código: {disciplina.codigo}")
    print(f"Nome: {disciplina.nome}")
    print(f"Carga horária: {disciplina.carga_horaria} horas")
    print(f"Fase sugerida: {disciplina.fase_sugerida}")
    print(f"Tipo: {disciplina.tipo.value}")


def cadastrar_disciplina(administrador: Administrador) -> Disciplina:
    print("\nCadastro de disciplina")
    print("-----------------------")
    disciplina = administrador.cadastrar_disciplina(
        codigo=ler_texto("Código da disciplina: "),
        nome=ler_texto("Nome da disciplina: "),
        carga_horaria=ler_inteiro_positivo("Carga horária: "),
        fase_sugerida=ler_inteiro_positivo("Fase sugerida: "),
        tipo=ler_tipo_disciplina(),
    )

    print("\nDisciplina cadastrada com sucesso!")
    exibir_disciplina(disciplina)
    return disciplina


def exibir_disciplinas(disciplinas: list[Disciplina]) -> None:
    print("\nDisciplinas cadastradas")
    print("------------------------")

    if not disciplinas:
        print("Nenhuma disciplina cadastrada.")
        return

    for numero, disciplina in enumerate(disciplinas, start=1):
        print(f"\nDisciplina {numero}")
        print("--------------------")
        exibir_disciplina(disciplina)


def main() -> None:
    print("Mega Moodle")
    print("-----------\n")

    administrador = Administrador(
        id=ler_inteiro_positivo("ID do administrador: "),
        nome=ler_texto("Nome do administrador: "),
    )
    disciplinas: list[Disciplina] = []

    while True:
        print("\n------------------------")
        print("1 - Cadastrar disciplina")
        print("2 - Listar disciplinas")
        print("0 - Sair")
        print("------------------------")
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
