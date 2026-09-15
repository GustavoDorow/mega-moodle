import sys

from PySide6.QtCore import QTime
from PySide6.QtWidgets import (
    QApplication,
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

from mega_moodle.administrador import Administrador
from mega_moodle.dia_semana import DiaSemana
from mega_moodle.estudante import Estudante
from mega_moodle.tipo_disciplina import TipoDisciplina


class MegaMoodleWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.usuario: Administrador | Estudante | None = None
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
        self.perfil.addItem("Administrador", Administrador)
        self.perfil.addItem("Estudante", Estudante)

        form.addRow("Identificação", self.identificacao)
        form.addRow("Nome", self.nome_usuario)
        form.addRow("Perfil", self.perfil)
        form.addRow(self._botao("Cadastrar", self._cadastrar_usuario))
        return tela

    def _cadastrar_usuario(self) -> None:
        nome = self.nome_usuario.text().strip()
        if not nome:
            QMessageBox.warning(self, "Cadastro", "Informe o nome.")
            return

        classe = self.perfil.currentData()
        self.usuario = classe(self.identificacao.value(), nome)
        tela = self._admin() if classe is Administrador else self._estudante()
        self.setCentralWidget(tela)

    def _admin(self) -> QWidget:
        tela, form = self._formulario()
        form.addRow(QLabel(f"Administrador: {self.usuario.nome}"))

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
        return tela

    def _cadastrar_disciplina(self) -> None:
        codigo = self.codigo.text().strip().upper()
        nome = self.nome_disciplina.text().strip()
        if not codigo or not nome:
            QMessageBox.warning(self, "Disciplina", "Informe o código e o nome.")
            return

        disciplina = self.usuario.cadastrar_disciplina(
            codigo,
            nome,
            self.carga.value(),
            self.fase.value(),
            self.tipo.currentData(),
        )
        self.lista.addItem(
            f"{disciplina.codigo} | {disciplina.nome} | "
            f"{disciplina.carga_horaria} h | {disciplina.fase_sugerida}ª fase | "
            f"{disciplina.tipo.value}"
        )
        self.codigo.clear()
        self.nome_disciplina.clear()

    def _estudante(self) -> QWidget:
        tela, form = self._formulario()
        form.addRow(QLabel(f"Estudante: {self.usuario.nome}"))

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
        return tela

    def _registrar_disponibilidade(self) -> None:
        try:
            disponibilidade = self.usuario.definir_disponibilidade(
                self.dia.currentData(),
                self.inicio.time().toPython(),
                self.fim.time().toPython(),
            )
        except ValueError as erro:
            QMessageBox.warning(self, "Disponibilidade", str(erro))
            return

        self.lista.addItem(
            f"{disponibilidade.dia_semana.value}: "
            f"{disponibilidade.hora_inicio:%H:%M} às "
            f"{disponibilidade.hora_fim:%H:%M}"
        )

    @staticmethod
    def _botao(texto: str, acao) -> QPushButton:
        botao = QPushButton(texto)
        botao.clicked.connect(acao)
        return botao


def main() -> None:
    app = QApplication(sys.argv)
    janela = MegaMoodleWindow()
    janela.show()
    raise SystemExit(app.exec())
