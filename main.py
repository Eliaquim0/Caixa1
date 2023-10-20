import os
os.environ["LC_ALL"] = "pt_BR.UTF-8"
from kivy.config import Config
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.metrics import dp
from datetime import datetime
from kivymd.app import MDApp
from kivymd.uix.datatables import MDDataTable
from kivy.uix.pagelayout import PageLayout
from kivy.lang import Builder
from kivy.graphics import Color, Rectangle
import sqlite3
from kivy.core.window import Window
from kivymd.uix.textfield import MDTextField
from kivymd.uix.pickers import MDDatePicker
from kivy.utils import get_color_from_hex 
from kivy.properties import Property
from kivy.clock import Clock
from kivy.uix.floatlayout import FloatLayout

Builder.load_file('styles.kv')
        

# Função para criar a tabela de transações no banco de dados SQLite
def create_transactions_table():
    conn = sqlite3.connect("CaixaApp.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            transaction_type TEXT,
            amount REAL,
            reason TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# Função para calcular o saldo com base nas transações no banco de dados
def calculate_balance_from_transactions():
    conn = sqlite3.connect("CaixaApp.db")
    cursor = conn.cursor()
    cursor.execute("SELECT transaction_type, amount FROM transactions")
    rows = cursor.fetchall()
    conn.close()

    balance = 0.0
    for row in rows:
        transaction_type, amount = row
        if transaction_type == "Depositar":
            balance += amount
        elif transaction_type == "Retirar":
            balance -= amount

    return balance
class BorderedButton(Button):
    def __init__(self, **kwargs):
        super(BorderedButton, self).__init__(**kwargs)
        self.border = (8, 8, 8, 8)  # Espessura da borda (esquerda, superior, direita, inferior)

class TransactionScreen(Screen):
    def __init__(self, transaction_type, **kwargs):
        super().__init__(**kwargs)
        self.transaction_type = transaction_type

        layout = BoxLayout(orientation='vertical', spacing=10, padding=10, size_hint=(None, None), height=300)
        layout.pos_hint = {'center_x': 0.45, 'center_y': 0.5}  # Centraliza o layout na tela

        self.amount_input = MDTextField(
            hint_text="Valor da transação",
            size_hint_x=None,
            width=200,
            foreground_color=(0, 0, 0, 1),
        )
        self.reason_input = MDTextField(
            hint_text="Motivo da transação",
            size_hint_x=None,
            width=200,
            foreground_color=(0, 0, 0, 1),
        )

        transaction_buttons_layout = BoxLayout(orientation='horizontal', spacing=5, padding=50, size_hint=(None, None), height=50)
        transaction_button = Button(
            text=transaction_type,
            background_color=(0.082, 0.447, 0.831, 1),
            size_hint=(None, None),
            width=100,
            height=50,
            color=(1, 1, 1, 1),
        )
        transaction_button.bind(on_press=self.show_confirmation_popup)

        return_button = Button(
            text="Retornar ao Menu Principal",
            background_color=(0.827, 0.180, 0.094, 1),
            size_hint=(None, None),
            width=200,
            height=50,
            color=(1, 1, 1, 1),
        )
        return_button.bind(on_press=self.return_to_main_menu)

        transaction_buttons_layout.add_widget(transaction_button)

        return_and_transaction_layout = BoxLayout(orientation='vertical', spacing=-35, padding=2, size_hint=(None, None), height=150)
        return_and_transaction_layout.add_widget(transaction_buttons_layout)
        return_and_transaction_layout.add_widget(return_button)

        layout.add_widget(self.amount_input)
        layout.add_widget(self.reason_input)
        layout.add_widget(return_and_transaction_layout)
        self.add_widget(layout)

    def show_confirmation_popup(self, instance):
        amount_str = self.amount_input.text
        try:
            amount = float(amount_str)
            reason = self.reason_input.text
            if amount > 0:
                if self.transaction_type == "Retirar" and amount > App.get_running_app().balance:
                    self.show_insufficient_funds_popup()
                else:
                    confirmation_message = (
                        f'Confirma a {self.transaction_type.lower()} de: {amount:.2f}?\n'
                        f'Motivo: {reason}'
                    )
                    confirmation_popup = ConfirmationPopup(
                        title=f'Confirmação de {self.transaction_type}',
                        content=Label(text=confirmation_message),
                        transaction_type=self.transaction_type,
                        transaction_amount=amount,
                        transaction_reason=reason,
                        transaction_screen=self,
                    )
                    confirmation_popup.bind(on_dismiss=self.clear_inputs)
                    confirmation_popup.open()
            else:
                self.amount_input.text = "Valor inválido"
        except ValueError:
            self.amount_input.text = "Digite um valor válido"

    def show_insufficient_funds_popup(self):
        popup_saldo_insuficiente = Popup(
            title="Saldo Insuficiente",
            size_hint=(None, None),
            size=(400, 250),
        )

        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        label = Label(
            text="Você não tem saldo suficiente para esta retirada.",
            halign='center'
        )
        layout.add_widget(label)

        button_layout = BoxLayout(orientation='horizontal', spacing=10, padding=10)
        button_layout.add_widget(Widget())
        ok_button = BorderedButton(text="OK", size_hint=(None, None), size=(100, 50))
        ok_button.bind(on_press=popup_saldo_insuficiente.dismiss)
        button_layout.add_widget(ok_button)

        layout.add_widget(button_layout)
        popup_saldo_insuficiente.content = layout
        popup_saldo_insuficiente.open()

    def clear_inputs(self, instance):
        self.amount_input.text = ''
        self.reason_input.text = ''

    def return_to_main_menu(self, instance):
        self.get_app().screen_manager.current = "main_screen"

    def get_app(self):
        return App.get_running_app()

    def update_extract_label(self):
        self.get_app().update_extract_label()

class ConfirmationPopup(Popup):
    def __init__(self, transaction_type, transaction_amount, transaction_reason, transaction_screen, **kwargs):
        super().__init__(**kwargs)
        self.transaction_type = transaction_type
        self.transaction_amount = transaction_amount
        self.transaction_reason = transaction_reason
        self.transaction_screen = transaction_screen

        confirmation_button = BorderedButton(
            text="Confirmar",
            background_color=(0.082, 0.447, 0.831, 1),
            size_hint=(None, None),
            width=100,
            height=50,
            color=(1, 1, 1, 1),  # Cor do texto
        )
        confirmation_button.bind(on_press=self.process_transaction)
        cancel_button = BorderedButton(
            text="Cancelar",
            background_color=(0.827, 0.180, 0.094, 1),
            size_hint=(None, None),
            width=100,
            height=50,
            color=(1, 1, 1, 1),  # Cor do texto
        )
        cancel_button.bind(on_press=self.dismiss)

        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        layout.add_widget(Label(text=f'{transaction_type} de: {transaction_amount:.2f}'))
        layout.add_widget(Label(text=f'Motivo: {transaction_reason}'))
        layout.add_widget(confirmation_button)
        layout.add_widget(cancel_button)

        self.title = f'Confirmação de {transaction_type}'
        self.content = layout

    def process_transaction(self, instance):
        if self.transaction_type == "Depositar":
            App.get_running_app().balance += self.transaction_amount
        elif self.transaction_type == "Retirar":
            App.get_running_app().balance -= self.transaction_amount

        conn = sqlite3.connect("CaixaApp.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transactions (transaction_type, amount, reason)
            VALUES (?, ?, ?)
        """, (self.transaction_type, self.transaction_amount, self.transaction_reason))
        conn.commit()
        conn.close()

        App.get_running_app().add_transaction_to_history(
            self.transaction_type,
            self.transaction_amount,
            self.transaction_reason
        )
        self.transaction_screen.update_extract_label()
        self.transaction_screen.get_app().update_balance_label()
        self.dismiss()
        self.return_to_main_menu()

    def return_to_main_menu(self):
        App.get_running_app().screen_manager.current = "main_screen"


class CaixaApp(MDApp):
    balance = 0.0
    balance_label = None
    extract_label = None
    transactions = []
    selected_date = None

    def build(self):
        self.theme_cls.primary_palette = "LightGreen"
        self.theme_cls.primary_hue = "500"
        self.theme_cls.theme_style = "Dark"

        create_transactions_table()

        self.screen_manager = ScreenManager()
        
        main_screen = Screen(name="main_screen")
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10, size_hint=(None, None), height=300, pos_hint={'center_x': 0.47, 'center_y': 0.5})

        deposit_button = BorderedButton(
            text="Depositar",
            background_color=(1, 2, 0.831, 1),
            size_hint=(None, None),
            width=200,
            height=50,
            color=(1, 1, 1, 1),
        )
        deposit_button.bind(on_press=self.show_deposit_screen)

        withdraw_button = BorderedButton(
            text="Retirar",
            background_color=(1, 2, 0.831, 1),
            size_hint=(None, None),
            width=200,
            height=50,
            color=(1, 1, 1, 1),
        )
        withdraw_button.bind(on_press=self.show_withdraw_screen)
        extract_button = BorderedButton(
            text="Extrato",
            background_color=(1, 2, 0.831, 1),
            size_hint=(None, None),
            width=200,
            height=50,
            color=(1, 1, 1, 1),
        )
        extract_button.bind(on_press=self.show_extract_screen)

        layout.add_widget(deposit_button)
        layout.add_widget(withdraw_button)
        layout.add_widget(extract_button)

        toggle_balance_button = BorderedButton(
            text="Mostrar/Esconder Saldo",
            background_color=(1, 2, 0.831, 1),
            size_hint=(None, None),
            width=200,
            height=50,
            color=(1, 1, 1, 1),
        )
        toggle_balance_button.bind(on_press=self.toggle_balance)

        layout.add_widget(toggle_balance_button)

        main_screen.add_widget(layout)

        layout.add_widget(GridLayout(cols=1, spacing=10, padding=10, pos_hint={'center_x': 0.5, 'center_y': 0.5}))
        self.balance_label = Label(text=f'Saldo Atual: [color=#0078d4]{self.balance:.2f}[/color]', size_hint=(1, None), height=30, markup=True)
        layout.add_widget(self.balance_label)

        self.screen_manager.add_widget(main_screen)

        extract_screen = Screen(name="extract_screen")
        self.screen_manager.add_widget(extract_screen)

        return_button = Button(
            text="Retornar ao Menu Principal",
            size_hint=(None, None),
            size=(200, 50),
            background_color=(0.827, 0.180, 0.094, 1),
            color=(1, 1, 1, 1),  # Cor do texto
        )
        return_button.bind(on_press=self.return_to_main_menu)

        extract_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        self.extract_label = MDDataTable(
            size_hint=(1, None),
            height=515,
            check=True,
            use_pagination=True,
            pagination_menu_pos="center",
            rows_num=10,
            column_data=[
                ("Data", dp(30)),
                ("Tipo", dp(30)),
                ("Valor", dp(30)),
                ("Motivo", dp(30)),
            ],
        )
        extract_layout.add_widget(self.extract_label)

        action_buttons_layout = BoxLayout(orientation='horizontal', spacing=10, padding=10)

        return_button = BorderedButton(
            text="Retornar ao Menu Principal",
            size_hint=(None, None),
            size=(200, 50),
            background_color=(0.827, 0.180, 0.094, 1),
            color=(1, 1, 1, 1),  # Cor do texto
        )
        return_button.bind(on_press=self.return_to_main_menu)

        action_buttons_layout.add_widget(return_button)

        # Botão "Filtrar por Data" ao lado do botão de retorno
        date_filter_button = BorderedButton(
            text="Filtrar por Data",
            size_hint=(None, None),
            size=(200, 50),
            background_color=(0.082, 0.447, 0.831, 1),
            color=(1, 1, 1, 1),  # Cor do texto
        )
        date_filter_button.bind(on_press=self.show_date_filter_dialog)

        action_buttons_layout.add_widget(date_filter_button)

        # Adicione um Widget de espaço flexível entre a tabela e os botões
        spacer = Widget()

        extract_layout.add_widget(spacer)
        extract_layout.add_widget(action_buttons_layout)

        extract_screen.add_widget(extract_layout)

        self.load_transactions_from_db()
        self.update_balance_label()

        return self.screen_manager

    def show_deposit_screen(self, instance):
        deposit_screen = TransactionScreen("Depositar", name="deposit_screen")
        deposit_screen.transaction_screen = self
        self.screen_manager.add_widget(deposit_screen)
        self.screen_manager.current = "deposit_screen"

    def show_withdraw_screen(self, instance):
        withdraw_screen = TransactionScreen("Retirar", name="withdraw_screen")
        withdraw_screen.transaction_screen = self
        self.screen_manager.add_widget(withdraw_screen)
        self.screen_manager.current = "withdraw_screen"

    def show_extract_screen(self, instance):
        self.load_transactions_from_db()
        self.update_balance_label()
        self.screen_manager.current = "extract_screen"

    def load_transactions_from_db(self):
        conn = sqlite3.connect("CaixaApp.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT transaction_type, amount, reason, timestamp FROM transactions
            ORDER BY timestamp DESC
        """)  # Ordenar as transações por ordem decrescente (da mais recente para a mais antiga)
        rows = cursor.fetchall()
        conn.close()

        self.transactions = []

        for row in rows:
            transaction_type, amount, reason, timestamp = row
            self.transactions.append((transaction_type, amount, reason, timestamp))

        self.update_extract_label()

    def return_to_main_menu(self, instance):
        self.screen_manager.current = "main_screen"

    def add_transaction_to_history(self, transaction_type, amount, reason):
        if transaction_type == "Depositar":
            transaction_type_str = "Depósito"
            amount_color = "#00FF00"
        elif transaction_type == "Retirar":
            transaction_type_str = "Retirada"
            amount_color = "#FF0000"

        # Obtenha a data e hora atual para o registro da transação
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        transaction_str = f'{timestamp} - {transaction_type_str: <10} - Valor: [color={amount_color}]{amount:.2f}[/color] - Motivo: {reason}'

        if self.extract_label:
            self.extract_label.row_data.append(
                [timestamp, transaction_type_str, f"[color={amount_color}]{amount:.2f}[/color]", reason]
            )

    def update_extract_label(self):
        if self.extract_label:
            self.extract_label.row_data = []
            for transaction_type, amount, reason, timestamp in self.transactions:
                date = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                date_str = date.strftime("%d/%m/%Y %H:%M:%S")
                self.add_transaction_to_history(transaction_type, amount, reason)

    def update_balance_label(self):
        self.balance = calculate_balance_from_transactions()
        if self.balance_label:
            self.balance_label.text = f'Saldo Atual: [color=#0078d4]{self.balance:.2f}[/color]'

    def toggle_balance(self, instance=None):
        if self.balance_label.text:
            self.balance_label.text = ''
        else:
            self.update_balance_label()

    def show_date_filter_dialog(self, instance):
        date_dialog = MDDatePicker()
        date_dialog.locale = "pt"  # Defina o idioma para português
        date_dialog.bind(on_save=self.on_date_save)
        date_dialog.open()

    def on_date_save(self, instance, value, date_range):
        self.selected_date = value
        self.load_transactions_from_db_by_date(self.selected_date)

    def load_transactions_from_db_by_date(self, selected_date):
        conn = sqlite3.connect("CaixaApp.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT transaction_type, amount, reason, timestamp
            FROM transactions
            WHERE DATE(timestamp) = ?
        """, (selected_date,))
        rows = cursor.fetchall()
        conn.close()

        self.transactions = []

        for row in rows:
            transaction_type, amount, reason, timestamp = row
            self.transactions.append((transaction_type, amount, reason, timestamp))

        self.update_extract_label()
        self.screen_manager.current = "extract_screen"
        

if __name__ == '__main__':
    app = CaixaApp()
    
    app.run()