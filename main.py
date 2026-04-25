import json
from collections import defaultdict
from functools import partial

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle

ARQUIVO = "lancamentos.json"


def carregar():
    try:
        with open(ARQUIVO, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def salvar(lancamentos):
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(lancamentos, f, indent=2, ensure_ascii=False)


class Tela(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=15, padding=15, **kwargs)

        self.lancamentos = carregar()
        self.selecionado = None

        # FUNDO
        with self.canvas.before:
            Color(0.95, 0.95, 0.95, 1)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)

        # TÍTULO
        titulo = Label(text="📋 Controle de Diárias", size_hint_y=None, height=50, font_size=22, bold=True)
        self.add_widget(titulo)

        # INPUTS
        box_inputs = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None, height=260)

        self.data = TextInput(hint_text="Data (2026-04-23)", multiline=False)
        self.pessoa = TextInput(hint_text="Nome", multiline=False)
        self.dias = TextInput(hint_text="Dias (1 ou 0.5)", multiline=False)
        self.diaria = TextInput(hint_text="Valor diária", text="70", multiline=False)

        self.dias.bind(text=self.calcular_valor)
        self.diaria.bind(text=self.calcular_valor)

        box_inputs.add_widget(self.data)
        box_inputs.add_widget(self.pessoa)
        box_inputs.add_widget(self.dias)
        box_inputs.add_widget(self.diaria)

        self.add_widget(box_inputs)

        # VALOR
        self.valor_label = Label(text="R$ 0.00", size_hint_y=None, height=40, font_size=20, color=(0, 0.6, 0, 1))
        self.add_widget(self.valor_label)

        # BOTÕES
        box_botoes = GridLayout(cols=2, spacing=10, size_hint_y=None, height=140)

        btn_add = Button(text="Adicionar", background_color=(0, 0.6, 0, 1))
        btn_del = Button(text="Apagar", background_color=(0.8, 0, 0, 1))
        btn_resumo = Button(text="Resumo", background_color=(0.2, 0.4, 1, 1))
        btn_rank = Button(text="Ranking", background_color=(1, 0.5, 0, 1))

        btn_add.bind(on_press=self.adicionar)
        btn_del.bind(on_press=self.apagar)
        btn_resumo.bind(on_press=self.resumo_por_pessoa)
        btn_rank.bind(on_press=self.ranking)

        box_botoes.add_widget(btn_add)
        box_botoes.add_widget(btn_del)
        box_botoes.add_widget(btn_resumo)
        box_botoes.add_widget(btn_rank)

        self.add_widget(box_botoes)

        # TOTAL
        self.total_label = Label(text="TOTAL: R$ 0.00", size_hint_y=None, height=40, font_size=18, bold=True)
        self.add_widget(self.total_label)

        # LISTA
        self.scroll = ScrollView()
        self.lista = GridLayout(cols=1, spacing=8, size_hint_y=None)
        self.lista.bind(minimum_height=self.lista.setter('height'))

        self.scroll.add_widget(self.lista)
        self.add_widget(self.scroll)

        self.atualizar_lista()
        self.atualizar_total()

    def _update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def atualizar_lista(self):
        self.lista.clear_widgets()
        for i, l in enumerate(self.lancamentos):
            valor = l["dias"] * l.get("diaria", 70)
            texto = f"{l['data']} | {l['pessoa']} | {l['dias']}d | R$ {valor:.2f}"

            btn = Button(
                text=texto,
                size_hint_y=None,
                height=55,
                background_color=(1, 1, 1, 1),
                color=(0, 0, 0, 1)
            )

            btn.bind(on_press=partial(self.selecionar, i))
            self.lista.add_widget(btn)

    def selecionar(self, index, *args):
        self.selecionado = index
        l = self.lancamentos[index]
        self.data.text = l["data"]
        self.pessoa.text = l["pessoa"]
        self.dias.text = str(l["dias"])
        self.diaria.text = str(l.get("diaria", 70))

    def adicionar(self, instance):
        try:
            self.lancamentos.append({
                "data": self.data.text,
                "pessoa": self.pessoa.text.lower(),
                "dias": float(self.dias.text),
                "diaria": float(self.diaria.text)
            })

            salvar(self.lancamentos)
            self.atualizar_lista()
            self.atualizar_total()

            self.data.text = ""
            self.pessoa.text = ""
            self.dias.text = ""

        except Exception as e:
            self.popup(f"Erro: {str(e)}")

    def apagar(self, instance):
        if self.selecionado is not None:
            self.lancamentos.pop(self.selecionado)
            salvar(self.lancamentos)
            self.selecionado = None
            self.atualizar_lista()
            self.atualizar_total()

    def atualizar_total(self):
        total = sum(l["dias"] * l.get("diaria", 70) for l in self.lancamentos)
        self.total_label.text = f"TOTAL: R$ {total:.2f}"

    def calcular_valor(self, instance, value):
        try:
            dias = float(self.dias.text)
            diaria = float(self.diaria.text)
            valor = dias * diaria
            self.valor_label.text = f"R$ {valor:.2f}"
        except:
            self.valor_label.text = "R$ 0.00"

    def resumo_por_pessoa(self, instance):
        totais = defaultdict(float)

        for l in self.lancamentos:
            totais[l["pessoa"]] += l["dias"]

        texto = "📊 RESUMO\n\n"
        total_geral = 0

        for pessoa, dias in sorted(totais.items()):
            valor = sum(l["dias"] * l.get("diaria", 70) for l in self.lancamentos if l["pessoa"] == pessoa)
            total_geral += valor
            texto += f"{pessoa}\n➡ {dias} dias\n💰 R$ {valor:.2f}\n\n"

        texto += f"TOTAL: R$ {total_geral:.2f}"
        self.popup(texto)

    def ranking(self, instance):
        totais = {}

        for l in self.lancamentos:
            totais[l["pessoa"]] = totais.get(l["pessoa"], 0) + l["dias"]

        ranking = []
        for pessoa in totais:
            valor = sum(l["dias"] * l.get("diaria", 70) for l in self.lancamentos if l["pessoa"] == pessoa)
            dias = totais[pessoa]
            ranking.append((pessoa, valor, dias))

        ranking.sort(key=lambda x: x[1], reverse=True)

        texto = "🏆 RANKING\n\n"
        medalhas = ["🥇", "🥈", "🥉"]

        for i, (pessoa, valor, dias) in enumerate(ranking):
            medalha = medalhas[i] if i < 3 else f"{i+1}º"
            texto += f"{medalha} {pessoa}\n💰 R$ {valor:.2f} ({dias} dias)\n\n"

        self.popup(texto)

    def popup(self, texto):
        box = BoxLayout(orientation='vertical', padding=10)
        lbl = Label(text=texto)
        btn = Button(text="Fechar", size_hint_y=None, height=60)

        box.add_widget(lbl)
        box.add_widget(btn)

        popup = Popup(title="Resultado", content=box, size_hint=(0.9, 0.9))
        btn.bind(on_press=popup.dismiss)
        popup.open()


class MeuApp(App):
    def build(self):
        return Tela()


MeuApp().run()