import sqlite3
import mysql.connector
import requests
import sys
import os
import subprocess
from PyQt5 import QtWidgets, QtCore
from atualizar_ui import Ui_Dialog

class AtualizadorSistema(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        super(AtualizadorSistema, self).__init__(parent)
        self.setupUi(self)

        # Obter versões
        self.versao_local = self.obter_versao_local()
        self.versao_atual = self.obter_versao_atual()

        # Exibir status da versão no textEdit
        self.atualizar_texto_versao()

        # Conectar o botão à função de atualização
        self.pushButton.clicked.connect(self.iniciar_atualizacao)

    def atualizar_texto_versao(self):
        mensagem = f"Versão do sistema neste computador: {self.versao_local}\n" \
                   f"Versão do sistema mais atualizada: {self.versao_atual}\n"
        if self.versao_local >= self.versao_atual:
            mensagem += "Sistema já está atualizado"
            self.pushButton.setEnabled(False)
        else:
            mensagem += "Nova versão disponível para atualização"
        self.textEdit.setText(mensagem)

    def iniciar_atualizacao(self):
        if self.versao_local == self.versao_atual:
            QtWidgets.QMessageBox.information(self, "Atualização", "Sistema já está atualizado")
        else:
            self.baixar_nova_versao()

    def baixar_nova_versao(self):
        url = "http://34.151.192.214/versao/retaguarda/main_logic.exe"
        resposta = requests.get(url, stream=True)

        tamanho_total = int(resposta.headers.get('content-length', 0))
        chunk_size = 1024
        bytes_baixados = 0

        progress_dialog = QtWidgets.QProgressDialog("Baixando atualização...", "Cancelar", 0, tamanho_total, self)
        progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        progress_dialog.show()

        with open("main_logic_novo.exe", 'wb') as arquivo:
            for dados in resposta.iter_content(chunk_size):
                bytes_baixados += len(dados)
                arquivo.write(dados)
                progress_dialog.setValue(bytes_baixados)
                if progress_dialog.wasCanceled():
                    break

        progress_dialog.close()

        if bytes_baixados >= tamanho_total:
            self.substituir_e_reiniciar()

    def substituir_e_reiniciar(self):
        arquivo_antigo = "main_logic_antigo.exe"
        arquivo_novo = "main_logic_novo.exe"
        arquivo_atual = "main_logic.exe"

        # Remover o antigo executável se ele já existir
        if os.path.exists(arquivo_antigo):
            os.remove(arquivo_antigo)

        # Renomear o executável atual para o nome antigo (opcional)
        os.rename(arquivo_atual, arquivo_antigo)

        # Renomear o novo executável para o nome atual
        os.rename(arquivo_novo, arquivo_atual)

        # Atualizar a versão no banco de dados local
        self.atualizar_versao_local(self.versao_atual)

        # Reiniciar o aplicativo
        subprocess.Popen([arquivo_atual])
        sys.exit()

    def atualizar_versao_local(self, nova_versao):
        conn = sqlite3.connect('bd/retaguarda.db')
        cursor = conn.cursor()
        # Atualizar a coluna 'versao_atual' na tabela 'config'
        cursor.execute("UPDATE config SET versao_atual = ?", (nova_versao,))
        conn.commit()
        conn.close()

    def obter_versao_local(self):
        # Conectar ao banco de dados SQLite
        conn = sqlite3.connect('bd/retaguarda.db')
        cursor = conn.cursor()
        cursor.execute("SELECT versao_atual FROM config")
        versao_local = cursor.fetchone()[0]
        conn.close()
        return versao_local

    def obter_versao_atual(self):
        # Conectar ao banco de dados MySQL
        conn = mysql.connector.connect(
            host='34.151.192.214',
            user='arthuraml',
            password='Ij{p=6$Y2Wits7bAo',
            database='bbcia'
        )
        cursor = conn.cursor()
        cursor.execute("SELECT versao_retaguarda FROM versao ORDER BY id DESC LIMIT 1")
        versao_atual = cursor.fetchone()[0]
        conn.close()
        return versao_atual

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = AtualizadorSistema()
    window.show()
    sys.exit(app.exec_())
