import os
import sqlite3
import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from mega_moodle.controllers.resultado_operacao import ResultadoOperacao
from mega_moodle.daos.banco_dados import BancoDados
from mega_moodle.daos.historico_dao import HistoricoDAO
from mega_moodle.daos.status_persistencia import StatusPersistencia
from mega_moodle.main import criar_controller
from mega_moodle.models.disciplina import Disciplina
from mega_moodle.models.estudante import Estudante
from mega_moodle.models.tipo_disciplina import TipoDisciplina
from mega_moodle.views.gui import MegaMoodleWindow


class HistoricoModelTest(unittest.TestCase):
    def setUp(self):
        self.d1 = Disciplina("INE5608", "APS", 72, 4, TipoDisciplina.OBRIGATORIA)
        self.d2 = Disciplina("INE5609", "Cálculo", 72, 1, TipoDisciplina.OBRIGATORIA)

    def test_disciplinas_concluidas_inicia_vazia_e_independente(self):
        e1 = Estudante(1, "David")
        e2 = Estudante(2, "Gustavo")
        self.assertEqual(e1.disciplinas_concluidas, [])
        self.assertEqual(e2.disciplinas_concluidas, [])
        self.assertIsNot(e1.disciplinas_concluidas, e2.disciplinas_concluidas)

    def test_registrar_disciplina_concluida_adiciona_e_retorna_true(self):
        e = Estudante(1, "David")
        self.assertTrue(e.registrar_disciplina_concluida(self.d1))
        self.assertEqual(len(e.disciplinas_concluidas), 1)
        self.assertEqual(e.disciplinas_concluidas[0].codigo, "INE5608")

    def test_registrar_duplicado_por_codigo_retorna_false_e_preserva_lista(self):
        e = Estudante(1, "David")
        self.assertTrue(e.registrar_disciplina_concluida(self.d1))
        # Mesmo código com outro objeto/nome
        d1_copia = Disciplina("INE5608", "Outro Nome", 90, 5, TipoDisciplina.OPTATIVA)
        self.assertFalse(e.registrar_disciplina_concluida(d1_copia))
        self.assertEqual(len(e.disciplinas_concluidas), 1)
        self.assertEqual(e.disciplinas_concluidas[0].nome, "APS")

    def test_estudantes_diferentes_podem_concluir_mesma_disciplina(self):
        e1 = Estudante(1, "David")
        e2 = Estudante(2, "Gustavo")
        self.assertTrue(e1.registrar_disciplina_concluida(self.d1))
        self.assertTrue(e2.registrar_disciplina_concluida(self.d1))
        self.assertEqual(len(e1.disciplinas_concluidas), 1)
        self.assertEqual(len(e2.disciplinas_concluidas), 1)


class HistoricoDAOTest(unittest.TestCase):
    def setUp(self):
        self.pasta = TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.caminho = Path(self.pasta.name) / "teste_historico.db"
        self.banco = BancoDados(self.caminho)
        self.banco.inicializar()
        self.dao = HistoricoDAO(self.banco)

        # Insere estudante e disciplina para testes de FK
        self.banco.executar_atualizacao(
            "INSERT INTO estudante (id, nome) VALUES (?, ?)", (1, "David")
        )
        self.banco.executar_atualizacao(
            "INSERT INTO estudante (id, nome) VALUES (?, ?)", (2, "Gustavo")
        )
        self.banco.executar_atualizacao(
            """
            INSERT INTO disciplina (codigo, nome, carga_horaria, fase_sugerida, tipo)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("INE5608", "APS", 72, 4, TipoDisciplina.OBRIGATORIA.value),
        )
        self.banco.executar_atualizacao(
            """
            INSERT INTO disciplina (codigo, nome, carga_horaria, fase_sugerida, tipo)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("INE5609", "Cálculo", 72, 1, TipoDisciplina.OBRIGATORIA.value),
        )

    def test_inserir_concluida_retorna_ok(self):
        status = self.dao.registrar(1, "INE5608")
        self.assertIs(status, StatusPersistencia.OK)

    def test_inserir_duplicada_retorna_duplicado(self):
        self.dao.registrar(1, "INE5608")
        status = self.dao.registrar(1, "INE5608")
        self.assertIs(status, StatusPersistencia.DUPLICADO)

    def test_estudantes_diferentes_mesma_disciplina_permite_pk_composta(self):
        status1 = self.dao.registrar(1, "INE5608")
        status2 = self.dao.registrar(2, "INE5608")
        self.assertIs(status1, StatusPersistencia.OK)
        self.assertIs(status2, StatusPersistencia.OK)

    def test_violacao_fk_retorna_erro_e_nao_grava(self):
        with self.assertLogs(level="ERROR"):
            status_estudante_invalido = self.dao.registrar(999, "INE5608")
        self.assertIs(status_estudante_invalido, StatusPersistencia.ERRO)

        with self.assertLogs(level="ERROR"):
            status_disciplina_invalida = self.dao.registrar(1, "NAOEXISTE")
        self.assertIs(status_disciplina_invalida, StatusPersistencia.ERRO)

    def test_listar_concluidas_com_join_retorna_disciplinas(self):
        self.dao.registrar(1, "INE5609")
        self.dao.registrar(1, "INE5608")

        concluidas = self.dao.listar_concluidas(1)
        self.assertEqual(len(concluidas), 2)
        # Ordenado por código
        self.assertEqual(concluidas[0].codigo, "INE5608")
        self.assertEqual(concluidas[0].nome, "APS")
        self.assertEqual(concluidas[0].carga_horaria, 72)
        self.assertEqual(concluidas[0].fase_sugerida, 4)
        self.assertEqual(concluidas[0].tipo, TipoDisciplina.OBRIGATORIA)
        self.assertEqual(concluidas[1].codigo, "INE5609")

        # Estudante 2 não tem concluídas
        self.assertEqual(self.dao.listar_concluidas(2), [])


