import sqlite3
from datetime import datetime
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button


class MenuPrincipal(Screen):
    total_estoque = NumericProperty(0)
    total_vendas = NumericProperty(0.0)
    total_fiados = NumericProperty(0)
    ultima_venda = StringProperty("Nenhuma")

    def on_pre_enter(self):
        self.atualizar_resumo()

    def atualizar_resumo(self):
        app = App.get_running_app()
        try:
            app.cursor.execute("SELECT COALESCE(SUM(quantidade), 0) FROM estoque")
            self.total_estoque = app.cursor.fetchone()[0]

            app.cursor.execute("SELECT COALESCE(SUM(valor), 0) FROM vendas")
            self.total_vendas = app.cursor.fetchone()[0]

            app.cursor.execute("SELECT COUNT(*) FROM fiado WHERE pago = 0")
            self.total_fiados = app.cursor.fetchone()[0]

            app.cursor.execute("SELECT produto, data FROM vendas ORDER BY id DESC LIMIT 1")
            ultima = app.cursor.fetchone()
            self.ultima_venda = f"{ultima[0]} ({ultima[1]})" if ultima else "Nenhuma"

        except Exception as e:
            self.mostrar_erro(f"Erro ao atualizar: {str(e)}")

    def mostrar_erro(self, mensagem):
        Popup(title='Erro', content=Label(text=mensagem), size_hint=(0.8, 0.4)).open()


class RegistrarVendaScreen(Screen):
    def salvar_venda(self):
        produto = self.ids.produto.text
        quantidade = self.ids.quantidade.text
        valor = self.ids.valor.text

        if produto and quantidade and valor:
            try:
                app = App.get_running_app()
                data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")

                app.cursor.execute(
                    "INSERT INTO vendas (produto, quantidade, valor, data) VALUES (?, ?, ?, ?)",
                    (produto, int(quantidade), float(valor), data_atual))

                app.conn.commit()
                self.manager.current = 'menu'

            except Exception as e:
                self.mostrar_erro(f"Erro ao registrar: {str(e)}")

    def mostrar_erro(self, mensagem):
        Popup(title='Erro', content=Label(text=mensagem), size_hint=(0.8, 0.4)).open()


class ControleEstoqueScreen(Screen):
    def atualizar_estoque(self):
        produto = self.ids.produto.text
        quantidade = self.ids.quantidade.text
        preco = self.ids.preco.text

        if produto and quantidade and preco:
            try:
                app = App.get_running_app()
                app.cursor.execute(
                    "INSERT OR REPLACE INTO estoque (produto, quantidade, preco_unitario) VALUES (?, ?, ?)",
                    (produto, int(quantidade), float(preco)))
                app.conn.commit()
                self.manager.current = 'menu'

            except Exception as e:
                self.mostrar_erro(f"Erro ao atualizar: {str(e)}")

    def mostrar_erro(self, mensagem):
        Popup(title='Erro', content=Label(text=mensagem), size_hint=(0.8, 0.4)).open()


