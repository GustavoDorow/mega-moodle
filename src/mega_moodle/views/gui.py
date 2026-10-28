from PySide6.QtCore import QTime
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTimeEdit,
    QWidget,
)

from mega_moodle.controllers.administrador_controller import AdministradorController
from mega_moodle.controllers.cadastro_controller import CadastroController
from mega_moodle.controllers.estudante_controller import EstudanteController
from mega_moodle.models.dia_semana import DiaSemana
from mega_moodle.models.disciplina import Disciplina
from mega_moodle.models.estudante import MAX_LIMITE_DISCIPLINAS
from mega_moodle.models.tipo_disciplina import TipoDisciplina


class MegaMoodleWindow(QMainWindow):
    def __init__(self, controller: CadastroController) -> None:
        super().__init__()
        self.controller = controller
        self.administrador_controller: AdministradorController | None = None
        self.estudante_controller: EstudanteController | None = None
        self.setWindowTitle("Mega Moodle")
        self.resize(650, 400)
        self.setCentralWidget(self._cadastro())

    @staticmethod
    def _formulario() -> tuple[QWidget, QFormLayout]:
        tela = QWidget()
        return tela, QFormLayout(tela)

    def _cadastro(self) -> QWidget:
        tela, form = self._formulario()
        form.addRow(QLabel("Cadastro"))

        self.identificacao = QSpinBox(maximum=99999999)
        self.nome_usuario = QLineEdit()
        self.perfil = QComboBox()
        self.perfil.addItems(["Administrador", "Estudante"])

        form.addRow("Identificação", self.identificacao)
        form.addRow("Nome", self.nome_usuario)
        form.addRow("Perfil", self.perfil)
        form.addRow(self._botao("Cadastrar", self._cadastrar_usuario))
        return tela

    def _cadastrar_usuario(self) -> None:
        perfil = self.perfil.currentText()
        resultado = self.controller.cadastrar_usuario(
            self.identificacao.value(), self.nome_usuario.text(), perfil
        )
        if not resultado.sucesso:
            self._exibir_mensagem("Cadastro", resultado.mensagem, sucesso=False)
            return

        self.administrador_controller = self.controller.administrador_controller
        self.estudante_controller = self.controller.estudante_controller
        tela = self._admin() if perfil == "Administrador" else self._estudante()
        self.setCentralWidget(tela)

    def _admin(self) -> QWidget:
        tela, form = self._formulario()
        nome = self.administrador_controller.administrador.nome
        form.addRow(QLabel(f"Administrador: {nome}"), self._botao("Sair", self._voltar_cadastro))

        self.codigo = QLineEdit()
        self.nome_disciplina = QLineEdit()
        self.carga = QSpinBox(minimum=1, maximum=999, value=72)
        self.fase = QSpinBox(minimum=1, maximum=20)
        self.tipo = QComboBox()
        for tipo in TipoDisciplina:
            self.tipo.addItem(tipo.value, tipo)

        form.addRow("Código", self.codigo)
        form.addRow("Nome", self.nome_disciplina)
        form.addRow("Carga horária", self.carga)
        form.addRow("Fase", self.fase)
        form.addRow("Tipo", self.tipo)
        form.addRow(self._botao("Cadastrar disciplina", self._cadastrar_disciplina))

        self.lista = QListWidget()
        form.addRow(self.lista)
        self._atualizar_disciplinas()
        return tela

    def _cadastrar_disciplina(self) -> None:
        resultado = self.administrador_controller.cadastrar_disciplina(
            self.codigo.text(),
            self.nome_disciplina.text(),
            self.carga.value(),
            self.fase.value(),
            self.tipo.currentData(),
        )
        if not resultado.sucesso:
            self._exibir_mensagem("Disciplina", resultado.mensagem, sucesso=False)
            return

        self._atualizar_disciplinas()
        self.codigo.clear()
        self.nome_disciplina.clear()

    def _atualizar_disciplinas(self) -> None:
        self.lista.clear()
        for disciplina in self.administrador_controller.disciplinas:
            self.lista.addItem(
                f"{disciplina.codigo} | {disciplina.nome} | "
                f"{disciplina.carga_horaria} h | {disciplina.fase_sugerida}ª fase | "
                f"{disciplina.tipo.value}"
            )

    def _estudante(self) -> QWidget:
        tela, form = self._formulario()
        form.addRow(
            QLabel(f"Estudante: {self.estudante_controller.estudante.nome}"),
            self._botao("Sair", self._voltar_cadastro),
        )

        self.limite_atual = QLabel()
        limite = self.estudante_controller.estudante.limite_disciplinas
        self._atualizar_limite(limite)
        self.limite_disciplinas = QSpinBox(
            minimum=1,
            maximum=MAX_LIMITE_DISCIPLINAS,
            value=limite or 1,
        )
        form.addRow("Limite atual", self.limite_atual)
        form.addRow("Novo limite", self.limite_disciplinas)
        form.addRow(self._botao("Salvar limite", self._salvar_limite))

        self.dia = QComboBox()
        for dia in DiaSemana:
            self.dia.addItem(dia.value, dia)
        self.inicio = QTimeEdit(QTime(8, 0), displayFormat="HH:mm")
        self.fim = QTimeEdit(QTime(12, 0), displayFormat="HH:mm")

        form.addRow("Dia", self.dia)
        form.addRow("Início", self.inicio)
        form.addRow("Fim", self.fim)
        form.addRow(self._botao("Registrar", self._registrar_disponibilidade))

        self.lista = QListWidget()
        form.addRow(self.lista)
        self._atualizar_disponibilidades()

        self.disciplina_concluida = QComboBox()
        for disciplina in self.estudante_controller.catalogo_disciplinas:
            self.disciplina_concluida.addItem(
                f"{disciplina.codigo} - {disciplina.nome}", disciplina
            )
        self.botao_registrar_concluida = self._botao(
            "Registrar disciplina concluída", self._registrar_disciplina_concluida
        )
        tem_disciplinas = bool(self.estudante_controller.catalogo_disciplinas)
        self.disciplina_concluida.setEnabled(tem_disciplinas)
        self.botao_registrar_concluida.setEnabled(tem_disciplinas)

        form.addRow("Disciplina", self.disciplina_concluida)
        form.addRow(self.botao_registrar_concluida)

        self.lista_concluidas = QListWidget()
        form.addRow("Histórico", self.lista_concluidas)
        self._atualizar_lista_concluidas(self.estudante_controller.estudante.disciplinas_concluidas)

        return tela

    def _registrar_disciplina_concluida(self) -> None:
        disciplina = self.disciplina_concluida.currentData()
        if disciplina is None:
            return

        resultado = self.estudante_controller.registrar_disciplina_concluida(disciplina)
        if not resultado.sucesso:
            self._exibir_mensagem("Disciplina concluída", resultado.mensagem, sucesso=False)
            return

        if resultado.disciplinas is not None:
            self._atualizar_lista_concluidas(resultado.disciplinas)
        self._exibir_mensagem("Disciplina concluída", resultado.mensagem, sucesso=True)

    def _atualizar_lista_concluidas(self, disciplinas: list[Disciplina]) -> None:
        self.lista_concluidas.clear()
        for disciplina in disciplinas:
            self.lista_concluidas.addItem(f"{disciplina.codigo} - {disciplina.nome}")

    _atualizar_historico = _atualizar_lista_concluidas

    def _salvar_limite(self) -> None:
        resultado = self.estudante_controller.definir_limite_disciplinas(
            self.limite_disciplinas.value()
        )
        if not resultado.sucesso:
            self._exibir_mensagem("Limite de disciplinas", resultado.mensagem, sucesso=False)
            return

        self._atualizar_limite(resultado.limite)
        self._exibir_mensagem("Limite de disciplinas", resultado.mensagem, sucesso=True)

    def _atualizar_limite(self, limite: int | None) -> None:
        self.limite_atual.setText(str(limite) if limite else "Não definido")

    def _registrar_disponibilidade(self) -> None:
        resultado = self.estudante_controller.registrar_disponibilidade(
            self.dia.currentData(),
            self.inicio.time().toPython(),
            self.fim.time().toPython(),
        )
        if not resultado.sucesso:
            self._exibir_mensagem("Disponibilidade", resultado.mensagem, sucesso=False)
            return

        self._atualizar_disponibilidades()

    def _atualizar_disponibilidades(self) -> None:
        self.lista.clear()
        for disponibilidade in self.estudante_controller.estudante.disponibilidades:
            self.lista.addItem(
                f"{disponibilidade.dia_semana.value}: "
                f"{disponibilidade.hora_inicio:%H:%M} às "
                f"{disponibilidade.hora_fim:%H:%M}"
            )

    def _exibir_mensagem(self, titulo: str, mensagem: str, sucesso: bool = True) -> None:
        if sucesso:
            QMessageBox.information(self, titulo, mensagem)
        else:
            QMessageBox.warning(self, titulo, mensagem)

    @staticmethod
    def _botao(texto: str, acao) -> QPushButton:
        botao = QPushButton(texto)
        botao.clicked.connect(acao)
        return botao

    def _voltar_cadastro(self) -> None:
        self.administrador_controller = None
        self.estudante_controller = None
        self.setCentralWidget(self._cadastro())
