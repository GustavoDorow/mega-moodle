import sqlite3
import unittest
from datetime import time
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from mega_moodle.daos.status_persistencia import StatusPersistencia
from mega_moodle.main import criar_controller
from mega_moodle.models.dia_semana import DiaSemana
from mega_moodle.models.tipo_disciplina import TipoDisciplina


class FluxosTest(unittest.TestCase):
    def setUp(self):
        self.pasta = TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.caminho = Path(self.pasta.name) / "teste.db"
        self.cadastro = criar_controller(self.caminho)
        self.cadastro.cadastrar_usuario(1, "Administrador", "Administrador")
        self.cadastro.cadastrar_usuario(2, "David", "Estudante")
        self.admin = self.cadastro.administrador_controller
        self.estudante = self.cadastro.estudante_controller

    def cadastrar_disciplina(self, codigo="INE5608"):
        return self.admin.cadastrar_disciplina(
            codigo, "Análise e Projeto de Sistemas", 72, 4, TipoDisciplina.OBRIGATORIA
        )

    def registrar_disponibilidade(self):
        return self.estudante.registrar_disponibilidade(
            DiaSemana.SEGUNDA, time(8), time(12)
        )

    def test_dados_permanecem_ao_reabrir_e_renomear_estudante(self):
        self.assertTrue(self.cadastrar_disciplina(" ine5608 ").sucesso)
        self.assertTrue(self.registrar_disponibilidade().sucesso)

        reaberto = criar_controller(self.caminho)
        self.assertTrue(reaberto.cadastrar_usuario(9, "Outro admin", "Administrador").sucesso)
        self.assertTrue(reaberto.cadastrar_usuario(2, "David atualizado", "Estudante").sucesso)
        self.assertEqual(reaberto.administrador_controller.disciplinas[0].codigo, "INE5608")
        estudante = reaberto.estudante_controller.estudante
        self.assertEqual(estudante.nome, "David atualizado")
        self.assertEqual(estudante.disponibilidades[0].hora_inicio, time(8))
        self.assertEqual(estudante.disponibilidades[0].dia_semana, DiaSemana.SEGUNDA)

    def test_codigo_duplicado_nao_adiciona_disciplina(self):
        self.assertTrue(self.cadastrar_disciplina().sucesso)
        self.assertFalse(self.cadastrar_disciplina("ine5608").sucesso)
        self.assertEqual(len(self.admin.disciplinas), 1)
        self.assertEqual(len(self.cadastro.disciplina_dao.listar()), 1)

    def test_dados_invalidos_nao_chamam_dao(self):
        with patch.object(self.cadastro.disciplina_dao, "cadastrar") as salvar:
            self.assertFalse(self.cadastrar_disciplina(" ").sucesso)
            salvar.assert_not_called()
        with patch.object(self.cadastro.disponibilidade_dao, "registrar") as salvar:
            resultado = self.estudante.registrar_disponibilidade(
                DiaSemana.SEGUNDA, time(12), time(8)
            )
            self.assertFalse(resultado.sucesso)
            salvar.assert_not_called()
        self.assertEqual(self.admin.disciplinas, [])
        self.assertEqual(self.estudante.estudante.disponibilidades, [])

    def test_falha_de_escrita_nao_altera_memoria(self):
        with patch.object(
            self.cadastro.disciplina_dao, "cadastrar", return_value=StatusPersistencia.ERRO
        ):
            self.assertFalse(self.cadastrar_disciplina().sucesso)
        with patch.object(
            self.cadastro.disponibilidade_dao, "registrar", return_value=StatusPersistencia.ERRO
        ):
            self.assertFalse(self.registrar_disponibilidade().sucesso)
        self.assertEqual(self.admin.disciplinas, [])
        self.assertEqual(self.estudante.estudante.disponibilidades, [])

    def test_estudantes_nao_compartilham_disponibilidades(self):
        self.registrar_disponibilidade()
        self.cadastro.cadastrar_usuario(3, "Gustavo", "Estudante")
        self.assertEqual(self.cadastro.estudante_controller.estudante.disponibilidades, [])
        self.assertEqual(len(self.cadastro.disponibilidade_dao.listar(2)), 1)

    def test_falha_de_leitura_nao_abre_perfil(self):
        cadastro = criar_controller(self.caminho)
        with patch.object(cadastro.disciplina_dao, "listar", side_effect=sqlite3.OperationalError):
            resultado = cadastro.cadastrar_usuario(1, "Admin", "Administrador")
        self.assertFalse(resultado.sucesso)
        self.assertIsNone(cadastro.administrador_controller)

    def test_falha_no_commit_faz_rollback(self):
        # A FK adiada permite o INSERT e falha somente ao confirmar a transação.
        with sqlite3.connect(self.caminho) as conexao:
            conexao.execute("""
                CREATE TABLE teste_commit (
                    estudante_id INTEGER REFERENCES estudante(id)
                    DEFERRABLE INITIALLY DEFERRED
                )
            """)
        banco = self.cadastro.estudante_dao.banco
        with self.assertLogs(level="ERROR"):
            linhas = banco.executar_atualizacao(
                "INSERT INTO teste_commit (estudante_id) VALUES (?)", (999,)
            )
        self.assertEqual(linhas, -1)
        self.assertEqual(banco.consultar("SELECT * FROM teste_commit"), [])

    def test_fk_impede_disponibilidade_sem_estudante(self):
        self.estudante.estudante.id = 999
        with self.assertLogs(level="ERROR"):
            resultado = self.registrar_disponibilidade()
        self.assertFalse(resultado.sucesso)
        self.assertEqual(self.estudante.estudante.disponibilidades, [])
        self.assertEqual(self.cadastro.disponibilidade_dao.listar(999), [])
