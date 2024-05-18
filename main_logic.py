from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox
import mysql.connector
import sys
from main_ui import Ui_loginWindow
from menu_logic import MainWindowLogic
from user_session import UserSession

class Login(QtWidgets.QDialog):
    def __init__(self):
        super(Login, self).__init__()
        self.ui = Ui_loginWindow()
        self.ui.setupUi(self)
        self.ui.entrarBotao.clicked.connect(self.check_credentials)
        self.ui.usuarioInput.returnPressed.connect(self.check_credentials)

    def get_mysql_connection(self):
        return mysql.connector.connect(
            host='34.151.192.214',
            user='arthuraml',
            password='Ij{p=6$Y2Wits7bAo',
            database='bbcia'
        )

    def check_credentials(self):
        entered_usuario_id = self.ui.usuarioInput.text()
        entered_senha = self.ui.senhaInput.text()

        if not entered_usuario_id.isnumeric():
            QMessageBox.warning(self, 'Error', 'ID do usuário inválido')
            return

        entered_usuario_id = int(entered_usuario_id)

        mysql_conn = self.get_mysql_connection()
        cursor = mysql_conn.cursor()
        cursor.execute("SELECT usuario, senha, cargo FROM usuarios WHERE usuario = %s AND senha = %s", (entered_usuario_id, entered_senha))
        credentials = cursor.fetchone()
        mysql_conn.close()

        if credentials:
            session = UserSession(entered_usuario_id, credentials[2])  # Agora, não usamos mais o campo loja
            self.MainWindow = MainWindowLogic(session)
            self.MainWindow.show()
            self.close()
        else:
            QMessageBox.warning(self, 'Error', 'Credenciais inválidas')

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Login()
    window.show()
    sys.exit(app.exec_())
