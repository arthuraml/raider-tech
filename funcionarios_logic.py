from PyQt5 import QtWidgets, QtGui
import funcionarios_ui
import mysql.connector
from PyQt5.QtCore import Qt 
from PyQt5.QtWidgets import QMessageBox
import brutils.cpf

class FuncionariosLogic(QtWidgets.QDialog, funcionarios_ui.Ui_Dialog):
    def __init__(self, parent=None):
        super(FuncionariosLogic, self).__init__(parent)
        self.setupUi(self)

        # Conectar sinais e slots
        self.lineEdit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.pushButton.clicked.connect(self.cadastrar_funcionario)
        self.pushButton_2.clicked.connect(self.excluir_funcionario)
        self.pushButton_3.clicked.connect(self.alterar_senha)
        self.comboBox_2.currentIndexChanged.connect(self.exibir_funcionarios_loja)
        self.pushButton_4.clicked.connect(self.salvar_alteracoes)
        self.comboBox_2.currentIndexChanged.connect(self.set_funcionario_code)

        # Preencher comboboxes de lojas
        self.preencher_lojas()
        self.preencher_cargos()

        # Iniciar comboBoxes em branco
        self.comboBox_2.setCurrentIndex(-1)

    def preencher_cargos(self):
        # Modificação 1: Preencher o comboBox com os cargos possíveis
        cargo_options = [
            'Administrador',
            'Assistente',
            'Gerente',
            'Vendedor',
            'Caixa',
            'Vendedor Externo',
            'Delivery'
        ]
        for cargo in cargo_options:
            self.comboBox.addItem(cargo)

    def preencher_lojas(self):
        try:
            conexao = mysql.connector.connect(
                host='34.151.192.214',
                user='arthuraml',
                password='Ij{p=6$Y2Wits7bAo',
                database='bbcia'
            )

            cursor = conexao.cursor()
            query = "SELECT loja_cod, loja FROM lojas ORDER BY loja ASC"
            cursor.execute(query)

            self.comboBox_2.addItem("")  # Adiciona opção vazia

            for (loja_cod, loja) in cursor:
                item = f"{str(loja_cod).zfill(2)} - {loja}"
                self.comboBox_2.addItem(item)

            cursor.close()
            conexao.close()
        except mysql.connector.Error as err:
            print(f"Erro ao se conectar ao MySQL: {err}")

    def set_funcionario_code(self):
        loja_cod = self.comboBox_2.currentText().split(" - ")[0] if self.comboBox_2.currentIndex() > 0 else None
        if not loja_cod:
            self.label_7.setText("Selecione uma loja para gerar o código do funcionário")
            return

        try:
            conexao = mysql.connector.connect(
                host='34.151.192.214',
                user='arthuraml',
                password='Ij{p=6$Y2Wits7bAo',
                database='bbcia'
            )
            cursor = conexao.cursor()

            for i in range(1, 100):  # Supondo um limite de 99 funcionários por loja
                new_user_code = f"{loja_cod}{i:02d}"
                query = "SELECT EXISTS(SELECT 1 FROM usuarios WHERE usuario = %s)"
                cursor.execute(query, (new_user_code,))
                exists = cursor.fetchone()[0]

                if not exists:
                    self.label_7.setText(new_user_code)
                    break
        finally:
            if cursor and conexao.is_connected():
                cursor.close()
                conexao.close()

    def exibir_funcionarios_loja(self):
        if self.comboBox_2.currentIndex() > 0:  # Ignora a opção vazia
            loja_cod = self.comboBox_2.currentText().split(" - ")[0]

            try:
                conexao = mysql.connector.connect(
                    host='34.151.192.214',
                    user='arthuraml',
                    password='Ij{p=6$Y2Wits7bAo',
                    database='bbcia'
                )

                cursor = conexao.cursor()
                query = f"SELECT usuario, nome, cpf, cargo FROM usuarios WHERE loja_cod = '{loja_cod}' ORDER BY usuario ASC"
                cursor.execute(query)

                self.tableWidget.setRowCount(0)
                self.tableWidget.setColumnCount(4)  # Define o número de colunas
                self.tableWidget.setHorizontalHeaderLabels(['Usuário', 'Nome', 'CPF', 'Cargo'])

                # Define as larguras das colunas
                self.tableWidget.setColumnWidth(0, 50)
                self.tableWidget.setColumnWidth(1, 200)
                self.tableWidget.setColumnWidth(2, 100)
                self.tableWidget.setColumnWidth(3, 120)

                cargo_options = {
                    'master': 'Administrador',
                    'assistente': 'Assistente',
                    'gerente': 'Gerente',
                    'vendedor': 'Vendedor',
                    'caixa': 'Caixa',
                    'vendedor_externo': 'Vendedor Externo',
                    'delivery': 'Delivery'
                }

                for row_number, row_data in enumerate(cursor):
                    self.tableWidget.insertRow(row_number)
                    for column_number, data in enumerate(row_data):
                        if column_number == 3:  # Coluna de cargo
                            comboBox = QtWidgets.QComboBox()
                            for key, value in cargo_options.items():
                                comboBox.addItem(value, key)
                                if cargo_options.get(data) == value:
                                    comboBox.setCurrentIndex(comboBox.count() - 1)
                            self.tableWidget.setCellWidget(row_number, column_number, comboBox)
                        else:
                            item = QtWidgets.QTableWidgetItem(str(data))
                            if column_number == 0:  # Torna a coluna "Usuario" não editável
                                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                            self.tableWidget.setItem(row_number, column_number, item)

                cursor.close()
                conexao.close()
            except mysql.connector.Error as err:
                print(f"Erro ao se conectar ao MySQL: {err}")

    def salvar_alteracoes(self):
        conexao = None
        try:
            conexao = mysql.connector.connect(
                host='34.151.192.214',
                user='arthuraml',
                password='Ij{p=6$Y2Wits7bAo',
                database='bbcia'
            )

            cursor = conexao.cursor()

            cargo_options_reversed = {
                'Administrador': 'master',
                'Assistente': 'assistente',
                'Gerente': 'gerente',
                'Vendedor': 'vendedor',
                'Caixa': 'caixa',
                'Vendedor Externo': 'vendedor_externo',
                'Delivery': 'delivery'
            }

            row_count = self.tableWidget.rowCount()
            for row in range(row_count):
                usuario = self.tableWidget.item(row, 0).text()  # Coluna "Usuário" para identificar a linha
                nome = self.tableWidget.item(row, 1).text()
                cpf = self.tableWidget.item(row, 2).text()
                comboBox = self.tableWidget.cellWidget(row, 3)
                cargo = cargo_options_reversed[comboBox.currentText()]

                update_query = """
                UPDATE usuarios 
                SET nome = %s, cpf = %s, cargo = %s
                WHERE usuario = %s
                """
                cursor.execute(update_query, (nome, cpf, cargo, usuario))

            conexao.commit()
        except mysql.connector.Error as err:
            print(f"Erro ao se conectar ao MySQL: {err}")
        finally:
            if conexao is not None:
                conexao.close()
        QMessageBox.information(self, "Sucesso", "Dados salvos com sucesso")

    def cadastrar_funcionario(self):
        usuario = self.label_7.text()
        nome = self.lineEdit_2.text()
        cpf = self.lineEdit_3.text().replace('.', '').replace('-', '')
        cargo = self.comboBox.currentText()
        senha = self.lineEdit.text()

        # Modificação 4: Verificar se todos os campos estão preenchidos
        if not all([usuario, nome, cpf, cargo, senha]):
            QMessageBox.warning(self, "Aviso", "Todos os campos devem ser preenchidos!")
            return

        # Modificação 3: Validar CPF
        if not brutils.cpf.validate(cpf):
            QMessageBox.warning(self, "Aviso", "CPF inválido!")
            return

        # Mapeia o texto do comboBox para o valor correspondente no banco de dados
        cargo_options = {
            'Administrador': 'master',
            'Assistente': 'assistente',
            'Gerente': 'gerente',
            'Vendedor': 'vendedor',
            'Caixa': 'caixa',
            'Vendedor Externo': 'vendedor_externo',
            'Delivery': 'delivery'
        }
        cargo_db = cargo_options.get(cargo)

        senha = self.lineEdit.text()
        loja_cod = self.comboBox_2.currentText().split(" - ")[0] if self.comboBox_2.currentIndex() > 0 else ''
        loja = self.comboBox_2.currentText().split(" - ")[1] if self.comboBox_2.currentIndex() > 0 else ''

        try:
            conexao = mysql.connector.connect(
                host='34.151.192.214',
                user='arthuraml',
                password='Ij{p=6$Y2Wits7bAo',
                database='bbcia'
            )
            cursor = conexao.cursor()

            insert_query = """
            INSERT INTO usuarios (loja_cod, loja, usuario, senha, cargo, nome, cpf)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (loja_cod, loja, usuario, senha, cargo_db, nome, cpf))
            conexao.commit()
        except mysql.connector.Error as err:
            QMessageBox.critical(self, "Erro", f"Erro ao cadastrar funcionário: {err}")
        finally:
            if conexao.is_connected():
                cursor.close()
                conexao.close()

        # Limpa os campos
        self.lineEdit_2.clear()
        self.lineEdit_3.clear()
        self.lineEdit.clear()
        self.comboBox.setCurrentIndex(-1)

        # Atualiza o tableWidget e mostra mensagem de sucesso
        self.exibir_funcionarios_loja()
        QMessageBox.information(self, "Sucesso", "Cadastro de funcionário realizado com sucesso")


    def excluir_funcionario(self):
        selected_row = self.tableWidget.currentRow()
        if selected_row < 0:  # Verifica se alguma linha está selecionada
            QMessageBox.warning(self, "Aviso", "Selecione um funcionário para excluir")
            return
        
        usuario = self.tableWidget.item(selected_row, 0).text()
        confirm = QMessageBox.question(self, "Confirmar exclusão", 
                                    "Tem certeza que deseja excluir esse funcionário?",
                                    QMessageBox.Yes | QMessageBox.No)

        if confirm == QMessageBox.Yes:
            try:
                conexao = mysql.connector.connect(
                    host='34.151.192.214',
                    user='arthuraml',
                    password='Ij{p=6$Y2Wits7bAo',
                    database='bbcia'
                )

                cursor = conexao.cursor()
                delete_query = "DELETE FROM usuarios WHERE usuario = %s"
                cursor.execute(delete_query, (usuario,))
                conexao.commit()

                # Atualiza o tableWidget após a exclusão
                self.exibir_funcionarios_loja()

                QMessageBox.information(self, "Sucesso", "Funcionário excluído com sucesso")
            except mysql.connector.Error as err:
                QMessageBox.critical(self, "Erro", f"Erro ao se conectar ao MySQL: {err}")
            finally:
                if conexao:
                    conexao.close()
        self.set_funcionario_code()


    def alterar_senha(self):
        selected_row = self.tableWidget.currentRow()
        if selected_row < 0:  # Verifica se alguma linha está selecionada
            QMessageBox.warning(self, "Aviso", "Selecione um funcionário para alterar a senha")
            return

        nome_funcionario = self.tableWidget.item(selected_row, 1).text()  # Obtém o nome para exibir na mensagem
        usuario_funcionario = self.tableWidget.item(selected_row, 0).text()  # Obtém o usuário para atualizar a senha

        nova_senha, ok = QtWidgets.QInputDialog.getText(self, "Alterar Senha", f"Digite a nova senha para {nome_funcionario}:")

        if ok and nova_senha:
            try:
                conexao = mysql.connector.connect(
                    host='34.151.192.214',
                    user='arthuraml',
                    password='Ij{p=6$Y2Wits7bAo',
                    database='bbcia'
                )

                cursor = conexao.cursor()
                update_query = "UPDATE usuarios SET senha = %s WHERE usuario = %s"
                cursor.execute(update_query, (nova_senha, usuario_funcionario))
                conexao.commit()

                QMessageBox.information(self, "Sucesso", f"Senha do funcionário '{nome_funcionario}' alterada com sucesso")
            except mysql.connector.Error as err:
                QMessageBox.critical(self, "Erro", f"Erro ao se conectar ao MySQL: {err}")
            finally:
                if conexao:
                    conexao.close()

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    dialog = FuncionariosLogic()
    dialog.show()
    sys.exit(app.exec_())
