import sqlite3
import os
import json
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Line, Rectangle
from kivy.clock import Clock
import requests

# SQLite bazasini sozlash
def init_db():
    conn = sqlite3.connect("trading_pro.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS strategies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            rules TEXT
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM strategies")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO strategies (name, rules) VALUES (?, ?)", 
                       ("Scalping Strategy", "RSI > 70 Sell, RSI < 30 Buy. Risk 1% per trade."))
        conn.commit()
    conn.close()

def get_strategy():
    conn = sqlite3.connect("trading_pro.db")
    cursor = conn.cursor()
    cursor.execute("SELECT rules FROM strategies LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else "No rules defined."

# Gemini API sozlamalari
GEMINI_API_KEY = "AQ.Ab8RN6LuV_gCqJYIuKVL1cVza5l_MiuRizexzDrMxvX8BZjLyA"

class ChartWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.signal_type = "NEUTRAL"
        with self.canvas.before:
            Color(0.1, 0.1, 0.12, 1)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        self.rect.size = instance.size
        self.rect.pos = instance.pos
        self.draw_chart()

    def draw_chart(self):
        self.canvas.clear()
        with self.canvas.before:
            Color(0.1, 0.1, 0.12, 1)
            Rectangle(size=self.size, pos=self.pos)
        
        with self.canvas:
            if self.signal_type == "BUY":
                Color(0.2, 0.8, 0.2, 1)
            elif self.signal_type == "SELL":
                Color(0.9, 0.2, 0.2, 1)
            else:
                Color(0.5, 0.5, 0.5, 1)

            w, h = self.size
            x, y = self.pos
            points = [x + w*0.1, y + h*0.3, x + w*0.3, y + h*0.4, 
                      x + w*0.5, y + h*0.2, x + w*0.7, y + h*0.7, x + w*0.9, y + h*0.6]
            Line(points=points, width=2)

class TradingApp(App):
    def build(self):
        init_db()
        
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        header = Label(
            text="[b]EUR/USD - H1[/b] | AI Copilot Terminal", 
            markup=True, 
            size_hint_y=0.08,
            color=(1, 1, 1, 1)
        )
        main_layout.add_widget(header)

        self.chart = ChartWidget(size_hint_y=0.35)
        main_layout.add_widget(self.chart)

        scroll = ScrollView(size_hint_y=0.37)
        self.ai_output = Label(
            text="AI analitikga savol bering...", 
            size_hint_y=None, 
            text_size=(None, None),
            halign='left', 
            valign='top',
            color=(0.9, 0.9, 0.9, 1)
        )
        self.ai_output.bind(texture_size=self.ai_output.setter('size'))
        scroll.add_widget(self.ai_output)
        main_layout.add_widget(scroll)

        input_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=5)
        self.user_input = TextInput(
            hint_text="Bozor/pattern holatini yozing (masalan: RSI 75)...", 
            multiline=False,
            background_color=(0.2, 0.2, 0.25, 1),
            foreground_color=(1, 1, 1, 1)
        )
        btn_analyze = Button(
            text="AI Analiz", 
            size_hint_x=0.3,
            background_color=(0, 0.5, 0.9, 1)
        )
        btn_analyze.bind(on_press=self.analyze_market)

        input_layout.add_widget(self.user_input)
        input_layout.add_widget(btn_analyze)
        main_layout.add_widget(input_layout)

        return main_layout

    def analyze_market(self, instance):
        query = self.user_input.text.strip()
        if not query:
            return

        self.ai_output.text = "Tahlil qilinmoqda..."
        Clock.schedule_once(lambda dt: self._process_ai(query), 0.1)

    def _process_ai(self, query):
        strategy = get_strategy()
        prompt_text = f"""
        Siz professional treyder yordamchisisiz.
        Foydalanuvchining bazasidagi strategiyasi: {strategy}
        Bozor holati: {query}

        Vaziyatni tahlil qiling va oxirida albatta XULOSA: BUY, SELL yoki HOLD deb yozing.
        Javobni o'zbek tilida qisqa va loqinda bering.
        """
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": prompt_text}]
            }]
        }

        try:
            res = requests.post(url, headers=headers, data=json.dumps(payload), timeout=15)
            if res.status_code == 200:
                data = res.json()
                text = data['candidates'][0]['content']['parts'][0]['text']
                self.ai_output.text = text

                if "BUY" in text.upper():
                    self.chart.signal_type = "BUY"
                elif "SELL" in text.upper():
                    self.chart.signal_type = "SELL"
                else:
                    self.chart.signal_type = "NEUTRAL"
                
                self.chart.draw_chart()
            else:
                self.ai_output.text = f"API Xatosi: {res.status_code}"
        except Exception as e:
            self.ai_output.text = f"Xatolik: {str(e)}"

if __name__ == "__main__":
    TradingApp().run()
