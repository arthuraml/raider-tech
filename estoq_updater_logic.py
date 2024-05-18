import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog
from estoq_updater_ui import Ui_Dialog
import geopandas as gpd
import pandas as pd
import mysql.connector

class EstoqueUpdaterApp(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self):
        super(EstoqueUpdaterApp, self).__init__()
        self.setupUi(self)
        self.pushButton.clicked.connect(self.analyze_file)
        self.pushButton_2.clicked.connect(self.update_database)
        self.selected_dbf_file_path = None  # Adiciona um atributo para armazenar o caminho do arquivo selecionado

    def convert_to_float(self, br_number):
        if isinstance(br_number, str):
            return float(br_number.replace(',', '.'))
        return br_number

    def convert_to_boolean(self, value):
        if value == "T":
            return 1
        elif value == "F":
            return 0
        else:
            return None

    def fetch_existing_data(self, conn):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM produtos")
        cols = cursor.column_names
        existing_data = pd.DataFrame(cursor.fetchall(), columns=cols)
        cursor.close()
        return existing_data

    def analyze_file(self):
        dbf_file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar arquivo de estoque", "", "DBF Files (*.dbf);;All Files (*)")
        if not dbf_file_path:  # Se nenhum arquivo foi selecionado, retorna e não faz nada
            return

        self.selected_dbf_file_path = dbf_file_path  # Armazena o caminho do arquivo selecionado

        gdf = gpd.read_file(dbf_file_path)
        gdf = gdf[['CODIGO', 'CBARRAS', 'NOME', 'CUSTO', 'PRECO', 'PRECOI', 'PRAZO', 'PRAZOI', 'MINIMO', 'CLASSE', 'CAPINT', 'JUROS', 'MEDIDA', 'CST', 'CSOSN', 'NCM', 'CEST', 'PONTA', 'PROMO']]
        gdf.columns = ['referencia', 'codigo_barras', 'nome_produto', 'custo_produto', 'preco_atacado_capital', 'preco_atacado_interior', 'preco_varejo_capital', 'preco_varejo_interior', 'minimo_atacado', 'classe', 'local', 'juros', 'unidade_medida', 'cst', 'csosn', 'ncm', 'cest', 'ponta', 'promo']

        conn = mysql.connector.connect(host='34.151.192.214', user='arthuraml', password='Ij{p=6$Y2Wits7bAo', database='bbcia')
        existing_data = self.fetch_existing_data(conn)

        gdf['referencia'] = gdf['referencia'].apply(lambda x: f"{int(x):05d}")
        for col in ['custo_produto', 'preco_atacado_capital', 'preco_atacado_interior', 'preco_varejo_capital', 'preco_varejo_interior', 'juros']:
            gdf[col] = gdf[col].apply(self.convert_to_float)
        gdf['ponta'] = gdf['ponta'].apply(self.convert_to_boolean)
        gdf['promo'] = gdf['promo'].apply(self.convert_to_boolean)
        gdf = gdf.where(pd.notnull(gdf), None)

        # Lista expandida para incluir as novas colunas de interesse
        monitored_columns = ['nome_produto', 'minimo_atacado', 'ponta', 'promo', 'custo_produto', 'preco_atacado_capital', 'preco_atacado_interior', 'preco_varejo_capital', 'preco_varejo_interior']
        changes_detected = []

        for index, row in gdf.iterrows():
            existing_row = existing_data[existing_data['referencia'] == row['referencia']]
            if not existing_row.empty:
                for col in monitored_columns:
                    old_value = existing_row.iloc[0][col]
                    new_value = row[col]
                    if old_value != new_value:
                        changes_detected.append((row['referencia'], col, old_value, new_value))

        if changes_detected:
            for change in changes_detected:
                self.textBrowser.append(f"Mudança detectada - Referência: {change[0]}, Coluna: {change[1]}, De: {change[2]}, Para: {change[3]}")
        else:
            self.textBrowser.append("Nenhuma alteração detectada")

        conn.close()

    def update_database(self):
        if not self.selected_dbf_file_path:  # Verifica se um arquivo foi selecionado
            self.textBrowser.append("Por favor, selecione um arquivo antes de tentar atualizar.")
            return

        # Utiliza o caminho do arquivo selecionado anteriormente
        gdf = gpd.read_file(self.selected_dbf_file_path)

        # Colunas selecionadas e renomeação
        gdf = gdf[['CODIGO', 'CBARRAS', 'NOME', 'CUSTO', 'PRECO', 'PRECOI', 'PRAZO', 'PRAZOI', 'MINIMO', 'PONTA', 'PROMO', 'CLASSE', 'CAPINT', 'JUROS', 'MEDIDA', 'CST', 'CSOSN', 'NCM', 'CEST']]
        gdf.columns = ['referencia', 'codigo_barras', 'nome_produto', 'custo_produto', 'preco_atacado_capital', 'preco_atacado_interior', 'preco_varejo_capital', 'preco_varejo_interior', 'minimo_atacado', 'ponta', 'promo', 'classe', 'local', 'juros', 'unidade_medida', 'cst', 'csosn', 'ncm', 'cest']

        # Processamento das colunas
        gdf['referencia'] = gdf['referencia'].apply(lambda x: f"{int(x):05d}")
        for col in ['custo_produto', 'preco_atacado_capital', 'preco_atacado_interior', 'preco_varejo_capital', 'preco_varejo_interior', 'juros']:
            gdf[col] = gdf[col].apply(self.convert_to_float)
        
        print("Valores originais de 'ponta' e 'promo' antes da conversão:")
        print(gdf[['ponta', 'promo']])
        gdf['ponta'] = gdf['ponta'].apply(self.convert_to_boolean)
        gdf['promo'] = gdf['promo'].apply(self.convert_to_boolean)
        gdf = gdf.where(pd.notnull(gdf), None)

        conn = mysql.connector.connect(host='34.151.192.214', user='arthuraml', password='Ij{p=6$Y2Wits7bAo', database='bbcia')
        cursor = conn.cursor()

        cursor.execute("DELETE FROM produtos")
        insert_query = """
        INSERT INTO produtos (referencia, codigo_barras, nome_produto, custo_produto, preco_atacado_capital, preco_atacado_interior, preco_varejo_capital, preco_varejo_interior, minimo_atacado, ponta, promo, classe, local, juros, unidade_medida, cst, csosn, ncm, cest) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        data_tuples = [tuple(x) for x in gdf.to_numpy()]
        cursor.executemany(insert_query, data_tuples)
        conn.commit()
        cursor.close()
        conn.close()
        self.textBrowser.append("Banco de dados atualizado")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mainWin = EstoqueUpdaterApp()
    mainWin.show()
    sys.exit(app.exec_())
