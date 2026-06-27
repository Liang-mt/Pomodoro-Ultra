"""
番茄钟应用 - 至尊版 (Pomodoro Ultra)
=====================================
修复：闪烁/重复窗口/跳过卡顿
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import math
import random
import time
import threading
import sys
import os
from collections import deque
from pathlib import Path
from PIL import Image, ImageDraw, ImageTk


def get_base_path():
    """获取基础路径（兼容打包后的 exe）"""
    if getattr(sys, 'frozen', False):
        # 打包后的 exe
        return Path(sys._MEIPASS)
    else:
        # 开发环境
        return Path(__file__).parent


# ============================================================
# 主题配置
# ============================================================

THEMES = {
    "dark": {
        "bg": "#0a0a1a", "bg2": "#1a1a3e", "bg3": "#2a2a4e",
        "fg": "#e0e0e0", "accent": "#ff6b6b", "success": "#00b894",
        "warning": "#fdcb6e", "work": "#ff6b6b", "break": "#4ecdc4", "long_break": "#a29bfe",
    },
    "ocean": {
        "bg": "#0c1445", "bg2": "#1a237e", "bg3": "#283593",
        "fg": "#e3f2fd", "accent": "#00bcd4", "success": "#4caf50",
        "warning": "#ff9800", "work": "#ff5722", "break": "#00bcd4", "long_break": "#9c27b0",
    },
    "sunset": {
        "bg": "#1a0a2e", "bg2": "#2d1b4e", "bg3": "#3d2b5e",
        "fg": "#ffecd2", "accent": "#ff6b6b", "success": "#51cf66",
        "warning": "#ffd43b", "work": "#ff6b6b", "break": "#51cf66", "long_break": "#845ef7",
    },
    "forest": {
        "bg": "#0d1f0d", "bg2": "#1a3a1a", "bg3": "#2a4a2a",
        "fg": "#d4edda", "accent": "#28a745", "success": "#20c997",
        "warning": "#ffc107", "work": "#dc3545", "break": "#28a745", "long_break": "#17a2b8",
    },
    "cyberpunk": {
        "bg": "#0a0015", "bg2": "#1a0030", "bg3": "#2a0045",
        "fg": "#f5f5f5", "accent": "#ff00ff", "success": "#00ff88",
        "warning": "#ffff00", "work": "#ff0055", "break": "#00ffff", "long_break": "#ff00ff",
    }
}


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


# ============================================================
# 粒子类
# ============================================================

class Particle:
    def __init__(self, x, y, color, size=3, lifetime=2.0):
        self.x, self.y = x, y
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.alpha = 1.0
        self.alive = True

    def update(self, dt):
        self.lifetime -= dt
        self.alpha = max(0, self.lifetime / self.max_lifetime)
        if self.lifetime <= 0: self.alive = False

    def draw(self, draw): pass


class FireworkParticle(Particle):
    def __init__(self, x, y, color):
        super().__init__(x, y, color, random.uniform(2, 5), random.uniform(0.8, 2.0))
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 8)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.gravity = 0.08

    def update(self, dt):
        self.vy += self.gravity
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.99
        self.vy *= 0.99
        super().update(dt)

    def draw(self, draw):
        if not self.alive: return
        alpha = int(self.alpha * 255)
        size = self.size * self.alpha
        if size > 0.5:
            draw.ellipse([self.x-size, self.y-size, self.x+size, self.y+size], fill=(*self.color, alpha))


class GlowParticle(Particle):
    def __init__(self, x, y, color, drift=True):
        super().__init__(x, y, color, random.uniform(3, 10), random.uniform(1.5, 4.0))
        self.vx = random.uniform(-0.5, 0.5) if drift else 0
        self.vy = random.uniform(-1.5, -0.5)

    def update(self, dt):
        self.x += self.vx
        self.y += self.vy
        super().update(dt)

    def draw(self, draw):
        if not self.alive: return
        alpha = int(self.alpha * 255)
        glow_size = self.size * 2
        draw.ellipse([self.x-glow_size, self.y-glow_size, self.x+glow_size, self.y+glow_size], fill=(*self.color, int(alpha*0.3)))
        draw.ellipse([self.x-self.size, self.y-self.size, self.x+self.size, self.y+self.size], fill=(*self.color, alpha))


class StarParticle(Particle):
    def __init__(self, x, y, color):
        super().__init__(x, y, color, random.uniform(1, 3), random.uniform(2, 5))
        self.twinkle = random.uniform(0, 2 * math.pi)

    def update(self, dt):
        self.twinkle += 5 * dt
        super().update(dt)

    def draw(self, draw):
        if not self.alive: return
        brightness = (math.sin(self.twinkle) + 1) / 2
        alpha = int(self.alpha * brightness * 255)
        size = self.size * (0.5 + brightness * 0.5)
        draw.ellipse([self.x-size, self.y-size, self.x+size, self.y+size], fill=(*self.color, alpha))


class MeteorParticle(Particle):
    def __init__(self, width, height):
        x = random.randint(0, width)
        y = random.randint(-50, 0)
        color = random.choice([(255, 255, 255), (255, 215, 0), (135, 206, 235)])
        super().__init__(x, y, color, random.uniform(2, 4), random.uniform(0.5, 1.5))
        self.vx = random.uniform(-3, -1)
        self.vy = random.uniform(4, 8)
        self.trail = deque(maxlen=20)

    def update(self, dt):
        self.trail.append((self.x, self.y, self.size))
        self.x += self.vx
        self.y += self.vy
        super().update(dt)

    def draw(self, draw):
        if not self.alive: return
        for i, (tx, ty, ts) in enumerate(self.trail):
            alpha = int((i+1) / len(self.trail) * self.alpha * 255)
            size = ts * alpha / 255
            if size > 0.3:
                draw.ellipse([tx-size, ty-size, tx+size, ty+size], fill=(*self.color, alpha))
        size = self.size * 1.5
        draw.ellipse([self.x-size, self.y-size, self.x+size, self.y+size], fill=(255, 255, 255, int(self.alpha*255)))


class MatrixDrop(Particle):
    def __init__(self, x, y, speed):
        color = random.choice([(0, 255, 0), (0, 204, 0), (0, 153, 0)])
        super().__init__(x, y, color, random.uniform(8, 12), random.uniform(2, 4))
        self.vy = speed

    def update(self, dt):
        self.y += self.vy
        super().update(dt)

    def draw(self, draw):
        if not self.alive: return
        alpha = int(self.alpha * 255)
        size = self.size / 2
        draw.ellipse([self.x-size, self.y-size, self.x+size, self.y+size], fill=(*self.color, alpha))


# ============================================================
# 粒子系统
# ============================================================

class ParticleSystem:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.particles = deque(maxlen=500)
        self.effect_mode = "firework"

    def set_mode(self, mode): self.effect_mode = mode

    def emit_firework(self, x, y, count=50):
        colors = [(255,107,107),(78,205,196),(69,183,209),(255,234,167),(221,160,221),(100,255,255)]
        for _ in range(count):
            self.particles.append(FireworkParticle(x, y, random.choice(colors)))

    def emit_aurora(self):
        for _ in range(3):
            x, y = random.randint(0, self.width), random.randint(0, self.height//2)
            self.particles.append(GlowParticle(x, y, random.choice([(0,255,136),(0,255,204),(136,255,0)])))

    def emit_meteor(self): self.particles.append(MeteorParticle(self.width, self.height))

    def emit_matrix(self):
        for _ in range(2): self.particles.append(MatrixDrop(random.randint(0, self.width), 0, random.uniform(3, 6)))

    def emit_rain(self):
        for _ in range(5):
            p = GlowParticle(random.randint(0, self.width), random.randint(-20, 0), random.choice([(74,144,217),(91,163,230)]), drift=False)
            p.vy, p.vx = random.uniform(5, 10), random.uniform(-0.5, 0.5)
            self.particles.append(p)

    def emit_snow(self):
        for _ in range(3):
            p = StarParticle(random.randint(0, self.width), random.randint(-20, 0), (255, 255, 255))
            p.vy, p.vx = random.uniform(1, 3), random.uniform(-0.5, 0.5)
            self.particles.append(p)

    def emit_stars(self):
        self.particles.append(StarParticle(random.randint(0, self.width), random.randint(0, self.height), random.choice([(255,215,0),(255,255,255)])))

    def emit_ambient(self, is_work):
        x, y = random.randint(50, self.width-50), random.randint(50, self.height-50)
        if is_work:
            self.particles.append(GlowParticle(x, y, random.choice([(255,107,107),(255,142,142)])))
        else:
            self.particles.append(GlowParticle(x, y, random.choice([(78,205,196),(69,183,209)])))

    def update(self, dt):
        alive = deque(maxlen=500)
        for p in self.particles:
            p.update(dt)
            if p.alive: alive.append(p)
        self.particles = alive

    def draw(self, draw):
        for p in self.particles: p.draw(draw)


# ============================================================
# 多轨音乐播放器
# ============================================================

class MultiTrackPlayer:
    def __init__(self):
        self.tracks = {}
        self.volume = 0.5
        self.init_pygame()
        self.load_builtin_tracks()

    def init_pygame(self):
        try:
            import pygame
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
            pygame.mixer.set_num_channels(20)
        except Exception as e:
            print(f"Pygame init error: {e}")

    def load_builtin_tracks(self):
        sounds_dir = get_base_path() / "sounds"
        track_map = {
            "brook.mp3": "🏞️ 小溪", "summer.mp3": "🌙 夏夜",
            "birds.mp3": "🐦 小鸟", "wind-chime.mp3": "🎐 风铃",
            "autumn.mp3": "🍂 秋风", "bonfire.mp3": "🔥 篝火",
            "tide.mp3": "🌊 潮汐", "rain.mp3": "🌧️ 大雨",
        }

        import pygame
        for filename, display_name in track_map.items():
            filepath = sounds_dir / filename
            if filepath.exists():
                try:
                    sound = pygame.mixer.Sound(str(filepath))
                    sound.set_volume(self.volume)
                    channel = pygame.mixer.Channel(len(self.tracks))
                    self.tracks[display_name] = {
                        "sound": sound, "channel": channel, "playing": False
                    }
                except Exception as e:
                    print(f"Error loading {filename}: {e}")

    def toggle_track(self, name):
        if name not in self.tracks: return False
        track = self.tracks[name]
        if track["playing"]:
            track["channel"].stop()
            track["playing"] = False
        else:
            track["channel"].play(track["sound"], loops=-1)
            track["playing"] = True
        return track["playing"]

    def set_master_volume(self, volume):
        self.volume = max(0, min(1, volume))
        for track in self.tracks.values():
            track["sound"].set_volume(self.volume)

    def play_custom(self, path):
        try:
            import pygame
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"Play error: {e}")

    def stop_all(self):
        import pygame
        pygame.mixer.music.stop()
        for track in self.tracks.values():
            track["channel"].stop()
            track["playing"] = False

    def pause_all(self):
        import pygame
        pygame.mixer.music.pause()
        for track in self.tracks.values():
            track["channel"].pause()

    def unpause_all(self):
        import pygame
        pygame.mixer.music.unpause()
        for track in self.tracks.values():
            track["channel"].unpause()


# ============================================================
# 番茄钟主应用
# ============================================================

class PomodoroApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("🍅 番茄钟 - Pomodoro Ultra")
        self.geometry("900x700")
        self.minsize(800, 650)

        self.current_theme = "dark"
        self.colors = THEMES[self.current_theme]

        self.work_time = 25 * 60
        self.short_break = 5 * 60
        self.long_break = 15 * 60
        self.sessions_before_long = 4

        self.time_left = self.work_time
        self.is_running = False
        self.is_work_time = True
        self.pomodoro_count = 0
        self.total_focus_time = 0

        self.pulse_phase = 0
        self.rotation = 0
        self.bg_stars = []
        self.canvas_width = 600
        self.canvas_height = 380

        self.particle_system = ParticleSystem(self.canvas_width, self.canvas_height)
        self.music_player = MultiTrackPlayer()

        # 跟踪打开的窗口
        self.music_window = None
        self.settings_window = None
        self.track_buttons = {}

        self.generate_bg_stars()
        self.setup_ui()
        self.animate()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.music_player.stop_all()
        self.destroy()

    def generate_bg_stars(self):
        for _ in range(60):
            self.bg_stars.append({
                'x': random.randint(0, self.canvas_width),
                'y': random.randint(0, self.canvas_height),
                'size': random.uniform(0.5, 1.5),
                'twinkle': random.uniform(0, 2 * math.pi),
                'speed': random.uniform(1, 2)
            })

    def setup_ui(self):
        self.configure(fg_color=self.colors["bg"])
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=15)
        self.setup_top_bar()
        self.setup_timer_area()
        self.setup_bottom_area()

    def setup_top_bar(self):
        top_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        top_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(top_frame, text="🍅 番茄钟", font=ctk.CTkFont(size=26, weight="bold"), text_color=self.colors["fg"]).pack(side="left")

        btn_group = ctk.CTkFrame(top_frame, fg_color="transparent")
        btn_group.pack(side="right")

        self.effect_btn = ctk.CTkButton(btn_group, text="✨ 特效", width=80, height=30, fg_color=self.colors["bg2"], hover_color=self.colors["accent"], command=self.cycle_effect)
        self.effect_btn.pack(side="left", padx=5)

        self.music_btn = ctk.CTkButton(btn_group, text="🎵 音乐", width=80, height=30, fg_color=self.colors["bg2"], hover_color=self.colors["accent"], command=self.open_music_panel)
        self.music_btn.pack(side="left", padx=5)

        self.theme_btn = ctk.CTkButton(btn_group, text="🎨 主题", width=80, height=30, fg_color=self.colors["accent"], hover_color=self.colors["work"], command=self.cycle_theme)
        self.theme_btn.pack(side="left", padx=5)

        self.settings_btn = ctk.CTkButton(btn_group, text="⚙️ 设置", width=80, height=30, fg_color=self.colors["bg2"], hover_color=self.colors["accent"], command=self.open_settings)
        self.settings_btn.pack(side="left", padx=5)

    def setup_timer_area(self):
        timer_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        timer_frame.pack(fill="both", expand=True, pady=5)

        self.canvas_label = tk.Label(timer_frame, bg=self.colors["bg"], highlightthickness=0)
        self.canvas_label.pack(expand=True)
        self.canvas_image = None

        info_frame = ctk.CTkFrame(timer_frame, fg_color="transparent")
        info_frame.pack(pady=5)

        self.status_label = ctk.CTkLabel(info_frame, text="💪 专注时间", font=ctk.CTkFont(size=14), text_color=self.colors["warning"])
        self.status_label.pack(side="left", padx=20)

        self.count_label = ctk.CTkLabel(info_frame, text="🍅 × 0", font=ctk.CTkFont(size=14), text_color=self.colors["accent"])
        self.count_label.pack(side="right", padx=20)

        # 时间显示框架 - 可点击调节
        time_frame = ctk.CTkFrame(timer_frame, fg_color="transparent")
        time_frame.pack(pady=10)

        # 当前选中的部分: 0=小时, 1=分钟, 2=秒
        self.time_part = 1  # 默认选中分钟
        self.time_parts = [0, 25, 0]  # [时, 分, 秒]

        # 小时
        self.hour_label = tk.Label(time_frame, text="00", font=("Courier New", 48, "bold"),
                                   bg=self.colors["bg"], fg=self.colors["fg"], cursor="hand2")
        self.hour_label.pack(side="left")
        self.hour_label.bind("<Button-1>", lambda e: self.select_time_part(0))
        self.hour_label.bind("<MouseWheel>", self.on_time_scroll)

        # 冒号1
        self.colon1 = tk.Label(time_frame, text=":", font=("Courier New", 48, "bold"),
                               bg=self.colors["bg"], fg=self.colors["fg"])
        self.colon1.pack(side="left")

        # 分钟
        self.min_label = tk.Label(time_frame, text="25", font=("Courier New", 48, "bold"),
                                  bg=self.colors["bg"], fg=self.colors["accent"], cursor="hand2")
        self.min_label.pack(side="left")
        self.min_label.bind("<Button-1>", lambda e: self.select_time_part(1))
        self.min_label.bind("<MouseWheel>", self.on_time_scroll)

        # 冒号2
        self.colon2 = tk.Label(time_frame, text=":", font=("Courier New", 48, "bold"),
                               bg=self.colors["bg"], fg=self.colors["fg"])
        self.colon2.pack(side="left")

        # 秒
        self.sec_label = tk.Label(time_frame, text="00", font=("Courier New", 48, "bold"),
                                  bg=self.colors["bg"], fg=self.colors["fg"], cursor="hand2")
        self.sec_label.pack(side="left")
        self.sec_label.bind("<Button-1>", lambda e: self.select_time_part(2))
        self.sec_label.bind("<MouseWheel>", self.on_time_scroll)

        # 提示标签
        self.time_hint = tk.Label(timer_frame, text="点击时分秒可调节 | 滚轮增减",
                                  font=("Arial", 10), bg=self.colors["bg"], fg=self.colors["bg3"])
        self.time_hint.pack(pady=5)

        # 更新时间显示高亮
        self.update_time_highlight()

    def setup_bottom_area(self):
        bottom_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        bottom_frame.pack(fill="x", pady=(10, 0))

        btn_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        btn_frame.pack(pady=10)

        btn_style = {"width": 110, "height": 40, "font": ctk.CTkFont(size=14, weight="bold"), "corner_radius": 8}

        self.start_btn = ctk.CTkButton(btn_frame, text="▶ 开始", fg_color=self.colors["success"], hover_color="#00a884", command=self.start_timer, **btn_style)
        self.start_btn.pack(side="left", padx=8)

        self.pause_btn = ctk.CTkButton(btn_frame, text="⏸ 暂停", fg_color=self.colors["warning"], hover_color="#e6b800", command=self.pause_timer, state="disabled", **btn_style)
        self.pause_btn.pack(side="left", padx=8)

        self.reset_btn = ctk.CTkButton(btn_frame, text="🔄 重置", fg_color=self.colors["accent"], hover_color="#d63851", command=self.reset_timer, **btn_style)
        self.reset_btn.pack(side="left", padx=8)

        self.skip_btn = ctk.CTkButton(btn_frame, text="⏭ 跳过", fg_color=self.colors["bg3"], hover_color=self.colors["accent"], command=self.skip_timer, **btn_style)
        self.skip_btn.pack(side="left", padx=8)

        stats_frame = ctk.CTkFrame(bottom_frame, fg_color=self.colors["bg2"], corner_radius=12)
        stats_frame.pack(fill="x", pady=15, ipady=10)

        stats_inner = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_inner.pack(expand=True)

        self.stat_pomodoros = self.create_stat_item(stats_inner, "🍅 今日", "0")
        self.stat_pomodoros.pack(side="left", padx=35)

        self.stat_focus = self.create_stat_item(stats_inner, "⏱️ 专注", "0 分钟")
        self.stat_focus.pack(side="left", padx=35)

        self.stat_session = self.create_stat_item(stats_inner, "📊 阶段", "1/4")
        self.stat_session.pack(side="left", padx=35)

        self.stat_effect = self.create_stat_item(stats_inner, "✨ 特效", "烟花")
        self.stat_effect.pack(side="left", padx=35)

    def create_stat_item(self, parent, title, value):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=11), text_color=self.colors["fg"]).pack()
        value_label = ctk.CTkLabel(frame, text=value, font=ctk.CTkFont(size=18, weight="bold"), text_color=self.colors["accent"])
        value_label.pack()
        frame._value_label = value_label
        return frame

    def update_stat(self, stat_frame, value):
        stat_frame._value_label.configure(text=value)

    def select_time_part(self, part):
        """选择时/分/秒"""
        if self.is_running:
            return
        self.time_part = part
        self.update_time_highlight()

    def update_time_highlight(self):
        """更新时间显示高亮"""
        # 时分秒对应不同颜色
        part_colors = [
            "#FFD700",  # 小时 - 金色
            "#00BFFF",  # 分钟 - 蓝色
            "#FF69B4",  # 秒 - 粉色
        ]

        colors = [self.colors["fg"], self.colors["fg"], self.colors["fg"]]
        colors[self.time_part] = part_colors[self.time_part]

        self.hour_label.configure(fg=colors[0])
        self.min_label.configure(fg=colors[1])
        self.sec_label.configure(fg=colors[2])

    def on_time_scroll(self, event):
        """滚轮调节时间"""
        if self.is_running:
            return

        # 滚轮方向
        delta = 1 if event.delta > 0 else -1

        # 调节对应部分
        if self.time_part == 0:  # 小时
            self.time_parts[0] = max(0, min(23, self.time_parts[0] + delta))
        elif self.time_part == 1:  # 分钟
            self.time_parts[1] = max(0, min(59, self.time_parts[1] + delta))
        else:  # 秒
            self.time_parts[2] = max(0, min(59, self.time_parts[2] + delta))

        # 更新显示
        self.update_time_display()

        # 更新 time_left
        self.time_left = self.time_parts[0] * 3600 + self.time_parts[1] * 60 + self.time_parts[2]

    def update_time_display(self):
        """更新时间显示"""
        self.hour_label.configure(text=f"{self.time_parts[0]:02d}")
        self.min_label.configure(text=f"{self.time_parts[1]:02d}")
        self.sec_label.configure(text=f"{self.time_parts[2]:02d}")

    def create_frame_image(self):
        img = Image.new('RGBA', (self.canvas_width, self.canvas_height), hex_to_rgb(self.colors["bg"]) + (255,))
        draw = ImageDraw.Draw(img, 'RGBA')

        for star in self.bg_stars:
            star['twinkle'] += star['speed'] * 0.02
            brightness = (math.sin(star['twinkle']) + 1) / 2
            size = star['size'] * (0.5 + brightness * 0.5)
            if size > 0.3:
                draw.ellipse([star['x']-size, star['y']-size, star['x']+size, star['y']+size], fill=(*hex_to_rgb(self.colors["fg"]), int(brightness*200)))

        cx, cy = self.canvas_width // 2, self.canvas_height // 2 - 20
        radius = 100

        # 外圈装饰
        draw.ellipse([cx-radius-15, cy-radius-15, cx+radius+15, cy+radius+15], outline=(*hex_to_rgb(self.colors["bg3"]), 150), width=2)

        # 背景圆环（灰色轨道）
        draw.ellipse([cx-radius, cy-radius, cx+radius, cy+radius], outline=(*hex_to_rgb(self.colors["bg2"]), 200), width=10)

        # 根据运行状态决定进度显示方式
        if self.is_running:
            # 运行时：显示倒计时进度
            total = self.work_time if self.is_work_time else (self.long_break if self.pomodoro_count % self.sessions_before_long == 0 else self.short_break)
            color = hex_to_rgb(self.colors["work"] if self.is_work_time else self.colors["break"])
            progress = self.time_left / total  # 剩余时间比例
        else:
            # 未运行时：显示当前选中时分秒的进度
            if self.time_part == 0:  # 小时
                progress = self.time_parts[0] / 24
                color = hex_to_rgb("#FFD700")  # 金色
            elif self.time_part == 1:  # 分钟
                progress = self.time_parts[1] / 59
                color = hex_to_rgb("#00BFFF")  # 蓝色
            else:  # 秒
                progress = self.time_parts[2] / 59
                color = hex_to_rgb("#FF69B4")  # 粉色

        # 绘制进度弧（从顶部顺时针绘制）
        if progress > 0:
            extent = int(progress * 360)
            draw.arc([cx-radius, cy-radius, cx+radius, cy+radius], start=90, end=90+extent, fill=(*color, 255), width=10)

        # 运行时：旋转装饰点
        if self.is_running:
            for i in range(8):
                angle = self.rotation + i * 45
                rad = math.radians(angle)
                dx, dy = cx + math.cos(rad)*(radius+20), cy + math.sin(rad)*(radius+20)
                draw.ellipse([dx-2, dy-2, dx+2, dy+2], fill=(*color, 200))

        # 中心装饰（纯装饰，无文字）
        draw.ellipse([cx-radius+20, cy-radius+20, cx+radius-20, cy+radius-20], fill=(*hex_to_rgb(self.colors["bg2"]), 200), outline=(*hex_to_rgb(self.colors["bg3"]), 150), width=2)

        self.particle_system.update(0.033)
        self.particle_system.draw(draw)

        return img

    def animate(self):
        self.pulse_phase += 0.08
        self.rotation = (self.rotation + 0.5) % 360

        if self.is_running and random.random() < 0.15:
            self.particle_system.emit_ambient(self.is_work_time)

        effect = self.particle_system.effect_mode
        if effect == "aurora" and random.random() < 0.1: self.particle_system.emit_aurora()
        elif effect == "meteor" and random.random() < 0.01: self.particle_system.emit_meteor()
        elif effect == "matrix" and random.random() < 0.2: self.particle_system.emit_matrix()
        elif effect == "rain" and random.random() < 0.2: self.particle_system.emit_rain()
        elif effect == "snow" and random.random() < 0.15: self.particle_system.emit_snow()
        elif effect == "stars" and random.random() < 0.05: self.particle_system.emit_stars()

        img = self.create_frame_image()
        self.canvas_image = ImageTk.PhotoImage(img)
        self.canvas_label.configure(image=self.canvas_image)

        self.after(50, self.animate)

    def update_display(self):
        """更新显示"""
        # 更新时间部分
        hours = self.time_left // 3600
        minutes = (self.time_left % 3600) // 60
        seconds = self.time_left % 60

        self.time_parts = [hours, minutes, seconds]
        self.update_time_display()

        # 更新番茄计数
        if not hasattr(self, '_last_count') or self._last_count != self.pomodoro_count:
            self.count_label.configure(text=f"🍅 × {self.pomodoro_count}")
            self.update_stat(self.stat_pomodoros, str(self.pomodoro_count))
            self._last_count = self.pomodoro_count

        focus_min = int(self.total_focus_time // 60)
        if not hasattr(self, '_last_focus') or self._last_focus != focus_min:
            self.update_stat(self.stat_focus, f"{focus_min} 分钟")
            self._last_focus = focus_min

        self.update_stat(self.stat_session, f"{(self.pomodoro_count % self.sessions_before_long) + 1}/{self.sessions_before_long}")

    def start_timer(self):
        if not self.is_running:
            self.is_running = True
            self.start_btn.configure(state="disabled")
            self.pause_btn.configure(state="normal")
            threading.Thread(target=self.run_timer, daemon=True).start()

    def run_timer(self):
        while self.is_running and self.time_left > 0:
            time.sleep(1)
            if self.is_running:
                self.time_left -= 1
                if self.is_work_time: self.total_focus_time += 1
                self.after(0, self.update_display)
        if self.time_left <= 0: self.after(0, self.timer_finished)

    def pause_timer(self):
        self.is_running = False
        self.start_btn.configure(state="normal")
        self.pause_btn.configure(state="disabled")

    def reset_timer(self):
        self.is_running = False
        self.time_left = self.work_time if self.is_work_time else self.short_break

        # 更新 time_parts
        hours = self.time_left // 3600
        minutes = (self.time_left % 3600) // 60
        seconds = self.time_left % 60
        self.time_parts = [hours, minutes, seconds]
        self.update_time_display()

        self.start_btn.configure(state="normal")
        self.pause_btn.configure(state="disabled")

    def skip_timer(self):
        """跳过 - 不弹窗，直接切换"""
        self.is_running = False
        self.switch_phase()

    def timer_finished(self):
        """计时结束 - 不弹窗，直接切换"""
        self.is_running = False

        # 烟花效果
        for _ in range(5):
            self.particle_system.emit_firework(random.randint(100, self.canvas_width-100), random.randint(50, self.canvas_height-100), 60)

        # 播放提示音
        try:
            import winsound
            winsound.Beep(800, 200)
            winsound.Beep(1000, 200)
            winsound.Beep(1200, 300)
        except: self.bell()

        self.switch_phase()

    def switch_phase(self):
        """切换工作/休息阶段 - 不阻塞UI"""
        if self.is_work_time:
            self.pomodoro_count += 1
            if self.pomodoro_count % self.sessions_before_long == 0:
                self.time_left = self.long_break
                self.status_label.configure(text="🎉 长休息", text_color=self.colors["long_break"])
            else:
                self.time_left = self.short_break
                self.status_label.configure(text="☕ 短休息", text_color=self.colors["break"])
        else:
            self.time_left = self.work_time
            self.status_label.configure(text="💪 专注", text_color=self.colors["work"])

        # 更新 time_parts
        hours = self.time_left // 3600
        minutes = (self.time_left % 3600) // 60
        seconds = self.time_left % 60
        self.time_parts = [hours, minutes, seconds]
        self.update_time_display()

        self.is_work_time = not self.is_work_time
        self.start_btn.configure(state="normal")
        self.pause_btn.configure(state="disabled")

    def cycle_theme(self):
        themes = list(THEMES.keys())
        idx = themes.index(self.current_theme)
        self.current_theme = themes[(idx + 1) % len(themes)]
        self.colors = THEMES[self.current_theme]
        self.configure(fg_color=self.colors["bg"])
        self.canvas_label.configure(bg=self.colors["bg"])
        self.status_label.configure(text_color=self.colors["work"] if self.is_work_time else self.colors["break"])
        self.time_label.configure(text_color=self.colors["fg"])
        self.count_label.configure(text_color=self.colors["accent"])
        for btn in [self.start_btn, self.pause_btn, self.reset_btn, self.skip_btn, self.theme_btn, self.effect_btn, self.music_btn, self.settings_btn]:
            btn.configure(fg_color=self.colors.get("bg2", self.colors["bg3"]))

    def cycle_effect(self):
        effects = ["firework", "aurora", "meteor", "matrix", "rain", "snow", "stars"]
        names = ["烟花", "极光", "流星", "矩阵", "雨滴", "雪花", "星空"]
        idx = effects.index(self.particle_system.effect_mode)
        self.particle_system.set_mode(effects[(idx + 1) % len(effects)])
        self.update_stat(self.stat_effect, names[(idx + 1) % len(names)])
        self.particle_system.particles.clear()

    # ============================================================
    # 音乐面板 - 防止重复打开
    # ============================================================

    def open_music_panel(self):
        """打开音乐面板，如果已打开则置顶"""
        if self.music_window is not None and self.music_window.winfo_exists():
            self.music_window.lift()
            self.music_window.focus_force()
            return

        self.music_window = ctk.CTkToplevel(self)
        win = self.music_window
        win.title("🎵 音乐播放器")
        win.geometry("450x600")
        win.configure(fg_color=self.colors["bg"])
        win.transient(self)  # 保持在主窗口上方

        def on_close():
            self.music_window = None
            win.destroy()

        win.protocol("WM_DELETE_WINDOW", on_close)

        ctk.CTkLabel(win, text="🎵 白噪音混音器", font=ctk.CTkFont(size=22, weight="bold"), text_color=self.colors["fg"]).pack(pady=15)

        scroll_frame = ctk.CTkScrollableFrame(win, fg_color=self.colors["bg2"], corner_radius=10, height=250)
        scroll_frame.pack(fill="x", padx=25, pady=10)

        self.track_buttons = {}
        for name in self.music_player.tracks.keys():
            btn_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            btn_frame.pack(fill="x", padx=5, pady=3)

            btn = ctk.CTkButton(
                btn_frame, text=f"  {name}", fg_color=self.colors["bg3"],
                hover_color=self.colors["accent"], height=35, anchor="w",
                command=lambda n=name: self.toggle_track(n)
            )
            btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
            self.track_buttons[name] = btn

            status = ctk.CTkLabel(btn_frame, text="●" if self.music_player.tracks[name]["playing"] else "○", width=30,
                                  text_color=self.colors["success"] if self.music_player.tracks[name]["playing"] else self.colors["fg"])
            status.pack(side="right")
            self.music_player.tracks[name]["status_label"] = status

        ctk.CTkFrame(win, fg_color=self.colors["bg3"], height=2).pack(fill="x", padx=25, pady=15)

        ctk.CTkLabel(win, text="自定义音乐", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.colors["accent"]).pack(pady=(0, 10))
        ctk.CTkButton(win, text="📁 选择音乐文件", fg_color=self.colors["success"], hover_color="#00a884", height=35, command=self.select_music).pack(pady=5)

        ctk.CTkLabel(win, text="主音量", font=ctk.CTkFont(size=12), text_color=self.colors["fg"]).pack(pady=(15, 5))
        slider = ctk.CTkSlider(win, from_=0, to=100, command=lambda v: self.music_player.set_master_volume(v/100), fg_color=self.colors["bg3"], progress_color=self.colors["accent"])
        slider.set(50)
        slider.pack(pady=5, padx=25)

        ctrl_frame = ctk.CTkFrame(win, fg_color="transparent")
        ctrl_frame.pack(pady=15)
        ctk.CTkButton(ctrl_frame, text="⏹ 全部停止", fg_color=self.colors["accent"], hover_color="#d63851", width=120, command=self.stop_all_tracks).pack(side="left", padx=10)
        ctk.CTkButton(ctrl_frame, text="❌ 关闭", fg_color=self.colors["bg3"], hover_color=self.colors["accent"], width=100, command=on_close).pack(side="left", padx=10)

    def toggle_track(self, name):
        is_playing = self.music_player.toggle_track(name)
        if name in self.track_buttons:
            if is_playing:
                self.track_buttons[name].configure(fg_color=self.colors["accent"])
                self.music_player.tracks[name]["status_label"].configure(text="●", text_color=self.colors["success"])
            else:
                self.track_buttons[name].configure(fg_color=self.colors["bg3"])
                self.music_player.tracks[name]["status_label"].configure(text="○", text_color=self.colors["fg"])

    def stop_all_tracks(self):
        self.music_player.stop_all()
        for name, btn in self.track_buttons.items():
            btn.configure(fg_color=self.colors["bg3"])
            self.music_player.tracks[name]["status_label"].configure(text="○", text_color=self.colors["fg"])

    def select_music(self):
        filetypes = [("音频文件", "*.mp3 *.wav *.ogg *.flac"), ("所有文件", "*.*")]
        filepath = filedialog.askopenfilename(filetypes=filetypes)
        if filepath:
            self.music_player.play_custom(filepath)

    # ============================================================
    # 设置面板 - 防止重复打开
    # ============================================================

    def open_settings(self):
        """打开设置，如果已打开则置顶"""
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.lift()
            self.settings_window.focus_force()
            return

        self.settings_window = ctk.CTkToplevel(self)
        win = self.settings_window
        win.title("⚙️ 设置")
        win.geometry("350x300")
        win.configure(fg_color=self.colors["bg"])
        win.transient(self)  # 保持在主窗口上方

        def on_close():
            self.settings_window = None
            win.destroy()

        win.protocol("WM_DELETE_WINDOW", on_close)

        ctk.CTkLabel(win, text="⚙️ 计时器设置", font=ctk.CTkFont(size=20, weight="bold"), text_color=self.colors["fg"]).pack(pady=15)

        entries = {}
        for label, key, default in [("工作时间(分钟):", "work", self.work_time // 60), ("短休息(分钟):", "short", self.short_break // 60), ("长休息(分钟):", "long", self.long_break // 60)]:
            frame = ctk.CTkFrame(win, fg_color="transparent")
            frame.pack(fill="x", padx=35, pady=8)
            ctk.CTkLabel(frame, text=label, text_color=self.colors["fg"]).pack(side="left")
            entry = ctk.CTkEntry(frame, width=70)
            entry.insert(0, str(default))
            entry.pack(side="right")
            entries[key] = entry

        def save():
            try:
                self.work_time = int(entries["work"].get()) * 60
                self.short_break = int(entries["short"].get()) * 60
                self.long_break = int(entries["long"].get()) * 60
                if self.is_work_time and not self.is_running:
                    self.time_left = self.work_time
                    self.update_display()
                on_close()
            except ValueError:
                pass

        ctk.CTkButton(win, text="💾 保存", fg_color=self.colors["success"], hover_color="#00a884", command=save).pack(pady=20)


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = PomodoroApp()
    app.mainloop()


if __name__ == "__main__":
    main()
