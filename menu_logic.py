from PyQt5 import QtWidgets
import mysql.connector
import sys
from menu_ui import Ui_MainWindow
from user_session import UserSession
# Importe as classes necessárias dos arquivos de lógica existentes
from estoq_updater_logic import EstoqueUpdaterApp
from enviar_conferencia_logic import ConferenciaLogic
from mapas_financeiros_logic import MapasFinanceirosLogic
from conferencias_logic import ConferenciasApp
from transferencias_logic import TransferenciasApp
# Importe a classe FuncionariosLogic
from funcionarios_logic import FuncionariosLogic
from lojas_logic import StoreLogic
from atualizar_logic import AtualizadorSistema
from notas_fiscais_logic import NotasFiscaisLogic
from cheques_logic import ChequesApp
from promissorias_logic import PromissoriasApp

class MainWindowLogic(QtWidgets.QMainWindow):
    def __init__(self, session):
        super(MainWindowLogic, self).__init__()
        self.session = session
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.set_username_on_label()
        # Conecte os eventos de clique aos métodos correspondentes
        self.ui.pushButton_7.clicked.connect(self.open_estoque_updater)
        self.ui.pushButton_8.clicked.connect(self.open_enviar_conferencia)
        self.ui.pushButton_31.clicked.connect(self.open_mapas_financeiros)
        self.ui.pushButton_5.clicked.connect(self.open_conferencias)
        self.ui.pushButton_18.clicked.connect(self.open_transferencias)
        # Conecte o evento de clique do pushButton_10 para abrir FuncionariosLogic
        self.ui.pushButton_10.clicked.connect(self.open_funcionarios)
        self.ui.pushButton_9.clicked.connect(self.open_lojas)
        self.ui.pushButton_19.clicked.connect(self.open_atualizador)
        self.ui.pushButton_11.clicked.connect(self.open_notas_fiscais)
        self.ui.pushButton_6.clicked.connect(self.open_cheques)
        self.ui.pushButton_12.clicked.connect(self.open_promissorias)

    def get_mysql_connection(self):
        return mysql.connector.connect(
            host='34.151.192.214',
            user='arthuraml',
            password='Ij{p=6$Y2Wits7bAo',
            database='bbcia'
        )

    def set_username_on_label(self):
        usuario_id = self.session.get_user()
        mysql_conn = self.get_mysql_connection()
        cursor = mysql_conn.cursor()
        cursor.execute("SELECT nome FROM usuarios WHERE usuario = %s", (usuario_id,))
        usuario_nome = cursor.fetchone()
        mysql_conn.close()
        if usuario_nome:
            self.ui.label_7.setText(usuario_nome[0])
        else:
            self.ui.label_7.setText("Usuário não encontrado")

    def open_lojas(self):
        self.lojas_window = StoreLogic()
        self.lojas_window.show()

    def open_estoque_updater(self):
        self.estoque_updater_window = EstoqueUpdaterApp()
        self.estoque_updater_window.show()

    def open_enviar_conferencia(self):
        self.enviar_conferencia_window = ConferenciaLogic()
        self.enviar_conferencia_window.show()

    def open_mapas_financeiros(self):
        self.mapas_financeiros_window = MapasFinanceirosLogic()
        self.mapas_financeiros_window.show()

    def open_conferencias(self):
        self.conferencias_window = ConferenciasApp()
        self.conferencias_window.show()

    def open_transferencias(self):
        self.transferencias_window = TransferenciasApp()
        self.transferencias_window.show()

    # Método para abrir a janela FuncionariosLogic
    def open_funcionarios(self):
        self.funcionarios_window = FuncionariosLogic()
        self.funcionarios_window.show()

    def open_atualizador(self):
        self.atualizador_window = AtualizadorSistema()
        self.atualizador_window.show()

    def open_notas_fiscais(self):
        self.notas_fiscais_window = NotasFiscaisLogic()
        self.notas_fiscais_window.show()

    def open_cheques(self):
        self.cheques_window = ChequesApp()
        self.cheques_window.show()

    def open_promissorias(self):
        self.promissorias_window = PromissoriasApp()
        self.promissorias_window.show()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    session = UserSession()
    MainWindow = MainWindowLogic(session)
    MainWindow.show()
    sys.exit(app.exec_())
