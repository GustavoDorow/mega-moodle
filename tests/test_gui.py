import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QTime
from PySide6.QtWidgets import QApplication

from mega_moodle.daos.status_persistencia import StatusPersistencia
from mega_moodle.controllers.resultado_operacao import ResultadoOperacao
from mega_moodle.main import criar_controller
from mega_moodle.models.estudante import MAX_LIMITE_DISCIPLINAS
from mega_moodle.views.gui import MegaMoodleWindow


class TelasTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.pasta = TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.caminho = Path(self.pasta.name) / "teste.db"
        self.cadastro = criar_controller(self.caminho)
        self.janela = self.abrir_janela(self.cadastro)

    def abrir_janela(self, cadastro):
        janela = MegaMoodleWindow(cadastro)
        self.addCleanup(janela.close)
        return janela

    def abrir_perfil(self, janela, perfil):
        janela.nome_usuario.setText("Usuário de teste")
        janela.identificacao.setValue(10)
        janela.perfil.setCurrentText(perfil)
        janela._cadastrar_usuario()

    def test_cadastro_disciplina_persiste_e_reaparece_na_tela(self):
        self.abrir_perfil(self.janela, "Administrador")
        self.janela.codigo.setText("INE5608")
        self.janela.nome_disciplina.setText("APS")
        self.janela._cadastrar_disciplina()
        self.assertEqual(self.janela.lista.count(), 1)
        self.assertEqual(self.janela.codigo.text(), "")

        reaberta = self.abrir_janela(criar_controller(self.caminho))
        self.abrir_perfil(reaberta, "Administrador")
        self.assertIn("INE5608", reaberta.lista.item(0).text())

    def test_limite_confirma_persiste_e_falha_preserva_estado(self):
        self.abrir_perfil(self.janela, "Estudante")
        self.assertEqual(self.janela.limite_atual.text(), "Não definido")
        self.janela.limite_disciplinas.setValue(4)
        with patch("mega_moodle.views.gui.QMessageBox.information") as confirmacao:
            self.janela._salvar_limite()
            confirmacao.assert_called_once()
        self.assertEqual(self.janela.limite_atual.text(), "4")

        self.janela.close()
        reaberta = self.abrir_janela(criar_controller(self.caminho))
        self.abrir_perfil(reaberta, "Estudante")
        self.assertEqual(reaberta.limite_atual.text(), "4")
        self.assertEqual(reaberta.limite_disciplinas.value(), 4)
        reaberta.limite_disciplinas.setValue(6)
        with patch.object(
            reaberta.controller.estudante_dao, "atualizar_limite",
            return_value=StatusPersistencia.ERRO,
        ), patch("mega_moodle.views.gui.QMessageBox.warning") as aviso, patch(
            "mega_moodle.views.gui.QMessageBox.information"
        ) as confirmacao:
            reaberta._salvar_limite()
            aviso.assert_called_once()
            confirmacao.assert_not_called()
        self.assertEqual(reaberta.limite_atual.text(), "4")
        self.assertEqual(reaberta.estudante_controller.estudante.limite_disciplinas, 4)
        self.assertEqual(reaberta.controller.estudante_dao.buscar_por_id(10).limite_disciplinas, 4)

    def test_falha_ao_ler_estudante_mantem_tela_de_cadastro(self):
        tela = self.janela.centralWidget()
        with patch.object(
            self.cadastro.estudante_dao, "buscar_por_id", return_value=None
        ), patch("mega_moodle.views.gui.QMessageBox.warning") as aviso:
            self.abrir_perfil(self.janela, "Estudante")
            aviso.assert_called_once()
        self.assertIs(self.janela.centralWidget(), tela)
        self.assertIsNone(self.janela.estudante_controller)

    def test_tela_atualiza_limite_pelo_resultado_do_controller(self):
        self.abrir_perfil(self.janela, "Estudante")
        self.janela.limite_disciplinas.setValue(6)
        resultado = ResultadoOperacao(True, "Limite salvo.", limite=6)
        with patch.object(
            self.janela.estudante_controller, "definir_limite_disciplinas", return_value=resultado
        ) as salvar, patch("mega_moodle.views.gui.QMessageBox.information"):
            self.janela._salvar_limite()
            salvar.assert_called_once_with(6)
        # O mock não altera a entidade: a tela precisa usar o valor do DTO.
        self.assertEqual(self.janela.estudante_controller.estudante.limite_disciplinas, 0)
        self.assertEqual(self.janela.limite_atual.text(), "6")

    def test_maior_limite_permitido_reabre_na_tela(self):
        self.abrir_perfil(self.janela, "Estudante")
        self.janela.limite_disciplinas.setValue(MAX_LIMITE_DISCIPLINAS)
        with patch("mega_moodle.views.gui.QMessageBox.information"):
            self.janela._salvar_limite()
        reaberta = self.abrir_janela(criar_controller(self.caminho))
        self.abrir_perfil(reaberta, "Estudante")
        self.assertEqual(reaberta.limite_disciplinas.value(), MAX_LIMITE_DISCIPLINAS)
        self.assertEqual(reaberta.limite_atual.text(), str(MAX_LIMITE_DISCIPLINAS))

    def test_limite_antigo_incompativel_mantem_tela_de_cadastro(self):
        banco = self.cadastro.estudante_dao.banco
        self.cadastro.cadastrar_usuario(10, "Usuário de teste", "Estudante")
        banco.executar_atualizacao(
            "UPDATE estudante SET limite_disciplinas = ? WHERE id = ?",
            (MAX_LIMITE_DISCIPLINAS + 1, 10),
        )
        reaberta = self.abrir_janela(criar_controller(self.caminho))
        tela = reaberta.centralWidget()
        with patch("mega_moodle.views.gui.QMessageBox.warning") as aviso:
            self.abrir_perfil(reaberta, "Estudante")
            aviso.assert_called_once()
        self.assertIs(reaberta.centralWidget(), tela)
        self.assertIsNone(reaberta.estudante_controller)

    def test_disponibilidade_persiste_e_falha_preserva_a_tela(self):
        self.abrir_perfil(self.janela, "Estudante")
        self.janela._registrar_disponibilidade()
        self.assertEqual(self.janela.lista.count(), 1)

        self.janela.inicio.setTime(QTime(9, 0))
        with patch.object(
            self.cadastro.disponibilidade_dao, "registrar", return_value=StatusPersistencia.ERRO
        ), patch("mega_moodle.views.gui.QMessageBox.warning") as aviso:
            self.janela._registrar_disponibilidade()
            aviso.assert_called_once()
        self.assertEqual(self.janela.lista.count(), 1)
        self.assertEqual(self.janela.inicio.time(), QTime(9, 0))

        reaberta = self.abrir_janela(criar_controller(self.caminho))
        self.abrir_perfil(reaberta, "Estudante")
        self.assertEqual(reaberta.lista.count(), 1)
        self.assertIn("08:00 às 12:00", reaberta.lista.item(0).text())

    def test_sair_volta_para_tela_de_cadastro(self):
        self.abrir_perfil(self.janela, "Administrador")
        self.assertIsNotNone(self.janela.administrador_controller)
        self.janela._voltar_cadastro()
        self.assertIsNone(self.janela.administrador_controller)
        self.assertTrue(hasattr(self.janela, "nome_usuario"))

        self.abrir_perfil(self.janela, "Estudante")
        self.assertIsNotNone(self.janela.estudante_controller)
        self.janela._voltar_cadastro()
        self.assertIsNone(self.janela.estudante_controller)
        self.assertTrue(hasattr(self.janela, "nome_usuario"))
