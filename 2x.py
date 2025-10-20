import random as r
import time
import threading
import requests
import pandas as pd
import customtkinter as ctk
from datetime import datetime

# ─── GLOBAL STATE ──────────────────────────────────────────────────────────────
player_data = {k: [] for k in ['timestamp', 'game_type', 'bet_amount', 'result', 'profit_loss', 'balance_after']}
wallet, backpack = 500, []
player_name, player_level, player_xp = "", 1, 0
jackpot_pool, daily_bonus_claimed, last_login_date = 10000, False, None
xp_thresholds = {1: 100, 2: 250, 3: 500, 4: 1000, 5: 2000, 6: 4000, 7: 8000, 8: 16000, 9: 32000, 10: 64000}

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def record(game, bet, res, pl):
    global wallet
    player_data['timestamp'].append(datetime.now())
    player_data['game_type'].append(game)
    player_data['bet_amount'].append(bet)
    player_data['result'].append(res)
    player_data['profit_loss'].append(pl)
    player_data['balance_after'].append(wallet)

def add_wallet(a): 
    global wallet
    wallet += a

def give_xp(a):
    global player_xp, player_level
    player_xp += a
    if player_level < 10 and player_xp >= xp_thresholds[player_level]:
        player_level += 1
        bonus = player_level * 100
        add_wallet(bonus)
        player_xp = 0

def get_mult():
    try:
        return float(requests.get("https://clash.gg/double", timeout=2).json().get("multiplier", 2))
    except:
        return 2

# ─── GUI SETUP ───────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🎰 Emoji Casino")
        self.geometry("1000x600")
        
        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True)
        
        self.frames = {}
        for F in (Login, Dashboard, ClassicGamble, SlotMachine, CaseBattle, CrazyCase, DoubleGame, Backpack, Stats):
            page = F(container, self)
            self.frames[F] = page
            page.place(relwidth=1, relheight=1)
        
        self.show(Login)
    
    def show(self, cls):
        f = self.frames[cls]
        f.refresh() if hasattr(f, "refresh") else None
        f.tkraise()

# ─── GAME FRAMES ──────────────────────────────────────────────────────────────
class Login(ctk.CTkFrame):
    def __init__(self, p, c):
        super().__init__(p)
        self.c = c
        ctk.CTkLabel(self, text="🎩 Enter Your Name", font=("Arial", 24)).pack(pady=50)
        self.e = ctk.CTkEntry(self)
        self.e.pack(pady=10)
        ctk.CTkButton(self, text="Start Gambling!", command=self.start).pack(pady=20)
    
    def start(self):
        global player_name
        player_name = self.e.get() or "Player"
        self.c.show(Dashboard)

