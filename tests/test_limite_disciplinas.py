import sqlite3
import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from mega_moodle.daos.banco_dados import BancoDados
from mega_moodle.daos.estudante_dao import EstudanteDAO
from mega_moodle.daos.status_persistencia import StatusPersistencia
from mega_moodle.main import criar_controller
from mega_moodle.models.estudante import MAX_LIMITE_DISCIPLINAS, Estudante


class LimiteModelTest(unittest.TestCase):
    def test_validacao_nao_altera_model_e_definicao_atualiza(self):
        estudante = Estudante(1, "Gustavo")
        self.assertEqual(estudante.limite_disciplinas, 0)
        self.assertIs(estudante.validar_limite_disciplinas(4), True)
        self.assertEqual(estudante.limite_disciplinas, 0)
        self.assertIs(estudante.definir_limite_disciplinas(4), True)
        self.assertEqual(estudante.limite_disciplinas, 4)
        for invalido in (0, -1, 1.5, "4", True, False, None, MAX_LIMITE_DISCIPLINAS + 1, 2**63):
            with self.subTest(limite=invalido):
                self.assertIs(estudante.validar_limite_disciplinas(invalido), False)
                self.assertIs(estudante.definir_limite_disciplinas(invalido), False)
                self.assertEqual(estudante.limite_disciplinas, 4)

    def test_limites_minimo_e_maximo_sao_validos(self):
        estudante = Estudante(1, "Gustavo")
        for limite in (1, MAX_LIMITE_DISCIPLINAS):
            with self.subTest(limite=limite):
                self.assertIs(estudante.validar_limite_disciplinas(limite), True)
                self.assertIs(estudante.definir_limite_disciplinas(limite), True)
                self.assertEqual(estudante.limite_disciplinas, limite)