class HistoricoControllerTest(unittest.TestCase):
    def setUp(self):
        self.pasta = TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.caminho = Path(self.pasta.name) / "teste_ctrl.db"
        self.cadastro = criar_controller(self.caminho)

        # Cadastra admin e cria disciplina
        self.cadastro.cadastrar_usuario(1, "Admin", "Administrador")
        self.admin = self.cadastro.administrador_controller
        self.admin.cadastrar_disciplina(
            "INE5608", "APS", 72, 4, TipoDisciplina.OBRIGATORIA
        )
        self.admin.cadastrar_disciplina(
            "INE5609", "Cálculo", 72, 1, TipoDisciplina.OBRIGATORIA
        )

        # Cadastra estudante
        self.cadastro.cadastrar_usuario(2, "David", "Estudante")
        self.estudante_ctrl = self.cadastro.estudante_controller
        self.d1 = self.admin.disciplinas[0]
        self.d2 = self.admin.disciplinas[1]

    def test_gravacao_no_banco_ocorre_antes_de_mutar_entidade(self):
        dao = self.estudante_ctrl.historico_dao
        original_registrar = dao.registrar

        def interceptar_registrar(estudante_id, codigo):
            # No momento da chamada ao DAO, o Model ainda não deve ter a disciplina
            self.assertEqual(len(self.estudante_ctrl.estudante.disciplinas_concluidas), 0)
            return original_registrar(estudante_id, codigo)

        with patch.object(dao, "registrar", side_effect=interceptar_registrar) as spy:
            resultado = self.estudante_ctrl.registrar_disciplina_concluida(self.d1)
            self.assertTrue(resultado.sucesso)
            spy.assert_called_once_with(2, "INE5608")

        self.assertEqual(len(self.estudante_ctrl.estudante.disciplinas_concluidas), 1)
        self.assertEqual(self.estudante_ctrl.estudante.disciplinas_concluidas[0].codigo, "INE5608")

    def test_sucesso_devolve_copia_das_disciplinas_no_dto(self):
        resultado = self.estudante_ctrl.registrar_disciplina_concluida(self.d1)
        self.assertTrue(resultado.sucesso)
        self.assertIsNotNone(resultado.disciplinas)
        self.assertEqual(len(resultado.disciplinas), 1)
        self.assertEqual(resultado.disciplinas[0].codigo, "INE5608")

    def test_duplicado_retorna_insucesso_e_nao_altera_model(self):
        self.assertTrue(self.estudante_ctrl.registrar_disciplina_concluida(self.d1).sucesso)
        resultado = self.estudante_ctrl.registrar_disciplina_concluida(self.d1)
        self.assertFalse(resultado.sucesso)
        self.assertIn("já registrada", resultado.mensagem.lower())
        self.assertEqual(len(self.estudante_ctrl.estudante.disciplinas_concluidas), 1)

    def test_erro_de_persistencia_nao_altera_model(self):
        with patch.object(
            self.estudante_ctrl.historico_dao,
            "registrar",
            return_value=StatusPersistencia.ERRO,
        ):
            resultado = self.estudante_ctrl.registrar_disciplina_concluida(self.d1)
            self.assertFalse(resultado.sucesso)
            self.assertIn("não foi possível", resultado.mensagem.lower())

        self.assertEqual(self.estudante_ctrl.estudante.disciplinas_concluidas, [])

    def test_abrir_perfil_carrega_historico_e_catalogo(self):
        self.estudante_ctrl.registrar_disciplina_concluida(self.d1)

        reaberto = criar_controller(self.caminho)
        res = reaberto.cadastrar_usuario(2, "David", "Estudante")
        self.assertTrue(res.sucesso)
        ctrl = reaberto.estudante_controller
        self.assertEqual(len(ctrl.estudante.disciplinas_concluidas), 1)
        self.assertEqual(ctrl.estudante.disciplinas_concluidas[0].codigo, "INE5608")
        self.assertEqual(len(ctrl.catalogo_disciplinas), 2)

    def test_falha_na_leitura_do_historico_nao_abre_perfil(self):
        reaberto = criar_controller(self.caminho)
        with patch.object(
            reaberto.historico_dao, "listar_concluidas", side_effect=sqlite3.OperationalError
        ):
            res = reaberto.cadastrar_usuario(2, "David", "Estudante")
            self.assertFalse(res.sucesso)
            self.assertIsNone(reaberto.estudante_controller)


class HistoricoGUITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.pasta = TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.caminho = Path(self.pasta.name) / "teste_gui_hist.db"
        self.cadastro = criar_controller(self.caminho)
        self.janela = MegaMoodleWindow(self.cadastro)
        self.addCleanup(self.janela.close)

    def abrir_perfil(self, janela, perfil, id_usuario=10, nome="Usuário Teste"):
        janela.identificacao.setValue(id_usuario)
        janela.nome_usuario.setText(nome)
        janela.perfil.setCurrentText(perfil)
        janela._cadastrar_usuario()

    def test_catalogo_vazio_desabilita_registro(self):
        # Abre perfil do estudante sem nenhuma disciplina cadastrada no sistema
        self.abrir_perfil(self.janela, "Estudante", id_usuario=2, nome="David")
        self.assertFalse(self.janela.botao_registrar_concluida.isEnabled())
        self.assertFalse(self.janela.disciplina_concluida.isEnabled())
        self.assertEqual(self.janela.lista_concluidas.count(), 0)

    def test_fluxo_completo_conclusao_duplicidade_e_persistencia(self):
        # 1. Admin cadastra disciplina
        self.abrir_perfil(self.janela, "Administrador", id_usuario=1, nome="Admin")
        self.janela.codigo.setText("INE5608")
        self.janela.nome_disciplina.setText("APS")
        self.janela._cadastrar_disciplina()
        self.janela.close()

        # 2. Estudante abre e registra a disciplina
        janela_estudante = MegaMoodleWindow(criar_controller(self.caminho))
        self.addCleanup(janela_estudante.close)
        self.abrir_perfil(janela_estudante, "Estudante", id_usuario=2, nome="David")

        self.assertTrue(janela_estudante.botao_registrar_concluida.isEnabled())
        self.assertEqual(janela_estudante.disciplina_concluida.count(), 1)
        self.assertEqual(janela_estudante.lista_concluidas.count(), 0)

        # Confirma registro
        with patch("mega_moodle.views.gui.QMessageBox.information") as info:
            janela_estudante._registrar_disciplina_concluida()
            info.assert_called_once()
        self.assertEqual(janela_estudante.lista_concluidas.count(), 1)
        self.assertIn("INE5608", janela_estudante.lista_concluidas.item(0).text())

        # 3. Tenta registrar a mesma disciplina novamente (duplicidade)
        with patch("mega_moodle.views.gui.QMessageBox.warning") as aviso, patch(
            "mega_moodle.views.gui.QMessageBox.information"
        ) as info:
            janela_estudante._registrar_disciplina_concluida()
            aviso.assert_called_once()
            info.assert_not_called()
        self.assertEqual(janela_estudante.lista_concluidas.count(), 1)

        # 4. Reabre o estudante e confere que o histórico permanece
        janela_estudante.close()
        reaberta = MegaMoodleWindow(criar_controller(self.caminho))
        self.addCleanup(reaberta.close)
        self.abrir_perfil(reaberta, "Estudante", id_usuario=2, nome="David")
        self.assertEqual(reaberta.lista_concluidas.count(), 1)
        self.assertIn("INE5608", reaberta.lista_concluidas.item(0).text())

        # 5. Abre outro estudante: o histórico deve ser independente (vazio)
        reaberta2 = MegaMoodleWindow(criar_controller(self.caminho))
        self.addCleanup(reaberta2.close)
        self.abrir_perfil(reaberta2, "Estudante", id_usuario=3, nome="Gustavo")
        self.assertEqual(reaberta2.lista_concluidas.count(), 0)

    def test_falha_de_gravacao_preserva_tela_e_emite_aviso(self):
        # Admin cadastra disciplina
        self.abrir_perfil(self.janela, "Administrador", id_usuario=1, nome="Admin")
        self.janela.codigo.setText("INE5608")
        self.janela.nome_disciplina.setText("APS")
        self.janela._cadastrar_disciplina()
        self.janela.close()

        # Abre estudante
        janela_estudante = MegaMoodleWindow(criar_controller(self.caminho))
        self.addCleanup(janela_estudante.close)
        self.abrir_perfil(janela_estudante, "Estudante", id_usuario=2, nome="David")

        # Simula erro no DAO
        with patch.object(
            janela_estudante.estudante_controller.historico_dao,
            "registrar",
            return_value=StatusPersistencia.ERRO,
        ), patch("mega_moodle.views.gui.QMessageBox.warning") as aviso, patch(
            "mega_moodle.views.gui.QMessageBox.information"
        ) as info:
            janela_estudante._registrar_disciplina_concluida()
            aviso.assert_called_once()
            info.assert_not_called()

        self.assertEqual(janela_estudante.lista_concluidas.count(), 0)
        self.assertEqual(janela_estudante.estudante_controller.estudante.disciplinas_concluidas, [])
