import os
import sqlite3
import urllib.request
import json
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Line

GEMINI_API_KEY = "AQ.Ab8RN6LuV_gCqJYIuKVL1cVza5l_M  iuRizexzDrMxvX8BZjLyA" # O'zingizning API kalitingiz

def init_db():
    conn = sqlite3.connect("trading_pro.db")
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS knowledge (title TEXT, content TEXT)')
    conn.commit()
    conn.close()

def save_knowledge(title, content):
    conn = sqlite3.connect("trading_pro.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO knowledge VALUES (?, ?)", (title, content))
    conn.commit()
    conn.close()

def load_knowledge():
    conn = sqlite3.connect("trading_pro.db")
    cursor = conn.cursor()
    cursor.execute("SELECT title, content FROM knowledge")
    rows = cursor.fetchall()
    conn.close()
    return "\n\n".join([f"[{r[0]}]: {r[1]}" for r in rows])

class AutoAIMonitor(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            self.bg_color = Color(0.08, 0.11, 0.15, 1)
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        self.bg_rect.size = instance.size
        self.bg_rect.pos = instance.pos

    def draw_ai_analysis(self, analysis_text):
        self.canvas.after.clear()
        with self.canvas.after:
            w, h = self.width, self.height
            if "BUY" in analysis_text.upper() or "BULLISH" in analysis_text.upper():
                Color(0, 0.8, 0.3, 0.3)
                Rectangle(pos=(w * 0.2, h * 0.35), size=(w * 0.6, h * 0.12))
                Color(0, 1, 0.5, 1)
                Line(points=[w * 0.5, h * 0.4, w * 0.5, h * 0.6], width=3)
            else:
                Color(0.9, 0.2, 0.2, 0.3)
                Rectangle(pos=(w * 0.2, h * 0.55), size=(w * 0.6, h * 0.12))
                Color(1, 0.3, 0.3, 1)
                Line(points=[w * 0.5, h * 0.6, w * 0.5, h * 0.4], width=3)

class ProTradingTerminalApp(App):
    def build(self):
        init_db()
        self.current_pair = "EUR/USD"
        self.current_tf = "H1"

        root = FloatLayout()
        self.monitor = AutoAIMonitor(size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
        root.add_widget(self.monitor)

        top_bar = BoxLayout(orientation='horizontal', size_hint=(1, None), height=45, pos_hint={'top': 1}, padding=5, spacing=5)
        self.pair_label = Label(text=f"{self.current_pair} | {self.current_tf}", bold=True, color=(0, 0.8, 1, 1))
        top_bar.add_widget(self.pair_label)
        root.add_widget(top_bar)

        self.scroll_info = ScrollView(size_hint=(0.95, 0.22), pos_hint={'x': 0.025, 'y': 0.18})
        self.info_label = Label(
            text="🤖 AI Copilot tayyor.",
            size_hint_y=None, text_size=(Window.width - 40, None),
            halign='left', valign='top', color=(1, 1, 1, 0.9), font_size='12sp'
        )
        self.info_label.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1]))
        self.scroll_info.add_widget(self.info_label)
        root.add_widget(self.scroll_info)

        input_bar = BoxLayout(orientation='horizontal', size_hint=(1, None), height=65, pos_hint={'y': 0}, padding=5, spacing=5)
        self.chat_input = TextInput(
            hint_text="Grafik holatini yozing...", multiline=True, font_size='12sp',
            background_color=(0.12, 0.16, 0.22, 0.95), foreground_color=(1, 1, 1, 1)
        )
        send_btn = Button(text="AI Analiz", size_hint_x=0.28, background_color=(0.1, 0.5, 0.85, 0.95), bold=True)
        send_btn.bind(on_press=self.ask_ai_and_draw)
        input_bar.add_widget(self.chat_input)
        input_bar.add_widget(send_btn)
        root.add_widget(input_bar)
        return root

    def ask_ai_and_draw(self, instance):
        query = self.chat_input.text.strip()
        knowledge = load_knowledge()
        self.info_label.text = f"Tahlil qilinmoqda..."
        self.chat_input.text = ""
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            prompt = f"Siz AI Copilot-siz. BUY/SELL tahlil bering.\nBILIMLAR:\n{knowledge}\n\nSAVOL: {query}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                ai_text = res_data['candidates'][0]['content']['parts'][0]['text']
                self.info_label.text = f"🤖 AI Copilot:\n{ai_text}"
                self.monitor.draw_ai_analysis(ai_text)
        except Exception as e:
            self.info_label.text = f"❌ Xatolik: {str(e)}"

if __name__ == '__main__':
    ProTradingTerminalApp().run()