class LimitePersistenciaTest(unittest.TestCase):
    def setUp(self):
        pasta = TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.caminho = Path(pasta.name) / "teste.db"
        self.cadastro = criar_controller(self.caminho)
        self.cadastro.cadastrar_usuario(2, "Gustavo", "Estudante")
        self.controller = self.cadastro.estudante_controller
        self.dao = self.cadastro.estudante_dao

    def test_salva_e_reabre_com_nome_atualizado(self):
        resultado = self.controller.definir_limite_disciplinas(4)
        self.assertTrue(resultado.sucesso)
        self.assertEqual(resultado.limite, 4)
        self.assertEqual(self.controller.estudante.limite_disciplinas, 4)
        reaberto = criar_controller(self.caminho)
        self.assertTrue(reaberto.cadastrar_usuario(2, "Novo nome", "Estudante").sucesso)
        self.assertEqual(reaberto.estudante_controller.estudante.limite_disciplinas, 4)
        self.assertEqual(reaberto.estudante_controller.estudante.nome, "Novo nome")

    def test_invalidos_nao_chamam_dao(self):
        self.controller.definir_limite_disciplinas(4)
        with patch.object(self.dao, "atualizar_limite") as salvar:
            for invalido in (0, -2, 2.5, "4", True, None, MAX_LIMITE_DISCIPLINAS + 1, 2**63, 10**100):
                with self.subTest(limite=invalido):
                    resultado = self.controller.definir_limite_disciplinas(invalido)
                    self.assertFalse(resultado.sucesso)
                    self.assertIsNone(resultado.limite)
            salvar.assert_not_called()
        self.assertEqual(self.controller.estudante.limite_disciplinas, 4)
        self.assertEqual(self.dao.buscar_por_id(2).limite_disciplinas, 4)

    def test_gravacao_acontece_antes_da_mutacao(self):
        atualizar = self.dao.atualizar_limite

        def gravar(identificacao, limite):
            self.assertEqual(self.controller.estudante.limite_disciplinas, 0)
            return atualizar(identificacao, limite)

        with patch.object(self.dao, "atualizar_limite", side_effect=gravar) as salvar:
            self.assertTrue(self.controller.definir_limite_disciplinas(4).sucesso)
            salvar.assert_called_once_with(2, 4)
        self.assertEqual(self.controller.estudante.limite_disciplinas, 4)

    def test_falha_real_de_escrita_preserva_banco_e_model(self):
        self.controller.definir_limite_disciplinas(4)
        with closing(sqlite3.connect(self.caminho)) as conexao, conexao:
            conexao.execute("""
                CREATE TRIGGER impedir_limite BEFORE UPDATE OF limite_disciplinas
                ON estudante BEGIN SELECT RAISE(ABORT, 'falha simulada'); END
            """)
        with self.assertLogs(level="ERROR"):
            self.assertFalse(self.controller.definir_limite_disciplinas(6).sucesso)
        self.assertEqual(self.controller.estudante.limite_disciplinas, 4)
        self.assertEqual(self.dao.buscar_por_id(2).limite_disciplinas, 4)

    def test_dao_retorna_erro_se_estudante_nao_existe(self):
        self.assertIs(self.dao.atualizar_limite(999, 4), StatusPersistencia.ERRO)

    def test_dao_recusa_valores_invalidos_sem_executar_sql(self):
        with patch.object(self.dao.banco, "executar_atualizacao") as salvar:
            for limite in (0, -1, True, 1.5, "4", None, MAX_LIMITE_DISCIPLINAS + 1, 2**63):
                with self.subTest(limite=limite):
                    self.assertIs(self.dao.atualizar_limite(2, limite), StatusPersistencia.ERRO)
            salvar.assert_not_called()
        self.assertEqual(self.dao.buscar_por_id(2).limite_disciplinas, 0)

    def test_valor_maximo_persiste_e_reabre(self):
        resultado = self.controller.definir_limite_disciplinas(MAX_LIMITE_DISCIPLINAS)
        self.assertTrue(resultado.sucesso)
        self.assertEqual(resultado.limite, MAX_LIMITE_DISCIPLINAS)
        reaberto = criar_controller(self.caminho)
        self.assertTrue(reaberto.cadastrar_usuario(2, "Gustavo", "Estudante").sucesso)
        self.assertEqual(
            reaberto.estudante_controller.estudante.limite_disciplinas,
            MAX_LIMITE_DISCIPLINAS,
        )

    def test_valor_antigo_incompativel_impede_carregar_perfil_sem_alterar_banco(self):
        # Simula um valor permitido pela versão anterior, antes da correção.
        with closing(sqlite3.connect(self.caminho)) as conexao, conexao:
            conexao.execute(
                "UPDATE estudante SET limite_disciplinas = ? WHERE id = ?",
                (MAX_LIMITE_DISCIPLINAS + 1, 2),
            )
        reaberto = criar_controller(self.caminho)
        self.assertFalse(reaberto.cadastrar_usuario(2, "Gustavo", "Estudante").sucesso)
        self.assertIsNone(reaberto.estudante_controller)
        with closing(sqlite3.connect(self.caminho)) as conexao:
            limite = conexao.execute(
                "SELECT limite_disciplinas FROM estudante WHERE id = 2"
            ).fetchone()[0]
        self.assertEqual(limite, MAX_LIMITE_DISCIPLINAS + 1)

    def test_falha_de_leitura_impede_abrir_perfil(self):
        for falha in (None, sqlite3.OperationalError("falha simulada")):
            with self.subTest(falha=falha):
                cadastro = criar_controller(self.caminho)
                with patch.object(
                    cadastro.estudante_dao, "buscar_por_id",
                    **({"side_effect": falha} if falha else {"return_value": None}),
                ):
                    self.assertFalse(cadastro.cadastrar_usuario(2, "Gustavo", "Estudante").sucesso)
                self.assertIsNone(cadastro.estudante_controller)


class MigracaoLimiteTest(unittest.TestCase):
    def test_banco_antigo_migra_sem_perder_dados_e_pode_reinicializar(self):
        with TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "antigo.db"
            with closing(sqlite3.connect(caminho)) as conexao, conexao:
                conexao.execute("CREATE TABLE estudante (id INTEGER PRIMARY KEY, nome TEXT NOT NULL)")
                conexao.execute("INSERT INTO estudante VALUES (7, 'Gustavo')")
            banco = BancoDados(caminho)
            banco.inicializar()
            dao = EstudanteDAO(banco)
            self.assertEqual(dao.buscar_por_id(7), Estudante(7, "Gustavo"))
            self.assertIs(dao.atualizar_limite(7, 4), StatusPersistencia.OK)
            banco.inicializar()
            self.assertEqual(dao.buscar_por_id(7).limite_disciplinas, 4)
            with self.assertLogs(level="ERROR"):
                linhas = banco.executar_atualizacao(
                    "UPDATE estudante SET limite_disciplinas = ? WHERE id = ?", (-1, 7)
                )
                self.assertEqual(linhas, -1)
            self.assertEqual(dao.buscar_por_id(7).limite_disciplinas, 4)