class ControleDevedoresScreen(Screen):
    def on_enter(self):
        self.carregar_fiados()

    def carregar_fiados(self):
        try:
            app = App.get_running_app()
            self.ids.lista_fiados.clear_widgets()

            app.cursor.execute("""
                SELECT 
                    cliente, 
                    telefone, 
                    SUM(valor) as total_devido,
                    GROUP_CONCAT(id) as ids
                FROM fiado 
                WHERE pago = 0
                GROUP BY cliente, telefone
                ORDER BY cliente
            """)

            devedores = app.cursor.fetchall()

            if not devedores:
                self.ids.lista_fiados.add_widget(Label(text="Nenhum débito pendente", size_hint_y=None, height=40))
                return

            for cliente, telefone, total, ids in devedores:
                box = BoxLayout(size_hint_y=None, height=60, padding=5)

                info_layout = BoxLayout(orientation='vertical', size_hint_x=0.7)
                info_layout.add_widget(Label(text=f"[b]{cliente}[/b]", markup=True, halign='left', size_hint_y=0.5))
                info_layout.add_widget(Label(text=f"Tel: {telefone}", halign='left', size_hint_y=0.3))

                acao_layout = BoxLayout(size_hint_x=0.3)
                acao_layout.add_widget(Label(text=f"[color=ff3333]R$ {float(total):.2f}[/color]", markup=True))

                btn_pagar = Button(text='Pagar', size_hint_x=0.4,
                                   background_color=(0, 0.7, 0, 1),
                                   on_press=lambda btn, ids=ids: self.marcar_como_pago(ids))
                acao_layout.add_widget(btn_pagar)

                box.add_widget(info_layout)
                box.add_widget(acao_layout)
                self.ids.lista_fiados.add_widget(box)

        except Exception as e:
            self.mostrar_erro(f"Erro ao carregar: {str(e)}")

    def marcar_como_pago(self, ids_fiado):
        try:
            app = App.get_running_app()
            app.cursor.execute(f"UPDATE fiado SET pago = 1 WHERE id IN ({ids_fiado})")
            app.conn.commit()
            self.carregar_fiados()

            menu = self.manager.get_screen('menu')
            if hasattr(menu, 'atualizar_resumo'):
                menu.atualizar_resumo()

            Popup(title='Sucesso',
                  content=Label(text='Débitos marcados como pagos!'),
                  size_hint=(0.6, 0.3)).open()

        except Exception as e:
            self.mostrar_erro(f"Erro ao pagar: {str(e)}")

    def mostrar_erro(self, mensagem):
        Popup(title='Erro',
              content=Label(text=mensagem),
              size_hint=(0.8, 0.4)).open()


class RegistrarFiadoScreen(Screen):
    def salvar_fiado(self):
        cliente = self.ids.cliente.text
        telefone = self.ids.telefone.text
        produto = self.ids.produto.text
        quantidade = self.ids.quantidade.text
        valor = self.ids.valor.text

        if cliente and produto and quantidade and valor:
            try:
                app = App.get_running_app()
                data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")

                app.cursor.execute(
                    "INSERT INTO fiado (cliente, telefone, produto, quantidade, valor, data) VALUES (?, ?, ?, ?, ?, ?)",
                    (cliente, telefone, produto, int(quantidade), float(valor), data_atual)
                )
                app.conn.commit()
                self.manager.current = 'menu'

                Popup(title='Sucesso',
                      content=Label(text='Fiado registrado com sucesso!'),
                      size_hint=(0.6, 0.3)).open()
            except Exception as e:
                self.mostrar_erro(f"Erro ao registrar fiado: {str(e)}")
        else:
            self.mostrar_erro("Preencha todos os campos obrigatórios.")

    def mostrar_erro(self, mensagem):
        Popup(title='Erro',
              content=Label(text=mensagem),
              size_hint=(0.8, 0.4)).open()


class FidelidadeFood(App):
    def build(self):
        self.inicializar_banco_dados()
        Builder.load_file('fidelidade.kv')

        sm = ScreenManager()
        sm.add_widget(MenuPrincipal(name='menu'))
        sm.add_widget(RegistrarVendaScreen(name='registrar_venda'))
        sm.add_widget(ControleEstoqueScreen(name='controle_estoque'))
        sm.add_widget(ControleDevedoresScreen(name='controle_devedores'))
        sm.add_widget(RegistrarFiadoScreen(name='registrar_fiado'))
        return sm

    def inicializar_banco_dados(self):
        self.conn = sqlite3.connect('fidelidade.db')
        self.cursor = self.conn.cursor()

        self.cursor.executescript('''
            CREATE TABLE IF NOT EXISTS vendas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produto TEXT,
                quantidade INTEGER,
                valor REAL,
                data TEXT
            );

            CREATE TABLE IF NOT EXISTS estoque (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produto TEXT UNIQUE,
                quantidade INTEGER,
                preco_unitario REAL
            );

            CREATE TABLE IF NOT EXISTS fiado (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente TEXT,
                telefone TEXT,
                produto TEXT,
                quantidade INTEGER,
                valor REAL,
                data TEXT,
                pago INTEGER DEFAULT 0
            );
        ''')
        self.conn.commit()

    def on_stop(self):
        self.conn.close()


if __name__ == '__main__':
    FidelidadeFood().run()