class Dashboard(ctk.CTkFrame):
    def __init__(self, p, c):
        super().__init__(p)
        self.c = c
        
        # Header
        top = ctk.CTkFrame(self)
        top.pack(fill="x", pady=10)
        
        self.w = ctk.CTkLabel(top, text="", font=("Arial", 16))
        self.w.pack(side="left", padx=20)
        
        self.l = ctk.CTkLabel(top, text="", font=("Arial", 16))
        self.l.pack(side="left", padx=20)
        
        self.xp = ctk.CTkProgressBar(top, width=200)
        self.xp.pack(side="left", padx=20)
        
        self.j = ctk.CTkLabel(top, text="", font=("Arial", 16))
        self.j.pack(side="left", padx=20)
        
        # Game Selection
        nav = ctk.CTkFrame(self)
        nav.pack(pady=50)
        
        games = [
            ("🎡 Classic Wheel", ClassicGamble),
            ("🎰 Slot Machine", SlotMachine),
            ("💼 Case Battle", CaseBattle),
            ("🎁 Crazy Case", CrazyCase),
            ("🪙 Double Game", DoubleGame),
            ("🎒 Backpack", Backpack),
            ("📊 Stats", Stats)
        ]
        
        for i, (t, f) in enumerate(games):
            btn = ctk.CTkButton(nav, text=t, command=lambda f=f: self.c.show(f))
            btn.grid(row=i//4, column=i%4, padx=10, pady=10)
        
        ctk.CTkButton(self, text="Exit", command=self.c.quit).pack(side="bottom", pady=20)
    
    def refresh(self):
        self.w.configure(text=f"💰 Wallet: ${wallet}")
        self.l.configure(text=f"⭐ Level: {player_level}")
        self.xp.set(player_xp / xp_thresholds[player_level])
        self.j.configure(text=f"🏆 Jackpot: ${jackpot_pool}")

class ClassicGamble(ctk.CTkFrame):
    def __init__(self, p, c):
        super().__init__(p)
        self.c = c
        
        ctk.CTkLabel(self, text="🎡 Classic Wheel", font=("Arial", 20)).pack(pady=10)
        
        self.canvas = ctk.CTkCanvas(self, width=300, height=300, bg="#222222")
        self.canvas.pack()
        
        self.btn = ctk.CTkButton(self, text="SPIN ($10)", command=self.spin)
        self.btn.pack(pady=10)
        
        self.lbl = ctk.CTkLabel(self, text="", font=("Arial", 16))
        self.lbl.pack(pady=10)
        
        ctk.CTkButton(self, text="Back", command=lambda: self.c.show(Dashboard)).pack(side="bottom", pady=20)
        
        self.wheel_emojis = ["🍒", "🍋", "🍊", "🍉", "🍇", "🍓", "7️⃣", "💎", "💰", "🎯"]
    
    def spin(self):
        if wallet < 10:
            self.lbl.configure(text="❌ Not enough money!")
            return
        
        add_wallet(-10)
        self.btn.configure(state="disabled")
        threading.Thread(target=self._spin, daemon=True).start()
    
    def _spin(self):
        start = time.time()
        durations = [2.0, 2.5, 3.0]
        emoji_pos = [0, 0, 0]
        
        while True:
            t = time.time() - start
            for i in range(3):
                if t < durations[i]:
                    speed = 0.2 - (t / durations[i]) * 0.15
                    emoji_pos[i] = (emoji_pos[i] + 1) % len(self.wheel_emojis)
                    self.canvas.delete(f"wheel_{i}")
                    self.canvas.create_text(
                        50 + i * 100, 150,
                        text=self.wheel_emojis[emoji_pos[i]],
                        font=("Arial", 40),
                        fill="gold",
                        tags=f"wheel_{i}"
                    )
            if t >= max(durations):
                break
            time.sleep(0.1)
        
        results = [r.randint(0, len(self.wheel_emojis)-1) for _ in range(3)]
        for i, res in enumerate(results):
            self.canvas.delete(f"wheel_{i}")
            self.canvas.create_text(
                50 + i * 100, 150,
                text=self.wheel_emojis[res],
                font=("Arial", 40),
                fill="gold",
                tags=f"wheel_{i}"
            )
        
        if len(set(results)) == 1:
            win_amount = 50 * (results[0] + 1)
            add_wallet(win_amount)
            self.lbl.configure(text=f"🎉 YOU WIN ${win_amount}!")
            record("Wheel", 10, "Win", win_amount)
        else:
            self.lbl.configure(text="😢 Try again!")
            record("Wheel", 10, "Lose", -10)
        
        self.btn.configure(state="normal")
    
    def refresh(self):
        self.lbl.configure(text="")
        self.canvas.delete("all")

class SlotMachine(ctk.CTkFrame):
    def __init__(self, p, c):
        super().__init__(p)
        self.c = c
        
        ctk.CTkLabel(self, text="🎰 Slot Machine", font=("Arial", 20)).pack(pady=10)
        
        self.reel_frames = [ctk.CTkFrame(self, width=100, height=200) for _ in range(3)]
        for i, frame in enumerate(self.reel_frames):
            frame.place(x=150 + i * 120, y=100)
        
        self.reel_labels = [
            ctk.CTkLabel(self.reel_frames[i], text="🍒", font=("Arial", 50))
            for i in range(3)
        ]
        for label in self.reel_labels:
            label.pack(pady=20)
        
        self.btn = ctk.CTkButton(self, text="SPIN ($5)", command=self.spin)
        self.btn.pack(pady=200)
        
        self.lbl = ctk.CTkLabel(self, text="", font=("Arial", 16))
        self.lbl.pack(pady=10)
        
        ctk.CTkButton(self, text="Back", command=lambda: self.c.show(Dashboard)).pack(side="bottom", pady=20)
        
        self.slot_emojis = ["🍒", "🍋", "🍊", "🍉", "🍇", "🍓", "7️⃣", "💎", "💰"]
    
    def spin(self):
        if wallet < 5:
            self.lbl.configure(text="❌ Not enough money!")
            return
        
        add_wallet(-5)
        self.btn.configure(state="disabled")
        threading.Thread(target=self._spin, daemon=True).start()
    
    def _spin(self):
        for _ in range(15):
            for label in self.reel_labels:
                label.configure(text=r.choice(self.slot_emojis))
            time.sleep(0.1)
        
        results = [r.choice(self.slot_emojis) for _ in range(3)]
        for i, res in enumerate(results):
            self.reel_labels[i].configure(text=res)
        
        if len(set(results)) == 1:
            win_amount = 100 if results[0] == "💰" else 50
            add_wallet(win_amount)
            self.lbl.configure(text=f"🎉 JACKPOT! ${win_amount}!")
            record("Slots", 5, "Win", win_amount)
        else:
            self.lbl.configure(text="😢 No win this time!")
            record("Slots", 5, "Lose", -5)
        
        self.btn.configure(state="normal")
    
    def refresh(self):
        self.lbl.configure(text="")

class CaseBattle(ctk.CTkFrame):
    def __init__(self, p, c):
        super().__init__(p)
        self.c = c
        
        ctk.CTkLabel(self, text="💼 Case Battle", font=("Arial", 20)).pack(pady=10)
        
        self.case_label = ctk.CTkLabel(self, text="📦", font=("Arial", 100))
        self.case_label.pack(pady=20)
        
        self.btn = ctk.CTkButton(self, text="OPEN ($20)", command=self.open)
        self.btn.pack()
        
        self.lbl = ctk.CTkLabel(self, text="", font=("Arial", 16))
        self.lbl.pack(pady=10)
        
        ctk.CTkButton(self, text="Back", command=lambda: self.c.show(Dashboard)).pack(side="bottom", pady=20)
        
        self.prizes = ["💰", "💎", "🚗", "🏆", "😢", "💣"]
    
    def open(self):
        if wallet < 20:
            self.lbl.configure(text="❌ Not enough money!")
            return
        
        add_wallet(-20)
        self.btn.configure(state="disabled")
        threading.Thread(target=self._open, daemon=True).start()
    
    def _open(self):
        # Animation
        for emoji in ["📦", "🔓", "🔍", "🎁"]:
            self.case_label.configure(text=emoji)
            time.sleep(0.3)
        
        result = r.choice(self.prizes)
        self.case_label.configure(text=result)
        
        if result in ["💰", "💎", "🚗", "🏆"]:
            win_amount = 100 if result == "🏆" else 50
            add_wallet(win_amount)
            backpack.append((result, win_amount))
            self.lbl.configure(text=f"🎉 You found {result} (${win_amount})!")
            record("Case", 20, "Win", win_amount)
        else:
            self.lbl.configure(text="💥 You got nothing!" if result == "😢" else "💣 BOOM! You lost!")
            record("Case", 20, "Lose", -20)
        
        self.btn.configure(state="normal")
    
    def refresh(self):
        self.lbl.configure(text="")
        self.case_label.configure(text="📦")

class CrazyCase(ctk.CTkFrame):
    def __init__(self, p, c):
        super().__init__(p)
        self.c = c
        
        ctk.CTkLabel(self, text="🎁 Crazy Case", font=("Arial", 20)).pack(pady=10)
        
        self.case_label = ctk.CTkLabel(self, text="🎁", font=("Arial", 100))
        self.case_label.pack(pady=20)
        
        self.btn = ctk.CTkButton(self, text="OPEN ($50)", command=self.open)
        self.btn.pack()
        
        self.lbl = ctk.CTkLabel(self, text="", font=("Arial", 16))
        self.lbl.pack(pady=10)
        
        ctk.CTkButton(self, text="Back", command=lambda: self.c.show(Dashboard)).pack(side="bottom", pady=20)
        
        self.prizes = ["💰", "💎", "🚗", "🏆", "😢", "💣", "🎰", "🏝️"]
    
    def open(self):
        if wallet < 50:
            self.lbl.configure(text="❌ Not enough money!")
            return
        
        add_wallet(-50)
        self.btn.configure(state="disabled")
        threading.Thread(target=self._open, daemon=True).start()
    
    def _open(self):
        # Crazy animation
        for _ in range(10):
            self.case_label.configure(text=r.choice(self.prizes))
            time.sleep(0.2)
        
        result = r.choice(self.prizes)
        self.case_label.configure(text=result)
        
        if result in ["💰", "💎", "🚗", "🏆", "🎰", "🏝️"]:
            win_amount = 200 if result == "🏆" else 100
            add_wallet(win_amount)
            backpack.append((result, win_amount))
            self.lbl.configure(text=f"🎉 You found {result} (${win_amount})!")
            record("CrazyCase", 50, "Win", win_amount)
        else:
            self.lbl.configure(text="💥 You got nothing!" if result == "😢" else "💣 BOOM! You lost!")
            record("CrazyCase", 50, "Lose", -50)
        
        self.btn.configure(state="normal")
    
    def refresh(self):
        self.lbl.configure(text="")
        self.case_label.configure(text="🎁")

class DoubleGame(ctk.CTkFrame):
    def __init__(self, p, c):
        super().__init__(p)
        self.c = c
        
        ctk.CTkLabel(self, text="🪙 Double Game", font=("Arial", 20)).pack(pady=10)
        
        self.coin_label = ctk.CTkLabel(self, text="🪙", font=("Arial", 100))
        self.coin_label.pack(pady=20)
        
        self.btn = ctk.CTkButton(self, text="FLIP ($10)", command=self.flip)
        self.btn.pack()
        
        self.lbl = ctk.CTkLabel(self, text="", font=("Arial", 16))
        self.lbl.pack(pady=10)
        
        ctk.CTkButton(self, text="Back", command=lambda: self.c.show(Dashboard)).pack(side="bottom", pady=20)
    
    def flip(self):
        if wallet < 10:
            self.lbl.configure(text="❌ Not enough money!")
            return
        
        add_wallet(-10)
        self.btn.configure(state="disabled")
        threading.Thread(target=self._flip, daemon=True).start()
    
    def _flip(self):
        # Coin flip animation
        for _ in range(8):
            self.coin_label.configure(text="🪙" if _ % 2 == 0 else "🤑")
            time.sleep(0.1)
        
        multiplier = get_mult()
        if r.random() < (1/multiplier):
            win_amount = int(10 * multiplier)
            add_wallet(win_amount)
            self.lbl.configure(text=f"🎉 Win x{multiplier:.1f}! +${win_amount}")
            self.coin_label.configure(text="🤑")
            record("Double", 10, "Win", win_amount)
        else:
            self.lbl.configure(text="😢 You lost!")
            self.coin_label.configure(text="💀")
            record("Double", 10, "Lose", -10)
        
        self.btn.configure(state="normal")
    
    def refresh(self):
        self.lbl.configure(text="")
        self.coin_label.configure(text="🪙")

class Backpack(ctk.CTkFrame):
    def __init__(self, p, c):
        super().__init__(p)
        self.c = c
        
        ctk.CTkLabel(self, text="🎒 Backpack", font=("Arial", 20)).pack(pady=10)
        
        self.scroll_frame = ctk.CTkScrollableFrame(self, width=800, height=300)
        self.scroll_frame.pack(pady=20)
        
        ctk.CTkButton(self, text="Back", command=lambda: self.c.show(Dashboard)).pack(side="bottom", pady=20)
    
    def refresh(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        if not backpack:
            ctk.CTkLabel(self.scroll_frame, text="Your backpack is empty!").pack()
            return
        
        for item, value in backpack:
            frame = ctk.CTkFrame(self.scroll_frame)
            frame.pack(fill="x", pady=5)
            
            ctk.CTkLabel(frame, text=f"{item} (${value})", font=("Arial", 16)).pack(side="left", padx=10)
            
            ctk.CTkButton(
                frame, 
                text="Sell", 
                command=lambda i=item, v=value: self.sell(i, v)
            ).pack(side="right", padx=10)
    
    def sell(self, item, value):
        backpack.remove((item, value))
        add_wallet(value)
        record("Sell", 0, "Sell", value)
        self.refresh()

class Stats(ctk.CTkFrame):
    def __init__(self, p, c):
        super().__init__(p)
        self.c = c
        
        ctk.CTkLabel(self, text="📊 Stats", font=("Arial", 20)).pack(pady=10)
        
        self.textbox = ctk.CTkTextbox(self, width=900, height=400)
        self.textbox.pack(pady=20)
        
        ctk.CTkButton(self, text="Back", command=lambda: self.c.show(Dashboard)).pack(side="bottom", pady=20)
    
    def refresh(self):
        self.textbox.delete("0.0", "end")
        
        if not player_data['timestamp']:
            self.textbox.insert("0.0", "No game history yet!")
            return
        
        df = pd.DataFrame(player_data)
        total_games = len(df)
        wins = (df['profit_loss'] > 0).sum()
        win_rate = (wins / total_games) * 100 if total_games > 0 else 0
        
        stats_text = f"""
        Player: {player_name}
        Level: {player_level}
        Balance: ${wallet}
        
        📈 Game Stats:
        - Total Games: {total_games}
        - Wins: {wins}
        - Win Rate: {win_rate:.1f}%
        
        🎮 Game Breakdown:
        """
        
        self.textbox.insert("0.0", stats_text)
        
        if not df.empty:
            game_stats = df.groupby('game_type').agg({
                'bet_amount': 'sum',
                'profit_loss': 'sum'
            })
            self.textbox.insert("end", game_stats.to_string())

# ─── MAIN EXECUTION ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()