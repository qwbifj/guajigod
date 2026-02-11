import pygame
import sys
import os
import random
import re
import json
import base64
from src.systems.character.player import Player, Profession
from src.systems.character.cultivation import BodyCultivation
from src.systems.world.map import Map
from src.systems.world.monster import Monster
from src.systems.combat.battle import BattleSystem
from src.ui.renderer import Renderer
from src.ui.windows import AttributeWindow, EquipmentWindow, InventoryWindow, SettingsWindow, DialogWindow, QuestWindow, SkillWindow, FloatingText, TreasureWindow, ShopWindow
from src.systems.save_manager import SaveManager
from src.systems.world.npc import NPC, NPCManager
from src.systems.quest.manager import QuestManager, Quest, QuestStage, QuestStatus
from src.systems.equipment.item import Item, ItemType, ItemQuality, Equipment
from src.systems.equipment.database import EQUIPMENT_DB
from src.data.maps_db import MAPS_DB
from src.data.monsters_db import MONSTERS_DB
import time

from src.systems.combat.skills import SkillBook
from src.ui.skill import SkillAnimation

from src.systems.network_manager import NetworkManager
from src.core.input import handle_input as engine_handle_input

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 50, 50)     # Monster
BLUE = (50, 50, 200)    # Player
GREEN = (50, 200, 50)   # Friendly/Info
GRAY = (128, 128, 128)

import math

class LootAnimation:
    def __init__(self, start_x, start_y, target_x, target_y, item_type, item_data=None, amount=0, auto_collect=True):
        self.x = start_x
        self.y = start_y
        self.start_x = start_x
        self.start_y = start_y
        self.target_ui_x = target_x
        self.target_ui_y = target_y
        
        self.item_type = item_type # "gold", "ingot", "item", "bone_powder"
        self.item_data = item_data
        self.amount = amount
        self.auto_collect = auto_collect
        
        # Phase 1: Bloom/Scatter
        angle = random.uniform(0, 6.28)
        dist = random.uniform(30, 60) # Scatter distance
        self.ground_x = start_x + math.cos(angle) * dist
        self.ground_y = start_y + math.sin(angle) * dist
        
        self.state = "SCATTER" # SCATTER, WAIT, COLLECT
        self.timer = 0
        self.progress = 0.0

    def update(self):
        if self.state == "SCATTER":
            self.progress += 0.1
            if self.progress >= 1.0:
                self.progress = 1.0
                self.x = self.ground_x
                self.y = self.ground_y
                self.state = "WAIT"
                self.timer = 60 # 1 second wait
            else:
                # Ease out cubic
                t = 1 - pow(1 - self.progress, 3)
                self.x = self.start_x + (self.ground_x - self.start_x) * t
                self.y = self.start_y + (self.ground_y - self.start_y) * t
                
        elif self.state == "WAIT":
            self.timer -= 1
            if self.timer <= 0:
                self.state = "COLLECT"
                self.progress = 0.0
                self.start_collect_x = self.x
                self.start_collect_y = self.y
                
        elif self.state == "COLLECT":
            self.progress += 0.05
            if self.progress >= 1.0:
                return True # Finished
            
            # Ease in quadratic
            t = self.progress * self.progress
            self.x = self.start_collect_x + (self.target_ui_x - self.start_collect_x) * t
            self.y = self.start_collect_y + (self.target_ui_y - self.start_collect_y) * t
            
        return False

import asyncio

class GameEngine:
    def __init__(self):
        print("[DEBUG] Engine Init Start")
        pygame.init()
        print("[DEBUG] Pygame Initialized")
        
        # Design Resolution (virtual canvas)
        self.design_width = 1024
        self.design_height = 768
        # Logical canvas size (used by UI/layout)
        self.width = self.design_width
        self.height = self.design_height
        
        # Display Setup
        # Android / Web: fullscreen adaptive; PC: resizable window
        platform = sys.platform.lower()
        if platform in ("android", "emscripten"):
            # 0,0 + FULLSCREEN lets Pygame/web fill device resolution
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            # Desktop defaults to 1024x768, scaling handled by our logic
            self.screen = pygame.display.set_mode((self.design_width, self.design_height), pygame.RESIZABLE)
            
        pygame.display.set_caption("挂机成神 0.1.0 DEMO版 QQ群:479722752")
        self.clock = pygame.time.Clock()
        
        # Virtual Canvas
        self.canvas = pygame.Surface((self.design_width, self.design_height))
        
        # Scaling Parameters
        self.scale_ratio = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.update_scaling()

        # Treasure Event Logic
        self.kill_count = 0 # Pity counter for treasure spawn
        
        # Font Loading with Fallback
        self.font = None
        self.log_font = None
        
        # Resource path helper
        def resource_path(relative_path):
            try:
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.abspath(".")
            return os.path.join(base_path, relative_path)

        font_path = resource_path("simhei.ttf")
        print(f"[DEBUG] Loading font from {font_path}")
        
        # WEB OPTIMIZATION: Skip large font file on Web (Emscripten)
        if sys.platform == 'emscripten':
            print("[DEBUG] Web mode detected: Skipping custom font to save bandwidth")
            self.font = pygame.font.Font(None, 24) # Use default system font
            self.log_font = pygame.font.Font(None, 20)
        elif os.path.exists(font_path):
            try:
                self.font = pygame.font.Font(font_path, 16)
                self.log_font = pygame.font.Font(font_path, 14)
                print("[DEBUG] Font loaded successfully")
            except Exception as e:
                print(f"Failed to load simhei.ttf: {e}")
        else:
             print(f"[DEBUG] Font file not found at {font_path}")
        
        if self.font is None:
            try:
                self.font = pygame.font.SysFont("Arial", 16)
                self.log_font = pygame.font.SysFont("Arial", 14)
            except Exception as e:
                print(f"Failed to load SysFont: {e}")
                self.font = pygame.font.Font(None, 24)
                self.log_font = pygame.font.Font(None, 20)
        
        # Pass CANVAS to renderer, not screen
        self.renderer = Renderer(self.canvas, self.font)
        print("[DEBUG] Renderer Initialized")
        self.save_manager = SaveManager()
        self.network_manager = NetworkManager()
        print("[DEBUG] Managers Initialized")
        
        # Init Managers
        self.quest_manager = QuestManager()
        self.npc_manager = NPCManager()
        
        self.game_log = ["欢迎来到挂机成神!", "自动战斗已开启。", "点击下方按钮查看信息。"]

        # Auto-save Settings
        self.auto_save_enabled = False
        self.auto_save_interval = 5 # minutes
        self.last_save_time = time.time()
        
        self.init_game_data()
        
        # Experience Bar Tweening
        self.displayed_xp = 0
        self.target_xp = 0
        
        # New lists for visual effects
        self.floating_texts = []
        self.ui_floating_texts = []
        self.loot_animations = []
        self.skill_animations = []
        self.button_rects = {}
        self.npc_rects = {} # NPC click areas
        
        # Windows
        self.windows = {
            "属性": AttributeWindow(self.renderer, self.player),
            "装备": EquipmentWindow(self.renderer, self.player),
            "背包": InventoryWindow(self.renderer, self.player),
            "技能": SkillWindow(self.renderer, self.player),
            "设置": SettingsWindow(self.renderer, self),
            "任务": QuestWindow(self.renderer, self),
            "商店": ShopWindow(self.renderer, self.player),
            "对话": DialogWindow(self.renderer, "对话", "...") # Placeholder
        }
        # Pass game engine to inventory window for recycle logic
        self.windows["背包"].game_engine = self
        self.windows["商店"].game_engine = self
        # Initially hide dialog
        self.windows["对话"].visible = False
        
        # Settings
        self.skip_recycle_confirmation = False
        self.auto_recycle_enabled = False # New auto recycle
        self.recycle_qualities = { # Default qualities to recycle
            "普通": False,
            "优良": False,
            "精品": False,
            "极品": False,
            "传说": False
        }

        # Login State
        self.state = "LOGIN"
        self.username_input = ""
        self.password_input = ""
        self.remember_username = False
        self.remember_password = False
        self.active_input = 0 # 0: Username, 1: Password
        self.login_message = "请输入账号密码 (Enter切换/登录)"
        self.login_msg_color = BLACK
        
        self.load_login_config()

        # Character Selection State
        self.characters = [None, None, None]
        self.current_char_index = -1
        self.char_select_msg = ""

        # Character Creation State
        self.create_char_name = "英雄"
        self.create_char_gender = "男"
        self.create_char_slot_index = 0
        self.create_char_msg = "请输入角色名称并选择性别"
        self.create_char_msg_color = BLACK

        # Auto-pilot state
        self.auto_pilot_timer = 0
        # Fixed interval 0.5s (30 frames)
        self.auto_pilot_interval = 30 
        
        self.auto_combat_enabled = False # Auto Combat Toggle
        self.auto_combat_btn_rect = None # Auto Combat Button Rect
        
        self.save_btn_rect = None # Initialize
        self.logout_btn_rect = None # Initialize
        self.target_monster = None # Locked target for auto-pilot
        self.mp_regen_timer = 0 # Timer for MP regeneration
        self.manual_target_pos = None # (x, y) for manual click movement
        
        self.auto_recycle_timer = 0 # Timer for auto recycle check
        
        # Map Display Offset
        self.map_offset_x = 0
        self.map_offset_y = 0
        
        # Layout Constants
        self.layout = {
            "map": pygame.Rect(0, 0, 800, 600),
            "info": pygame.Rect(800, 0, 224, 600),
            "interaction": pygame.Rect(0, 600, 800, 168),
            "function": pygame.Rect(800, 600, 224, 168)
        }
        
        # Cursor Blink State
        self.cursor_visible = True
        self.cursor_timer = 0
        
        # Inject game_engine into EquipmentWindow for enhancement logic
        if "装备" in self.windows:
            self.windows["装备"].game_engine = self

    def update_scaling(self):
        screen_w, screen_h = self.screen.get_size()
        
        # Calculate scale to fit
        scale_w = screen_w / self.design_width
        scale_h = screen_h / self.design_height
        self.scale_ratio = min(scale_w, scale_h)
        
        # Calculate offsets to center
        final_w = self.design_width * self.scale_ratio
        final_h = self.design_height * self.scale_ratio
        
        self.offset_x = (screen_w - final_w) / 2
        self.offset_y = (screen_h - final_h) / 2

    def transform_input(self, pos):
        # Transform screen coordinates to canvas coordinates
        mx, my = pos
        canvas_x = (mx - self.offset_x) / self.scale_ratio
        canvas_y = (my - self.offset_y) / self.scale_ratio
        return int(canvas_x), int(canvas_y)

    def update_character_select(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.VIDEORESIZE:
                self.update_scaling()
                
            # Priority: Check Dialog (Modal)
            if self.windows["对话"].visible:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = self.transform_input(event.pos)
                    if self.windows["对话"].handle_click((mx, my), event.button):
                        pass
                # Block other interactions if dialog is visible
                continue

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = self.transform_input(pygame.mouse.get_pos())
                cx, cy = self.width // 2, self.height // 2
                
                # 3 Slots Horizontal
                # Slot width 200, spacing 20. Total w = 640.
                start_x = cx - 320
                slot_w = 200
                slot_h = 300
                spacing = 20
                
                for i in range(3):
                    rect = pygame.Rect(start_x + i * (slot_w + spacing), cy - 150, slot_w, slot_h)
                    
                    # Check "Play/Create" button inside slot
                    # Button at bottom of slot
                    btn_rect = pygame.Rect(rect.centerx - 50, rect.bottom - 50, 100, 30)
                    
                    if btn_rect.collidepoint(mx, my):
                        if self.characters[i]:
                            # Play
                            self.enter_game(i)
                        else:
                            # Create
                            self.create_char_slot_index = i
                            self.create_char_name = "英雄" # Reset default
                            self.create_char_gender = "男"
                            self.state = "CREATE_CHARACTER"
                            pygame.key.start_text_input()
                        return
                    
                    # Delete Button (Top Right of slot) - Only if char exists
                    if self.characters[i]:
                        del_rect = pygame.Rect(rect.right - 25, rect.top + 5, 20, 20)
                        if del_rect.collidepoint(mx, my):
                            # Confirm Delete
                            def on_confirm(opt):
                                if opt == "确定":
                                    self.characters[i] = None
                                    self.save_game_state()
                            
                            # msg = "角色一旦删除将无法找回，这意味着你将彻底失去当前角色的所有相关数据。\n确定删除吗？"
                            msg = [
                                {"text": "角色一旦删除将无法找回，", "color": (0, 0, 0), "bold": False},
                                {"text": "这意味着你将彻底失去当前角色的所有相关数据。", "color": (255, 0, 0), "bold": True},
                                {"text": "\n确定删除吗？", "color": (0, 0, 0), "bold": False}
                            ]
                            
                            self.windows["对话"] = DialogWindow(self.renderer, "删除角色", msg, ["确定", "取消"], on_confirm, show_close_button=False)
                            # Center Dialog
                            self.windows["对话"].rect.center = (self.width // 2, self.height // 2)
                            return

                # Logout/Back Button
                back_rect = pygame.Rect(cx - 50, cy + 200, 100, 30)
                if back_rect.collidepoint(mx, my):
                    self.state = "LOGIN"
                    self.network_manager.logout()

    def draw_character_select(self):
        self.canvas.fill(WHITE)
        cx, cy = self.width // 2, self.height // 2
        
        # Title
        title = self.renderer.cn_font.render("选择角色", True, BLACK)
        t_rect = title.get_rect(center=(cx, cy - 200))
        self.canvas.blit(title, t_rect)
        
        # Slots
        start_x = cx - 320
        slot_w = 200
        slot_h = 300
        spacing = 20
        
        for i in range(3):
            x = start_x + i * (slot_w + spacing)
            y = cy - 150
            rect = pygame.Rect(x, y, slot_w, slot_h)
            
            pygame.draw.rect(self.canvas, (245, 245, 245), rect, border_radius=10)
            pygame.draw.rect(self.canvas, BLACK, rect, 2, border_radius=10)
            
            char_data = self.characters[i]
            
            if char_data:
                # Character Info
                p = char_data["player"]
                
                # Name
                name_txt = self.renderer.cn_font.render(p.name, True, BLACK)
                name_rect = name_txt.get_rect(center=(rect.centerx, rect.top + 30))
                self.canvas.blit(name_txt, name_rect)
                
                # Level / Class
                info_txt = self.renderer.small_font.render(f"Lv.{p.level} {p.profession.value}", True, BLUE)
                info_rect = info_txt.get_rect(center=(rect.centerx, rect.top + 60))
                self.canvas.blit(info_txt, info_rect)
                
                # Gender
                g_txt = self.renderer.small_font.render(f"性别: {p.gender}", True, GRAY)
                g_rect = g_txt.get_rect(center=(rect.centerx, rect.top + 80))
                self.canvas.blit(g_txt, g_rect)
                
                # Avatar (Simple placeholder)
                av_color = BLUE if p.gender == "男" else (200, 100, 100)
                av_rect = pygame.Rect(rect.centerx - 30, rect.top + 100, 60, 60)
                pygame.draw.rect(self.canvas, av_color, av_rect, border_radius=30)
                
                # Play Button
                btn_rect = pygame.Rect(rect.centerx - 50, rect.bottom - 50, 100, 30)
                pygame.draw.rect(self.canvas, GREEN, btn_rect, border_radius=5)
                btn_txt = self.renderer.cn_font.render("进入游戏", True, WHITE)
                btn_t_rect = btn_txt.get_rect(center=btn_rect.center)
                self.canvas.blit(btn_txt, btn_t_rect)
                
                # Delete Button (X)
                del_rect = pygame.Rect(rect.right - 25, rect.top + 5, 20, 20)
                pygame.draw.rect(self.canvas, RED, del_rect, border_radius=3)
                del_txt = self.renderer.small_font.render("X", True, WHITE)
                del_t_rect = del_txt.get_rect(center=del_rect.center)
                self.canvas.blit(del_txt, del_t_rect)
                
            else:
                # Empty Slot
                empty_txt = self.renderer.cn_font.render("空位", True, GRAY)
                empty_rect = empty_txt.get_rect(center=(rect.centerx, rect.centery - 20))
                self.canvas.blit(empty_txt, empty_rect)
                
                # Create Button
                btn_rect = pygame.Rect(rect.centerx - 50, rect.bottom - 50, 100, 30)
                pygame.draw.rect(self.canvas, BLUE, btn_rect, border_radius=5)
                btn_txt = self.renderer.cn_font.render("创建角色", True, WHITE)
                btn_t_rect = btn_txt.get_rect(center=btn_rect.center)
                self.canvas.blit(btn_txt, btn_t_rect)

        # Back Button
        back_rect = pygame.Rect(cx - 50, cy + 200, 100, 30)
        pygame.draw.rect(self.canvas, GRAY, back_rect, border_radius=5)
        back_txt = self.renderer.cn_font.render("返回登录", True, WHITE)
        back_t_rect = back_txt.get_rect(center=back_rect.center)
        self.canvas.blit(back_txt, back_t_rect)
        
        # Draw Dialog if visible
        if self.windows["对话"].visible:
            self.windows["对话"].draw(self.canvas)

    def update_create_character(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.VIDEORESIZE:
                self.update_scaling()
                
            if event.type == pygame.TEXTINPUT:
                # Handle IME input (Chinese)
                if len(self.create_char_name) + len(event.text) <= 12:
                     self.create_char_name += event.text

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    # Start Game
                    if not self.create_char_name:
                        self.create_char_msg = "角色名称不能为空"
                        self.create_char_msg_color = RED
                        return
                    
                    self.perform_create_character()
                    
                elif event.key == pygame.K_BACKSPACE:
                    self.create_char_name = self.create_char_name[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.state = "CHARACTER_SELECT"
                    pygame.key.stop_text_input()
                else:
                    # Filter input: Chinese, Letters, Numbers only
                    char = event.unicode
                    if char and re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9]$', char):
                        if len(self.create_char_name) < 12:
                            self.create_char_name += char
                    
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = self.transform_input(pygame.mouse.get_pos())
                cx, cy = self.width // 2, self.height // 2
                
                # Check Gender Buttons
                male_rect = pygame.Rect(cx - 80, cy + 20, 60, 30)
                female_rect = pygame.Rect(cx + 20, cy + 20, 60, 30)
                
                if male_rect.collidepoint(mx, my):
                    self.create_char_gender = "男"
                elif female_rect.collidepoint(mx, my):
                    self.create_char_gender = "女"
                    
                # Check Start Button
                start_rect = pygame.Rect(cx - 50, cy + 80, 100, 40)
                if start_rect.collidepoint(mx, my):
                    if not self.create_char_name:
                        self.create_char_msg = "角色名称不能为空"
                        self.create_char_msg_color = RED
                        return
                    
                    self.perform_create_character()

                # Back Button
                back_rect = pygame.Rect(cx - 50, cy + 130, 100, 30)
                if back_rect.collidepoint(mx, my):
                    self.state = "CHARACTER_SELECT"
                    pygame.key.stop_text_input()

    def perform_create_character(self):
        # Create data
        new_char_data = self.create_new_character_data(self.create_char_name, self.create_char_gender)
        self.characters[self.create_char_slot_index] = new_char_data
        
        # Save
        self.save_game_state()
        
        # Return to Select
        self.state = "CHARACTER_SELECT"
        pygame.key.stop_text_input()
        self.char_select_msg = "角色创建成功"

    def draw_create_character(self):
        self.canvas.fill(WHITE)
        
        cx, cy = self.width // 2, self.height // 2
        
        # Title
        title = self.renderer.cn_font.render(f"创建角色 (位置 {self.create_char_slot_index + 1})", True, BLACK)
        t_rect = title.get_rect(center=(cx, cy - 100))
        self.canvas.blit(title, t_rect)
        
        # Name Input
        n_label = self.renderer.cn_font.render("角色名:", True, BLACK)
        self.canvas.blit(n_label, (cx - 150, cy - 40))
        
        n_rect = pygame.Rect(cx - 80, cy - 45, 200, 30)
        pygame.key.set_text_input_rect(n_rect)
        pygame.draw.rect(self.canvas, WHITE, n_rect)
        pygame.draw.rect(self.canvas, BLUE, n_rect, 2)
        
        n_txt = self.renderer.cn_font.render(self.create_char_name, True, BLACK)
        self.canvas.blit(n_txt, (n_rect.x + 5, n_rect.y + 5))
        
        # Gender Selection
        g_label = self.renderer.cn_font.render("性别:", True, BLACK)
        self.canvas.blit(g_label, (cx - 150, cy + 25))
        
        # Male
        male_rect = pygame.Rect(cx - 80, cy + 20, 60, 30)
        color = GREEN if self.create_char_gender == "男" else GRAY
        pygame.draw.rect(self.canvas, color, male_rect, border_radius=5)
        m_txt = self.renderer.cn_font.render("男", True, WHITE)
        m_rect = m_txt.get_rect(center=male_rect.center)
        self.canvas.blit(m_txt, m_rect)
        
        # Female
        female_rect = pygame.Rect(cx + 20, cy + 20, 60, 30)
        color = GREEN if self.create_char_gender == "女" else GRAY
        pygame.draw.rect(self.canvas, color, female_rect, border_radius=5)
        f_txt = self.renderer.cn_font.render("女", True, WHITE)
        f_rect = f_txt.get_rect(center=female_rect.center)
        self.canvas.blit(f_txt, f_rect)
        
        # Start Button
        start_rect = pygame.Rect(cx - 50, cy + 80, 100, 40)
        pygame.draw.rect(self.canvas, BLUE, start_rect, border_radius=5)
        s_txt = self.renderer.cn_font.render("创建并保存", True, WHITE)
        s_rect = s_txt.get_rect(center=start_rect.center)
        self.canvas.blit(s_txt, s_rect)

        # Back Button
        back_rect = pygame.Rect(cx - 50, cy + 130, 100, 30)
        pygame.draw.rect(self.canvas, GRAY, back_rect, border_radius=5)
        back_txt = self.renderer.cn_font.render("返回", True, WHITE)
        back_t_rect = back_txt.get_rect(center=back_rect.center)
        self.canvas.blit(back_txt, back_t_rect)
        
        # Message
        msg = self.renderer.cn_font.render(self.create_char_msg, True, self.create_char_msg_color)
        msg_rect = msg.get_rect(center=(cx, cy + 180))
        self.canvas.blit(msg, msg_rect)

    def load_game_data(self):
        # Try to load game (Cloud first if connected, else Local)
        saved_data = None
        
        if self.network_manager.is_connected:
             self.log("正在从云端加载存档...")
             cloud_data, msg = self.network_manager.load_game()
             if cloud_data:
                 saved_data = self.save_manager.load_from_dict(cloud_data)
                 self.log("云端存档加载成功！")
             else:
                 self.log(f"云端无存档或加载失败: {msg}")
                 self.log("尝试加载本地存档...")
                 local_filename = self.get_save_file_path()
                 username = self.network_manager.username
                 saved_data = self.save_manager.load_game(filename=local_filename, expected_username=username)
        else:
             saved_data = self.save_manager.load_game(filename="savegame.dat")

        # Load Characters
        if saved_data and "characters" in saved_data:
            self.characters = saved_data["characters"]
            # Ensure 3 slots
            while len(self.characters) < 3:
                self.characters.append(None)
                
            # Load Global Settings
            settings = saved_data.get("auto_save_settings", {})
            self.auto_save_enabled = settings.get("enabled", False)
            self.auto_save_interval = settings.get("interval", 5)
            self.skip_recycle_confirmation = settings.get("skip_recycle_confirmation", False)
            self.auto_recycle_enabled = settings.get("auto_recycle_enabled", False)
            saved_qualities = settings.get("recycle_qualities", {})
            if saved_qualities:
                for k, v in saved_qualities.items():
                    if k in self.recycle_qualities:
                        self.recycle_qualities[k] = v
                        
            self.log("读取存档成功！")
            self.state = "CHARACTER_SELECT"
            
        else:
            # No save found or invalid
            self.characters = [None, None, None]
            self.state = "CHARACTER_SELECT"
            self.log("请创建角色...")

    def create_new_character_data(self, name, gender):
        player = Player(name, Profession.WARRIOR, gender)
        player.x = 2
        player.y = 2
        player.ingots = 1000 # Temporary rule: New characters get 1000 Ingots
        
        qm = QuestManager()
        
        return {
            "player": player,
            "map_name": "新手村",
            "quest_manager": qm
        }

    def enter_game(self, slot_index):
        if slot_index < 0 or slot_index >= len(self.characters) or not self.characters[slot_index]:
            return
            
        char_data = self.characters[slot_index]
        self.current_char_index = slot_index
        
        self.player = char_data["player"]
        
        # Load Quest Manager
        if "quest_manager" in char_data and char_data["quest_manager"]:
            self.quest_manager = char_data["quest_manager"]
        else:
            self.quest_manager = QuestManager()
            
        # Re-init map (Reset monsters)
        target_map_id = getattr(self.player, 'map_id', 'NoviceVillage')
        if not self.load_map(target_map_id):
            self.current_map = Map("新手村", 1, width=20, height=15)
            self.current_map.add_monster_type(Monster("稻草人", 1, 30, 5, 0, 10))
            for _ in range(5):
                self.current_map.spawn_monster()

        # Update NPC Status
        self.update_npc_status()

        # Backward compatibility checks
        if not hasattr(self.player, 'gender'):
            self.player.gender = "男" 
            
        if not hasattr(self.player, 'map_id'):
            self.player.map_id = "NoviceVillage"

        if not hasattr(self.player, 'ingots'):
            self.player.ingots = 0
        
        if not hasattr(self.player, 'magic'): self.player.magic = 0
        if not hasattr(self.player, 'taoism'): self.player.taoism = 0
        if not hasattr(self.player, 'magic_defense'): self.player.magic_defense = 0
        
        if not hasattr(self.player, 'body_cultivation'):
            self.player.body_cultivation = BodyCultivation()

        # Re-link player to windows
        self.windows["属性"].player = self.player
        self.windows["装备"].player = self.player
        self.windows["背包"].player = self.player
        self.windows["技能"].player = self.player
        self.windows["商店"].player = self.player
        
        # Cleanup Debug Items (One-time fix for existing saves)
        cleaned_items = [item for item in self.player.inventory.items if item and not item.name.startswith("测试剑")]
        
        if self.player.inventory.capacity < 1000:
            self.player.inventory.capacity = 1000
            
        new_items = [None] * self.player.inventory.capacity
        for i, item in enumerate(cleaned_items):
            if i < len(new_items):
                new_items[i] = item
        self.player.inventory.items = new_items

        # Inventory Backward Compatibility
        if not hasattr(self.player.inventory, 'unlocked_pages'):
            self.player.inventory.unlocked_pages = 1
            self.player.inventory.page_size = 150
            if self.player.inventory.capacity < 600:
                self.player.inventory.capacity = 600
                new_items = [None] * 600
                for i, item in enumerate(self.player.inventory.items):
                    if i < 600: new_items[i] = item
                self.player.inventory.items = new_items

        # Equipment Migration
        for item in self.player.inventory.items:
            if item:
                if isinstance(item, Equipment):
                    if not hasattr(item, 'enhancement_level'): item.enhancement_level = 0
                    if not hasattr(item, 'durability'): item.durability = 100
                    if not hasattr(item, 'max_durability'): item.max_durability = 100
                
                # General Item Migration (Cover all items including UpgradeStone)
                if not hasattr(item, 'locked'): item.locked = False
        
        for slot, item in self.player.equipment.items():
            if item:
                if isinstance(item, Equipment):
                    if not hasattr(item, 'enhancement_level'): item.enhancement_level = 0
                    if not hasattr(item, 'durability'): item.durability = 100
                    if not hasattr(item, 'max_durability'): item.max_durability = 100
                
                if not hasattr(item, 'locked'): item.locked = False
        
        # Player Attributes
        if not hasattr(self.player, 'attack_speed'): self.player.attack_speed = 0
        if not hasattr(self.player, 'cooldown_reduction'): self.player.cooldown_reduction = 0.0

        # Skills Backward Compatibility
        if not hasattr(self.player, 'skills') or not self.player.skills:
            self.player.skill_book = SkillBook()
            self.player.skills = [self.player.skill_book.get_skill("Hellfire")]
            self.player.active_skill = self.player.skills[0]
        elif hasattr(self.player, 'skills'):
             updated_skills = []
             skill_book = SkillBook()
             for s in self.player.skills:
                 if s.name == "流星火雨" or s.name == "烈火梵天":
                     new_s = skill_book.get_skill("Hellfire")
                     updated_skills.append(new_s)
                     if self.player.active_skill and (self.player.active_skill.name == "流星火雨" or self.player.active_skill.name == "烈火梵天"):
                         self.player.active_skill = new_s
                 elif s.name == "烈火焚天":
                     new_s = skill_book.get_skill("Hellfire")
                     updated_skills.append(new_s)
                     if self.player.active_skill and self.player.active_skill.name == "烈火焚天":
                         self.player.active_skill = new_s
                 else:
                     updated_skills.append(s)
             
             self.player.skills = updated_skills
             if not self.player.active_skill and self.player.skills:
                 self.player.active_skill = self.player.skills[0]

        # Stackable Items
        if hasattr(self.player, 'inventory') and hasattr(self.player.inventory, 'items'):
             for item in self.player.inventory.items:
                if item:
                    if not hasattr(item, 'stackable'):
                        if item.name == "强化石" or item.name == "神话强化石":
                            item.stackable = True
                            item.max_stack = 99999
                        else:
                            item.stackable = False
                            item.max_stack = 1
                    if not hasattr(item, 'count'): item.count = 1
                        
        if hasattr(self.player, 'equipment'):
            for slot, item in self.player.equipment.items():
                if item:
                    if not hasattr(item, 'stackable'):
                        item.stackable = False
                        item.max_stack = 1
                    if not hasattr(item, 'count'): item.count = 1
        
        # Stats Rebalance Migration (Version 4)
        # Randomize with new multiplier logic: [min*mult, max*mult]
        if not hasattr(self.player, 'stats_version') or self.player.stats_version < 4:
            self.log("检测到数据需要更新，正在应用随机属性优化...")
            
            quality_mults = {
                "普通": 1.0, "优良": 2.0, "精品": 3.0, "极品": 4.0,
                "传说": 5.0, "史诗": 6.0, "神话": 7.0
            }
            
            def migrate_item_v4(item):
                if not item or not hasattr(item, 'quality'): return
                if item.name not in EQUIPMENT_DB: return 
                
                data = EQUIPMENT_DB[item.name]
                q_val = item.quality.value
                mult = quality_mults.get(q_val, 1.0)
                
                # Re-roll stats
                item.stats = {} 
                
                for stat, (min_v, max_v) in data["stats"].items():
                    # 1. Base min at least 1
                    base_min = max(1, min_v)
                    base_max = max(base_min, max_v)
                    
                    # 2. Scale range
                    scaled_min = int(base_min * mult)
                    scaled_max = int(base_max * mult)
                    
                    # 3. Randomize
                    val = random.randint(scaled_min, scaled_max)
                    
                    item.add_stat(stat, val)
            
            # Apply to Inventory
            for item in self.player.inventory.items:
                if item and getattr(item, 'is_equipment', False):
                    migrate_item_v4(item)
                    
            # Apply to Equipment
            for slot, item in self.player.equipment.items():
                if item:
                    migrate_item_v4(item)
            
            self.player.stats_version = 4
            self.player.recalculate_stats()
            self.log("装备属性随机优化完成。")

        # State: Playing
        self.state = "PLAYING"
        
        # Reset timers
        self.auto_pilot_interval = 30 
        self.save_btn_rect = None
        self.target_monster = None
        self.mp_regen_timer = 0
        self.manual_target_pos = None
        self.auto_recycle_timer = 0
        
        # Inject game_engine into EquipmentWindow for enhancement logic
        if "装备" in self.windows:
            self.windows["装备"].game_engine = self

    def load_map(self, map_key):
        if map_key not in MAPS_DB:
            print(f"[ERROR] Map {map_key} not found")
            return False
            
        map_data = MAPS_DB[map_key]
        
        # Create Map
        new_map = Map(map_data["name"], map_data["min_level"], 
                      width=map_data["width"], height=map_data["height"])
                      
        # Add Monster Templates
        for m_key in map_data["monsters"]:
            monster = Monster.create_from_db(m_key)
            if monster:
                new_map.add_monster_type(monster)
            else:
                print(f"[WARN] Monster {m_key} not found in DB")
                
        # Set Current Map
        self.current_map = new_map
        self.current_map.map_key = map_key # Store key for reference
        
        # Spawn Monsters
        # Density: 5% of tiles
        count = max(5, int(new_map.width * new_map.height * 0.05))
        for _ in range(count):
            self.current_map.spawn_monster()
            
        self.log(f"进入地图: {new_map.name} (Lv.{map_data['min_level']}-{map_data['max_level']})")
        
        # Reset player position to safe zone (usually top-left)
        self.player.x = 2
        self.player.y = 2
        
        # Stop auto-pilot when switching maps
        self.target_monster = None
        self.manual_target_pos = None
        
        return True

    def init_game_data(self, name="Hero", gender="男"):
        # Initialize Default Session (for __init__)
        data = self.create_new_character_data(name, gender)
        self.player = data["player"]
        
        # Initialize Map from DB
        if not self.load_map("NoviceVillage"):
            # Fallback if DB load fails
            self.current_map = Map("新手村", 1, width=20, height=15)
            self.current_map.add_monster_type(Monster("稻草人", 1, 30, 5, 0, 10))
            for _ in range(5):
                self.current_map.spawn_monster()
            
        # Define NPCs
        self.npc_manager.add_npc(NPC("老兵", "传送", "想去哪里冒险？"))
        self.npc_manager.add_npc(NPC("每日任务", "日常", "每日刷新任务"))
        self.npc_manager.add_npc(NPC("每周任务", "周常", "每周刷新任务"))
        self.npc_manager.add_npc(NPC("每月任务", "月常", "每月刷新任务"))
        self.npc_manager.add_npc(NPC("成就系统", "成就", "查看你的成就"))
        self.npc_manager.add_npc(NPC("门口超市", "商店", "买买买！"))
        self.npc_manager.add_npc(NPC("地下黑市", "黑市", "神秘物品出售"))
        
        self.update_npc_status()

    def update_npc_status(self):
        # Reset statuses
        for npc in self.npc_manager.npcs.values():
            npc.has_quest_available = False
            npc.has_quest_turn_in = False
            
    def interact_npc(self, npc_name):
        npc = self.npc_manager.get_npc(npc_name)
        if not npc: return
        
        if npc.name == "老兵":
            # Map Teleport Logic
            dialog_text = "你要去哪里？\n危险等级越高，收益越大。"
            
            # Create options from MAPS_DB
            # Map Name -> Map Key
            map_options = []
            map_keys = []
            
            # Use current_map.map_key if available, else assume NoviceVillage
            current_key = getattr(self.current_map, 'map_key', 'NoviceVillage')
            
            for key, data in MAPS_DB.items():
                if key == current_key: continue
                label = f"{data['name']} (Lv.{data['min_level']}-{data['max_level']})"
                map_options.append(label)
                map_keys.append(key)
                
            map_options.append("取消")
            
            def callback(opt):
                if opt == "取消": 
                    # self.windows["对话"].visible = False # Dialog handles this?
                    return
                
                # Find key
                idx = -1
                for i, o in enumerate(map_options):
                    if o == opt:
                        idx = i
                        break
                
                if idx != -1 and idx < len(map_keys):
                    target_key = map_keys[idx]
                    
                    # Optional: Check Level
                    # req = MAPS_DB[target_key]["min_level"]
                    # if self.player.level < req: ...
                    
                    self.load_map(target_key)
                    self.windows["对话"].visible = False
            
            self.windows["对话"] = DialogWindow(self.renderer, npc.name, dialog_text, map_options, callback, layout="matrix")
            self.windows["对话"].visible = True
            return
            
        elif npc.name == "门口超市":
            self.windows["商店"].visible = True
            return

        dialog_text = npc.description
        options = ["离开"]
        
        # Show Dialog
        def callback(opt):
            pass # Just close
            
        self.windows["对话"] = DialogWindow(self.renderer, npc.name, dialog_text, options, callback)
        self.windows["对话"].visible = True

    def handle_input(self):
        engine_handle_input(self)

    def log(self, message):
        self.game_log.append(message)
        if len(self.game_log) > 10:
            self.game_log.pop(0)

    def spawn_floating_text(self, text, grid_x, grid_y, color):
        # Convert grid to screen coords
        off_x = getattr(self, 'map_offset_x', 50)
        off_y = getattr(self, 'map_offset_y', 50)
        
        screen_x = off_x + grid_x * (self.renderer.tile_size + self.renderer.margin) + 10
        screen_y = off_y + grid_y * (self.renderer.tile_size + self.renderer.margin) - 20
        self.floating_texts.append(FloatingText(text, screen_x, screen_y, color))

    def spawn_ui_floating_text(self, text, screen_x, screen_y, color):
        """Spawn floating text at absolute screen coordinates"""
        self.ui_floating_texts.append(FloatingText(text, screen_x, screen_y, color))

    def spawn_loot_animation(self, grid_x, grid_y, item_type, item_data=None, amount=0, auto_collect=True):
        off_x = getattr(self, 'map_offset_x', 50)
        off_y = getattr(self, 'map_offset_y', 50)
        
        start_x = off_x + grid_x * (self.renderer.tile_size + self.renderer.margin)
        start_y = off_y + grid_y * (self.renderer.tile_size + self.renderer.margin)
        
        # Target is the "背包" button (Index 2 in 1 Row of 6)
        # Button Area: (0, 684, 800, 84)
        # Start X = 50. Btn Width = 100. Spacing = 20.
        # Index 2 X = 50 + 2 * 120 = 290.
        # Center X = 290 + 50 = 340.
        # Center Y = 684 + 20 = 704.
        
        target_x = 340
        target_y = 704
        
        self.loot_animations.append(LootAnimation(start_x, start_y, target_x, target_y, item_type, item_data, amount, auto_collect))

    # Old duplicate handle_input removed


    def spawn_treasure_event(self):
        # Limit total treasures: If ANY treasure exists, do not spawn another.
        if len(self.current_map.treasure_events) > 0:
            return 
            
        self.log(f"神秘宝藏出现了！")
        
        attempts = 0
        while attempts < 100:
            rx = random.randint(0, self.current_map.width - 1)
            ry = random.randint(0, self.current_map.height - 1)
            
            if not self.current_map.is_valid_move(rx, ry):
                attempts += 1
                continue
                
            if rx == self.player.x and ry == self.player.y:
                attempts += 1
                continue
                
            occupied = False
            for m in self.current_map.active_monsters:
                if m.x == rx and m.y == ry:
                    occupied = True
                    break
            if occupied:
                attempts += 1
                continue
                
            if (rx, ry) in self.current_map.treasure_events:
                attempts += 1
                continue
                
            # Random Quality (EPIC to DIVINE)
            # Weights: EPIC 60%, LEGENDARY 30%, MYTHIC 9%, DIVINE 1%
            qualities = [ItemQuality.EPIC, ItemQuality.LEGENDARY, ItemQuality.MYTHIC, ItemQuality.DIVINE]
            weights = [60, 30, 9, 1]
            q = random.choices(qualities, weights=weights, k=1)[0]
            
            self.current_map.treasure_events[(rx, ry)] = {
                'quality': q,
                'timestamp': time.time()
            }
            break

    def check_treasure_event(self, x, y):
        if (x, y) in self.current_map.treasure_events:
            event = self.current_map.treasure_events[(x, y)]
            q = event['quality']
            q_name = q.value
            
            # Determine Cost
            cost_gold = 0
            cost_ingots = 0
            
            if q == ItemQuality.EPIC: # 极品
                cost_gold = 1000
            elif q == ItemQuality.LEGENDARY: # 传说
                cost_gold = 5000
            elif q == ItemQuality.MYTHIC: # 史诗
                cost_ingots = 1
            elif q == ItemQuality.DIVINE: # 神话
                cost_ingots = 3
            
            cost_str = ""
            if cost_gold > 0: cost_str = f"{cost_gold} 金币"
            if cost_ingots > 0: cost_str = f"{cost_ingots} 元宝"
            
            def on_confirm(label):
                if label == "确定":
                    can_afford = False
                    if cost_gold > 0:
                        if self.player.gold >= cost_gold:
                            self.player.gold -= cost_gold
                            can_afford = True
                        else:
                            self.log("金币不足！")
                    elif cost_ingots > 0:
                        if self.player.ingots >= cost_ingots:
                            self.player.ingots -= cost_ingots
                            can_afford = True
                        else:
                            self.log("元宝不足！")
                    
                    if can_afford:
                        # Use Map Level Limits for Drop
                        map_key = getattr(self.current_map, 'map_key', None)
                        min_lvl = 1
                        max_lvl = 100
                        if map_key and map_key in MAPS_DB:
                            min_lvl = MAPS_DB[map_key].get("min_level", 1)
                            max_lvl = MAPS_DB[map_key].get("max_level", 100)
                            
                        drop = Equipment.create_random_drop(min_level=min_lvl, max_level=max_lvl, force_quality=q)
                        if drop:
                            # Show TreasureWindow instead of direct add
                            def on_collect():
                                if self.player.inventory.add_item(drop):
                                    self.log(f"开启宝藏获得: {drop.name} ({drop.quality.value})")
                                    self.spawn_loot_animation(x, y, "item", item_data=drop, auto_collect=False)
                                    if (x, y) in self.current_map.treasure_events:
                                        del self.current_map.treasure_events[(x, y)]
                                    return True # Success, close window
                                else:
                                    self.log("背包已满，无法获取物品。")
                                    self.spawn_floating_text("背包已满", self.player.x, self.player.y, (255, 0, 0))
                                    return False # Keep window open

                            self.windows["宝藏"] = TreasureWindow(self.renderer, drop, on_collect)
                            self.windows["宝藏"].rect.center = (self.width // 2, self.height // 2)
                        else:
                            self.log("宝藏是空的？（生成失败）")
                            # Refund
                            if cost_gold > 0: self.player.gold += cost_gold
                            if cost_ingots > 0: self.player.ingots += cost_ingots
                        
                elif label == "取消":
                    def on_cancel_confirm(l2):
                        if l2 == "确定":
                            if (x, y) in self.current_map.treasure_events:
                                del self.current_map.treasure_events[(x, y)]
                            self.log("你错失了这次机缘。")
                        else:
                            # Re-open main dialog if they regret cancelling
                            self.check_treasure_event(x, y)
                            
                    self.windows["二级提示"] = DialogWindow(self.renderer, "警告", "如果取消将错失良缘，请慎重考虑。", ["确定", "取消"], on_cancel_confirm)
                    self.windows["二级提示"].rect.center = (self.width // 2, self.height // 2)
            
            self.windows["宝藏"] = DialogWindow(self.renderer, "发现宝藏", f"发现 [{q_name}] 品质宝藏！\n是否花费 {cost_str} 开启？", ["确定", "取消"], on_confirm)
            self.windows["宝藏"].rect.center = (self.width // 2, self.height // 2)

    def update_ai(self):
        for monster in self.current_map.active_monsters:
            if not monster.is_alive(): continue
            
            monster.move_timer += 1
            if monster.move_timer >= monster.move_interval:
                monster.move_timer = 0
                if not monster.is_aggro:
                    monster.move_interval = random.randint(60, 180) # Reset timer normal
                    # Random move
                    direction = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
                else:
                    # Aggro move (Chase player)
                    # Simple chase: move towards player
                    dx, dy = 0, 0
                    if monster.x < self.player.x: dx = 1
                    elif monster.x > self.player.x: dx = -1
                    
                    if monster.y < self.player.y: dy = 1
                    elif monster.y > self.player.y: dy = -1
                    
                    # Prefer axis with larger distance? Or random axis?
                    # Let's try moving along one axis at a time to avoid zig-zags stuck
                    if dx != 0 and dy != 0:
                        if random.random() < 0.5: dy = 0
                        else: dx = 0
                    
                    direction = (dx, dy)

                dx, dy = direction
                new_x = monster.x + dx
                new_y = monster.y + dy
                
                # Validate move
                if self.current_map.is_valid_move(new_x, new_y):
                    # Check collision with player
                    if new_x == self.player.x and new_y == self.player.y:
                        # Attack player
                        self.combat_round(monster) # Monster attacks player logic inside
                        # If aggro, keep attacking? Yes.
                    
                    # Check collision with other monsters
                    occupied = False
                    for other in self.current_map.active_monsters:
                        if other != monster and other.x == new_x and other.y == new_y:
                            occupied = True
                            break
                    
                    if not occupied and not (new_x == self.player.x and new_y == self.player.y):
                        monster.x = new_x
                        monster.y = new_y

    def update_logic(self):
        # Auto Potion Check
        if self.player:
            self.player.check_auto_potion()

        # AI Update
        self.update_ai()
        
        # Update effects
        self.floating_texts = [ft for ft in self.floating_texts if ft.update()]
        self.ui_floating_texts = [ft for ft in self.ui_floating_texts if ft.update()]
        # Update Loot Animations
        active_anims = []
        for anim in self.loot_animations:
            if not anim.update():
                # Animation Running
                active_anims.append(anim)
            else:
                # Animation Finished (COLLECT phase done)
                if not anim.auto_collect:
                    pass # Already collected
                # Handle Collection
                elif anim.item_type == "gold":
                    self.player.gold += anim.amount
                    self.log(f"获得金币 +{anim.amount}")
                elif anim.item_type == "ingot":
                    self.player.ingots += anim.amount
                    self.log(f"运气爆棚！获得元宝 +{anim.amount}")
                elif anim.item_type == "item":
                    if self.player.inventory.add_item(anim.item_data):
                        self.log(f"获得: {anim.item_data.name} ({anim.item_data.quality.value})")
                        self.spawn_floating_text(f"+{anim.item_data.name}", self.player.x, self.player.y, GREEN)
                    else:
                        self.log("背包已满，无法获取掉落物品。")
                        self.spawn_floating_text("背包已满", self.player.x, self.player.y, (255, 0, 0))
                elif anim.item_type == "bone_powder":
                    if self.player.inventory.add_item(anim.item_data):
                        self.log(f"获得: 骨粉 x{anim.amount}")
                        self.spawn_floating_text(f"+骨粉 x{anim.amount}", self.player.x, self.player.y, GREEN)
                    else:
                        self.log("背包已满，无法获取骨粉")
        
        self.loot_animations = active_anims
        self.skill_animations = [sa for sa in self.skill_animations if sa.update()]
        
        # Auto-Save Check
        if self.auto_save_enabled:
            current_time = time.time()
            if current_time - self.last_save_time >= self.auto_save_interval * 60:
                self.save_game_state()
                self.last_save_time = current_time
                
        # Auto-Recycle Check
        if self.auto_recycle_enabled:
            self.auto_recycle_timer += 1
            if self.auto_recycle_timer >= 600: # 10 seconds * 60 FPS
                self.auto_recycle_timer = 0
                self.perform_auto_recycle()
        
        # XP Bar Tweening
        # Skill: 渐变 (Gradient/Tweening)
        # Smoothly interpolate displayed_xp towards target_xp
        self.target_xp = self.player.current_xp
        if self.displayed_xp < self.target_xp:
            # Linear interpolation or simple step
            diff = self.target_xp - self.displayed_xp
            step = max(1, int(diff * 0.1)) # 10% per frame
            self.displayed_xp += step
            if self.displayed_xp > self.target_xp:
                self.displayed_xp = self.target_xp
        elif self.displayed_xp > self.target_xp:
            # Handle level up reset (displayed_xp might be > new target_xp which is low)
            # If level up happened, we should probably reset displayed_xp or animate it filling up then resetting.
            # For simplicity, if displayed > target (likely level up), just set to target for now
            self.displayed_xp = self.target_xp
        
        # Update Auto-pilot Interval (Fixed 0.5s)
        self.auto_pilot_interval = 30
        
        # Auto-pilot logic
        self.auto_pilot_timer += 1
        if self.auto_pilot_timer >= self.auto_pilot_interval:
            self.auto_pilot_timer = 0
            self.auto_pilot_step()
            
        # MP Regeneration (1% per second)
        self.mp_regen_timer += 1
        if self.mp_regen_timer >= 60: # 60 frames = 1 second
            self.mp_regen_timer = 0
            if self.player.mp < self.player.max_mp:
                regen_amount = max(1, int(self.player.max_mp * 0.01))
                self.player.mp = min(self.player.max_mp, self.player.mp + regen_amount)

        # Update Monster Animations
        for m in self.current_map.active_monsters:
            if hasattr(m, 'update_spawn_animation'):
                m.update_spawn_animation()

        # Monster Respawn
        if len(self.current_map.active_monsters) < 5:
            if random.random() < 0.05: # 5% chance per frame to respawn if low count
                self.current_map.spawn_monster()

    def perform_auto_recycle(self):
        if not self.player: return
        
        # Use centralized recycle logic in Player
        results = self.player.recycle_items(self.recycle_qualities)
        count = results["count"]
        
        if count > 0:
            # Log results
            # msg = f"自动回收: {count}件装备" # Simplified log
            # Detailed log if needed, or just summary
            msg = f"自动回收: {count}件 (金币+{results['gold']})"
            if results['ingots'] > 0: msg += f" (元宝+{results['ingots']})"
            
            self.log(msg)
            self.spawn_floating_text(f"自动回收x{count}", self.player.x, self.player.y, GREEN)

    def load_login_config(self):
        # Disable file IO on Web to prevent crash
        if sys.platform == 'emscripten':
            return

        if not os.path.exists("login.json"):
            return
            
        try:
            with open("login.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                
            self.remember_username = data.get("remember_username", False)
            self.remember_password = data.get("remember_password", False)
            
            if self.remember_username:
                self.username_input = data.get("username", "")
                
            if self.remember_password:
                encoded_pw = data.get("password", "")
                if encoded_pw:
                    try:
                        self.password_input = base64.b64decode(encoded_pw.encode()).decode()
                    except:
                        self.password_input = ""
        except Exception as e:
            print(f"Failed to load login config: {e}")

    def save_login_config(self):
        # Disable file IO on Web
        if sys.platform == 'emscripten':
            return

        data = {
            "remember_username": self.remember_username,
            "remember_password": self.remember_password
        }
        
        if self.remember_username:
            data["username"] = self.username_input
        else:
            data["username"] = ""
            
        if self.remember_password:
            encoded_pw = base64.b64encode(self.password_input.encode()).decode()
            data["password"] = encoded_pw
        else:
            data["password"] = ""
            
        try:
            with open("login.json", "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Failed to save login config: {e}")

    def get_save_file_path(self):
        if self.network_manager.is_connected and self.network_manager.username:
            # Use username specific save file
            return f"savegame_{self.network_manager.username}.dat"
        else:
            # Offline save file
            return "savegame.dat"

    def save_game_state(self):
        # Update current character data if playing
        if self.state == "PLAYING" and self.current_char_index != -1:
             # Update Map ID in Player object
             self.player.map_id = getattr(self.current_map, 'map_key', 'NoviceVillage')
             
             char_data = self.characters[self.current_char_index]
             if char_data:
                 char_data["map_name"] = self.current_map.name
                 char_data["quest_manager"] = self.quest_manager
        
        settings = {
            "enabled": self.auto_save_enabled,
            "interval": self.auto_save_interval,
            "skip_recycle_confirmation": self.skip_recycle_confirmation,
            "auto_recycle_enabled": self.auto_recycle_enabled,
            "recycle_qualities": self.recycle_qualities
        }
        
        # Local Save
        local_filename = self.get_save_file_path()
        username = self.network_manager.username if self.network_manager.is_connected else None
        
        local_success = self.save_manager.save_game(self.characters, settings, filename=local_filename, username=username)
        
        # Cloud Save
        cloud_success = False
        if self.network_manager.is_connected:
             save_dict = self.save_manager.get_save_dict(self.characters, settings)
             success, msg = self.network_manager.save_game(save_dict)
             if success:
                 cloud_success = True
                 self.log("云端保存成功。")
             else:
                 self.log(f"云端保存失败: {msg}")
        
        if local_success:
            self.log("游戏已保存 (本地)。")

    def try_attack(self, monster):
        dist = abs(monster.x - self.player.x) + abs(monster.y - self.player.y)
        
        # Check active skill
        skill = self.player.active_skill
        
        # Fallback to melee if MP is low OR skill is on cooldown
        use_melee = False
        
        if skill:
            # Check MP
            if self.player.mp < skill.mp_cost:
                use_melee = True
            
            # Check Cooldown
            current_time = time.time()
            reduction_pct = min(100.0, max(0.0, self.player.cooldown_reduction))
            effective_cd = skill.cooldown * (1.0 - reduction_pct / 100.0)
            if current_time - skill.last_used < effective_cd:
                use_melee = True
        else:
            use_melee = True

        if use_melee:
            # Not enough MP or CD, treat as melee basic attack
            # Range = 1
            if dist <= 1:
                self.combat_round(monster)
                return True
            else:
                return False # Need to move closer

        if skill:
            if dist <= skill.range:
                self.perform_skill_attack(monster, skill)
                return True
        
        return False

    def auto_pilot_step(self):
        # 0. Check locked target validity
        if self.target_monster:
            if self.target_monster not in self.current_map.active_monsters or not self.target_monster.is_alive():
                self.target_monster = None

        # 1. Manual Move Priority
        if self.manual_target_pos:
            tx, ty = self.manual_target_pos
            if self.player.x == tx and self.player.y == ty:
                self.manual_target_pos = None # Reached
                self.log("到达目的地")
            else:
                # Move towards
                dx, dy = 0, 0
                if tx > self.player.x: dx = 1
                elif tx < self.player.x: dx = -1
                
                if ty > self.player.y: dy = 1
                elif ty < self.player.y: dy = -1
                
                # Move
                if dx != 0 and dy != 0:
                     # Diagonal move? Engine supports axis only usually, unless map allows diagonal.
                     # Let's do axis aligned for now to match other logic
                     if random.random() < 0.5: dy = 0
                     else: dx = 0
                     
                self.move_player(dx, dy)
                return # Skip auto-combat if moving manually
        
        # 2. Try to attack locked target or any valid target in range
        if self.target_monster:
             if self.try_attack(self.target_monster):
                 return
        
        # 3. Find nearest monster
        if self.auto_combat_enabled and not self.target_monster:
            min_dist = 9999
            nearest_monster = None
            
            # Find closest monster (First found if distances are equal)
            for m in self.current_map.active_monsters:
                dist = abs(m.x - self.player.x) + abs(m.y - self.player.y)
                if dist < min_dist:
                    min_dist = dist
                    nearest_monster = m
            
            if nearest_monster:
                self.target_monster = nearest_monster
                # Try attack immediately if in range
                if self.try_attack(self.target_monster):
                    return
        
        # 4. Move towards target
        if self.target_monster:
             # Check if we need to move
             # If using melee fallback (CD or low MP), range is 1.
             # If skill available, range is skill.range.
             
             max_range = 1
             skill = self.player.active_skill
             
             use_melee = False
             if skill:
                 # Check MP & CD (Same logic as try_attack)
                 if self.player.mp < skill.mp_cost: use_melee = True
                 
                 current_time = time.time()
                 reduction_pct = min(100.0, max(0.0, self.player.cooldown_reduction))
                 effective_cd = skill.cooldown * (1.0 - reduction_pct / 100.0)
                 if current_time - skill.last_used < effective_cd: use_melee = True
                 
                 if not use_melee:
                     max_range = skill.range
             else:
                 max_range = 1
                
             dist = abs(self.target_monster.x - self.player.x) + abs(self.target_monster.y - self.player.y)
             
             if dist > max_range:
                # Move towards
                dx = 0
                dy = 0
                if self.target_monster.x > self.player.x: dx = 1
                elif self.target_monster.x < self.player.x: dx = -1
                elif self.target_monster.y > self.player.y: dy = 1
                elif self.target_monster.y < self.player.y: dy = -1
                
                self.move_player(dx, dy)
             else:
                # In range but try_attack failed? 
                # Could be because try_attack returned False (out of melee range but we thought we were in skill range?)
                # If we are here, dist <= max_range.
                # If using melee, max_range=1.
                # If try_attack failed, maybe we need to retry or move closer?
                # Actually, if dist <= max_range, try_attack should succeed unless blocked?
                # Just in case, try moving closer if dist > 1
                if dist > 1:
                    # Move closer
                    dx = 0
                    dy = 0
                    if self.target_monster.x > self.player.x: dx = 1
                    elif self.target_monster.x < self.player.x: dx = -1
                    elif self.target_monster.y > self.player.y: dy = 1
                    elif self.target_monster.y < self.player.y: dy = -1
                    self.move_player(dx, dy)

    def move_player(self, dx, dy):
        new_x = self.player.x + dx
        new_y = self.player.y + dy
        
        if not self.current_map.is_valid_move(new_x, new_y):
            # self.log("Blocked.")
            return

        # Check for monster collision (Manual move might trigger this)
        target_monster = None
        for m in self.current_map.active_monsters:
            if m.x == new_x and m.y == new_y:
                target_monster = m
                break
        
        if target_monster:
            self.try_attack(target_monster)
        else:
            self.player.x = new_x
            self.player.y = new_y
            self.check_treasure_event(new_x, new_y)

    def handle_monster_death(self, monster):
        self.log(f"击败了 {monster.name}! +{monster.xp_reward} 经验")
        self.player.gain_xp(monster.xp_reward)
        if monster in self.current_map.active_monsters:
            self.current_map.active_monsters.remove(monster)
        
        # Update Treasure Pity Counter
        self.kill_count += 1
        
        # Check Treasure Spawn (1% ~ 5% chance OR Pity >= 100)
        # Using 3% chance
        triggered_treasure = False
        if self.kill_count >= 100:
            triggered_treasure = True
            # self.log("宝藏保底触发！")
        elif random.randint(1, 100) <= 3: # 3% chance
            triggered_treasure = True
            # self.log("运气爆棚，宝藏现世！")
            
        if triggered_treasure:
            self.spawn_treasure_event()
            self.kill_count = 0 # Reset counter
        
        # Loot Drop Logic - Modified for Ground Items
        if random.random() < 0.8: # High drop rate for demo
            # Gold Drop
            gold_amount = random.randint(10, 50)
            self.spawn_loot_animation(monster.x, monster.y, "gold", amount=gold_amount)
            # self.log("获得金币!") # Log when collected
            
            # Ingot Drop (1% chance)
            if random.random() < 0.01:
                self.spawn_loot_animation(monster.x, monster.y, "ingot", amount=1)
            
            # Equipment Drop (20% chance)
            if random.random() < 0.2:
                # Determine drop parameters
                drops_list = getattr(monster, 'drops', [])
                
                # Get Map Limits
                map_key = getattr(self.current_map, 'map_key', None)
                map_max_level = 100
                # map_min_level = 1
                
                if map_key and map_key in MAPS_DB:
                    map_max_level = MAPS_DB[map_key].get("max_level", 100)
                
                if drops_list:
                    # Use specific drop table
                    drop = Equipment.create_random_drop(allowed_items=drops_list)
                else:
                    # Use map level limits
                    drop = Equipment.create_random_drop(min_level=1, max_level=map_max_level)
                    
                if drop:
                    self.spawn_loot_animation(monster.x, monster.y, "item", item_data=drop)
            
            # Bone Powder Drop (10% chance, 1-3 count)
            if random.random() < 0.1:
                from src.systems.equipment.item import BonePowder
                count = random.randint(1, 3)
                bp = BonePowder()
                bp.count = count
                self.spawn_loot_animation(monster.x, monster.y, "bone_powder", item_data=bp, amount=count)
        
        # Quest Update Kill
        if self.quest_manager.update_kill(monster.name):
            self.log("任务进度更新！")
            self.update_npc_status()
            
        # Special Boss Logic
        if monster.name == "蛇妖王":
            self.quest_manager.accept_quest("q5")
            self.npc_manager.get_npc("世外高人").has_quest_available = True
            self.log("世外高人出现在村子里了！")

    def perform_skill_attack(self, monster, skill):
        # Check Cooldown
        current_time = time.time()
        # Effective Cooldown
        reduction_pct = min(100.0, max(0.0, self.player.cooldown_reduction))
        effective_cd = skill.cooldown * (1.0 - reduction_pct / 100.0)
        
        if current_time - skill.last_used < effective_cd:
            # On Cooldown
            # Log? Or just fail silently? Or use basic attack?
            # User said "Use frequency depends on use time".
            # For auto-pilot, if we are here, we are trying to use this skill.
            # If on CD, we should probably return False so auto-pilot can decide what to do (e.g. wait or use other skill).
            # But this function returns None.
            # Let's log it for now or show text.
            # self.log(f"{skill.name} 冷却中...")
            return

        # Check MP
        if self.player.mp < skill.mp_cost:
            self.log("MP不足！")
            self.spawn_floating_text("MP不足", self.player.x, self.player.y, BLUE)
            return

        self.player.mp -= skill.mp_cost
        skill.last_used = current_time # Update usage time
        
        # Calculate Damage
        damage = int(max(1, (self.player.attack * skill.damage_multiplier) - monster.defense))
        monster.take_damage(damage)
        
        # Log
        self.log(f"使用了 {skill.name} 攻击 {monster.name}，伤害 {damage}")
        self.spawn_floating_text(f"-{damage}", monster.x, monster.y, RED)
        
        # Animation
        if skill.icon:
             # Convert grid to screen coords
             # Monster tile: (monster.x, monster.y)
             # Effect needs to cover monster and 1 tile above (monster.y - 1)
             # So top-left of effect is (monster.x, monster.y - 1)
             
             off_x = getattr(self, 'map_offset_x', 50)
             off_y = getattr(self, 'map_offset_y', 50)
             
             screen_x = off_x + monster.x * (self.renderer.tile_size + self.renderer.margin)
             screen_y = off_y + (monster.y - 1) * (self.renderer.tile_size + self.renderer.margin)
             
             # Width = 1 tile, Height = 2 tiles
             # We should use actual pixel sizes for better scaling
             target_w = self.renderer.tile_size
             target_h = self.renderer.tile_size * 2 + self.renderer.margin
             
             # Pass size for scaling
             self.skill_animations.append(SkillAnimation(screen_x, screen_y, skill.icon, target_w, target_h))

        if not monster.is_alive():
             self.handle_monster_death(monster)

    def combat_round(self, monster):
        # Player hits monster
        damage = max(1, self.player.attack - monster.defense)
        monster.take_damage(damage)
        self.spawn_floating_text(f"-{damage}", monster.x, monster.y, RED)
        self.log(f"你攻击了 {monster.name} 造成 {damage} 点伤害。")
        
        if not monster.is_alive():
            self.handle_monster_death(monster)
            return

        # Monster hits player
        m_damage = max(1, monster.attack - self.player.defense)
        self.player.hp -= m_damage
        self.spawn_floating_text(f"-{m_damage}", self.player.x, self.player.y, RED)
        # self.log(f"{monster.name} hits you for {m_damage} dmg.")
        
        if self.player.hp <= 0:
            self.log("你挂了! 游戏结束。")
            self.player.hp = self.player.max_hp
            self.player.x = 0
            self.player.y = 0
            self.log("原地复活。")

    def update_login(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.VIDEORESIZE:
                self.update_scaling()
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    self.active_input = (self.active_input + 1) % 2
                    
                elif event.key == pygame.K_RETURN:
                    # Login/Register Logic
                    if not self.username_input or not self.password_input:
                        self.login_message = "账号密码不能为空"
                        self.login_msg_color = RED
                        return
                    
                    if len(self.username_input) < 6 or len(self.password_input) < 4:
                        self.login_message = "账号最少6位，密码最少4位"
                        self.login_msg_color = RED
                        return
                        
                    # Try Login First
                    success, msg = self.network_manager.login(self.username_input, self.password_input)
                    if success:
                        self.login_message = "登录成功！"
                        self.login_msg_color = GREEN
                        self.save_login_config()
                        # Proceed to game
                        self.load_game_data()
                    else:
                        if "Invalid credentials" in msg:
                             self.login_message = "账号或密码错误"
                             self.login_msg_color = RED
                        else:
                             self.login_message = f"登录失败: {msg}"
                             self.login_msg_color = RED

                elif event.key == pygame.K_BACKSPACE:
                    if self.active_input == 0:
                        self.username_input = self.username_input[:-1]
                    else:
                        self.password_input = self.password_input[:-1]
                else:
                    # Typing
                    if self.active_input == 0:
                        if len(self.username_input) < 12:
                            self.username_input += event.unicode
                    else:
                        if len(self.password_input) < 16:
                            self.password_input += event.unicode

            if event.type == pygame.MOUSEBUTTONDOWN:
                real_mx, real_my = pygame.mouse.get_pos()
                mx, my = self.transform_input((real_mx, real_my))
                
                cx, cy = self.width // 2, self.height // 2
                
                # Check Input Focus
                u_rect = pygame.Rect(cx - 100, cy - 45, 200, 30)
                p_rect = pygame.Rect(cx - 100, cy + 5, 200, 30)
                
                if u_rect.collidepoint(mx, my):
                    self.active_input = 0
                elif p_rect.collidepoint(mx, my):
                    self.active_input = 1

                # Check Remember Checkboxes
                rem_user_rect = pygame.Rect(cx - 100, cy + 45, 100, 20)
                rem_pass_rect = pygame.Rect(cx + 20, cy + 45, 100, 20)
                
                if rem_user_rect.collidepoint(mx, my):
                    self.remember_username = not self.remember_username
                elif rem_pass_rect.collidepoint(mx, my):
                    self.remember_password = not self.remember_password

                # Check buttons
                # Login Button
                login_rect = pygame.Rect(self.width//2 - 100, self.height//2 + 80, 80, 30)
                if login_rect.collidepoint(mx, my):
                     if self.username_input and self.password_input:
                         if len(self.username_input) < 6 or len(self.password_input) < 4:
                             self.login_message = "账号最少6位，密码最少4位"
                             self.login_msg_color = RED
                         else:
                             success, msg = self.network_manager.login(self.username_input, self.password_input)
                             if success:
                                 self.save_login_config()
                                 self.load_game_data()
                             else:
                                 self.login_message = msg
                                 self.login_msg_color = RED

                # Register Button
                reg_rect = pygame.Rect(self.width//2 + 20, self.height//2 + 80, 80, 30)
                if reg_rect.collidepoint(mx, my):
                     if self.username_input and self.password_input:
                         if len(self.username_input) < 6 or len(self.password_input) < 4:
                             self.login_message = "账号最少6位，密码最少4位"
                             self.login_msg_color = RED
                         else:
                             success, msg = self.network_manager.register(self.username_input, self.password_input)
                             if success:
                                 self.save_login_config()
                                 self.login_message = "注册成功，请登录"
                                 self.login_msg_color = GREEN
                             else:
                                 self.login_message = msg
                                 self.login_msg_color = RED

                # Offline Button
                off_rect = pygame.Rect(self.width//2 - 40, self.height//2 + 130, 80, 30)
                if off_rect.collidepoint(mx, my):
                     self.load_game_data() # Will load local

    def draw_login(self):
        self.canvas.fill(WHITE)
        
        # Cursor Blink Logic
        current_time = time.time()
        if current_time - self.cursor_timer > 0.5:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = current_time
        
        cx, cy = self.width // 2, self.height // 2
        
        # Title
        title = self.renderer.cn_font.render("挂机成神 - 登录", True, BLACK)
        t_rect = title.get_rect(center=(cx, cy - 100))
        self.canvas.blit(title, t_rect)
        
        # Inputs
        # Username
        u_label = self.renderer.cn_font.render("账号:", True, BLACK)
        self.canvas.blit(u_label, (cx - 150, cy - 40))
        
        u_rect = pygame.Rect(cx - 100, cy - 45, 200, 30)
        color = BLUE if self.active_input == 0 else GRAY
        pygame.draw.rect(self.canvas, WHITE, u_rect)
        pygame.draw.rect(self.canvas, color, u_rect, 2)
        
        if self.username_input:
            u_txt = self.renderer.cn_font.render(self.username_input, True, BLACK)
            u_txt_rect = u_txt.get_rect(midleft=(u_rect.x + 5, u_rect.centery))
            self.canvas.blit(u_txt, u_txt_rect)
        else:
            # Placeholder
            ph_txt = self.renderer.small_font.render("输入由字母或数字组成的账号", True, (180, 180, 180))
            ph_rect = ph_txt.get_rect(midleft=(u_rect.x + 5, u_rect.centery))
            self.canvas.blit(ph_txt, ph_rect)
            
        # Cursor for Username
        if self.active_input == 0 and self.cursor_visible:
            if self.username_input:
                txt_w = self.renderer.cn_font.render(self.username_input, True, BLACK).get_width()
            else:
                txt_w = 0
            
            cursor_x = u_rect.x + 5 + txt_w
            # Ensure cursor doesn't go out of bounds? 
            # Simple line
            pygame.draw.line(self.canvas, BLACK, (cursor_x, u_rect.y + 5), (cursor_x, u_rect.bottom - 5), 2)
        
        # Password
        p_label = self.renderer.cn_font.render("密码:", True, BLACK)
        self.canvas.blit(p_label, (cx - 150, cy + 10))
        
        p_rect = pygame.Rect(cx - 100, cy + 5, 200, 30)
        color = BLUE if self.active_input == 1 else GRAY
        pygame.draw.rect(self.canvas, WHITE, p_rect)
        pygame.draw.rect(self.canvas, color, p_rect, 2)
        
        if self.password_input:
            # Mask password
            p_masked = "*" * len(self.password_input)
            p_txt = self.renderer.cn_font.render(p_masked, True, BLACK)
            p_txt_rect = p_txt.get_rect(midleft=(p_rect.x + 5, p_rect.centery))
            self.canvas.blit(p_txt, p_txt_rect)
        else:
             # Placeholder for password (Optional but good UX)
             ph_txt = self.renderer.small_font.render("请输入密码", True, (180, 180, 180))
             ph_rect = ph_txt.get_rect(midleft=(p_rect.x + 5, p_rect.centery))
             self.canvas.blit(ph_txt, ph_rect)

        # Cursor for Password
        if self.active_input == 1 and self.cursor_visible:
            if self.password_input:
                p_masked = "*" * len(self.password_input)
                txt_w = self.renderer.cn_font.render(p_masked, True, BLACK).get_width()
            else:
                txt_w = 0
            
            cursor_x = p_rect.x + 5 + txt_w
            pygame.draw.line(self.canvas, BLACK, (cursor_x, p_rect.y + 5), (cursor_x, p_rect.bottom - 5), 2)
        
        # Remember Checkboxes
        # User Checkbox
        rem_user_rect = pygame.Rect(cx - 100, cy + 45, 15, 15)
        pygame.draw.rect(self.canvas, BLACK, rem_user_rect, 1)
        if self.remember_username:
            pygame.draw.rect(self.canvas, BLACK, rem_user_rect.inflate(-4, -4))
            
        rem_user_txt = self.renderer.small_font.render("记住账号", True, BLACK)
        self.canvas.blit(rem_user_txt, (rem_user_rect.right + 5, rem_user_rect.y + 2))
        
        # Password Checkbox
        rem_pass_rect = pygame.Rect(cx + 20, cy + 45, 15, 15)
        pygame.draw.rect(self.canvas, BLACK, rem_pass_rect, 1)
        if self.remember_password:
            pygame.draw.rect(self.canvas, BLACK, rem_pass_rect.inflate(-4, -4))
            
        rem_pass_txt = self.renderer.small_font.render("记住密码", True, BLACK)
        self.canvas.blit(rem_pass_txt, (rem_pass_rect.right + 5, rem_pass_rect.y + 2))

        # Warning for Remember Password
        if self.remember_password:
            warn_msg = "非常用设备不建议勾选此项"
            # Simulate bold by rendering twice with offset
            warn_surf = self.renderer.small_font.render(warn_msg, True, (255, 0, 0))
            
            # Position to the right of "记住密码" text
            # rem_pass_rect.right + 5 (spacing) + text_width + 10 (spacing)
            warn_x = rem_pass_rect.right + 5 + rem_pass_txt.get_width() + 10
            warn_y = rem_pass_rect.y + 2
            
            self.canvas.blit(warn_surf, (warn_x, warn_y))
            self.canvas.blit(warn_surf, (warn_x + 1, warn_y)) # Bold effect

        # Buttons
        # Login
        l_rect = pygame.Rect(cx - 100, cy + 80, 80, 30)
        pygame.draw.rect(self.canvas, GREEN, l_rect, border_radius=5)
        l_txt = self.renderer.cn_font.render("登录", True, WHITE)
        l_rect_t = l_txt.get_rect(center=l_rect.center)
        self.canvas.blit(l_txt, l_rect_t)
        
        # Register
        r_rect = pygame.Rect(cx + 20, cy + 80, 80, 30)
        pygame.draw.rect(self.canvas, BLUE, r_rect, border_radius=5)
        r_txt = self.renderer.cn_font.render("注册", True, WHITE)
        r_rect_t = r_txt.get_rect(center=r_rect.center)
        self.canvas.blit(r_txt, r_rect_t)
        
        # Offline
        o_rect = pygame.Rect(cx - 40, cy + 130, 80, 30)
        pygame.draw.rect(self.canvas, GRAY, o_rect, border_radius=5)
        o_txt = self.renderer.cn_font.render("离线游玩", True, WHITE)
        o_rect_t = o_txt.get_rect(center=o_rect.center)
        self.canvas.blit(o_txt, o_rect_t)
        
        # Message
        msg = self.renderer.cn_font.render(self.login_message, True, self.login_msg_color)
        msg_rect = msg.get_rect(center=(cx, cy + 180))
        self.canvas.blit(msg, msg_rect)

    def draw_ui(self):
        # Draw Layout Borders (Thick Lines)
        # Vertical Line separating Left (Map/Inter) and Right (Info/Func)
        pygame.draw.line(self.canvas, BLACK, (800, 0), (800, 768), 4)
        # Horizontal Line separating Top (Map/Info) and Bottom (Inter/Func)
        pygame.draw.line(self.canvas, BLACK, (0, 600), (1024, 600), 4)
        
        # --- Info Panel (Top Right) ---
        info_rect = self.layout["info"]
        
        # 1. Log (Top) - REMOVED per user request
        # log_h = 200
        # ...
        
        # 2. Quest Tracker (Moved to Top)
        # Use top area for quests
        quest_h = 160 # Increased slightly from 140
        quest_rect = pygame.Rect(info_rect.x, info_rect.y + 10, info_rect.width, quest_h)
        self.renderer.draw_quest_tracker(quest_rect, self.quest_manager.active_quests)
        
        # Separator Quest/Stats
        stats_y = info_rect.y + quest_h + 20
        pygame.draw.line(self.canvas, BLACK, (info_rect.x, stats_y), (info_rect.right, stats_y), 2)
        
        # 3. Stats Matrix (Below Quest)
        # Use normal font for matrix layout
        col1_x = info_rect.x + 10
        col2_x = info_rect.x + 115
        current_y = stats_y + 10
        line_height = 30 # Increased from 20
        
        # Row 1: Name / Prof
        self.canvas.blit(self.renderer.cn_font.render(f"姓名: {self.player.name}", True, BLUE), (col1_x, current_y))
        self.canvas.blit(self.renderer.cn_font.render(f"职业: {self.player.profession.value}", True, BLUE), (col2_x, current_y))
        current_y += line_height

        # Row 2: Level
        self.canvas.blit(self.renderer.cn_font.render(f"等级: {self.player.level}", True, BLUE), (col1_x, current_y))
        current_y += line_height
        
        # Row 3: HP (Full Row)
        self.canvas.blit(self.renderer.cn_font.render(f"生命: {int(self.player.hp)}/{int(self.player.max_hp)}", True, RED), (col1_x, current_y))
        current_y += line_height
        
        # Row 4: MP (Full Row)
        self.canvas.blit(self.renderer.cn_font.render(f"魔法: {int(self.player.mp)}/{int(self.player.max_mp)}", True, BLUE), (col1_x, current_y))
        current_y += line_height
        
        # Row 5: Atk / Def
        self.canvas.blit(self.renderer.cn_font.render(f"攻击: {self.player.attack}", True, BLACK), (col1_x, current_y))
        self.canvas.blit(self.renderer.cn_font.render(f"防御: {self.player.defense}", True, BLACK), (col2_x, current_y))
        current_y += line_height
        
        # Row 6: Magic / M.Def
        self.canvas.blit(self.renderer.cn_font.render(f"魔法: {self.player.magic}", True, BLACK), (col1_x, current_y))
        self.canvas.blit(self.renderer.cn_font.render(f"魔防: {self.player.magic_defense}", True, BLACK), (col2_x, current_y))
        current_y += line_height
        
        # Row 7: Taoism / Luck
        self.canvas.blit(self.renderer.cn_font.render(f"道术: {self.player.taoism}", True, BLACK), (col1_x, current_y))
        self.canvas.blit(self.renderer.cn_font.render(f"幸运: {getattr(self.player, 'luck', 0)}", True, BLACK), (col2_x, current_y))
        current_y += line_height
        
        # Row 8: Speed / CD
        self.canvas.blit(self.renderer.cn_font.render(f"攻速: {getattr(self.player, 'attack_speed', 0)}", True, BLACK), (col1_x, current_y))
        self.canvas.blit(self.renderer.cn_font.render(f"冷缩: {getattr(self.player, 'cooldown_reduction', 0)}%", True, BLACK), (col2_x, current_y))
        current_y += line_height

        # Row 9: Acc / Dodge
        self.canvas.blit(self.renderer.cn_font.render(f"准确: {getattr(self.player, 'accuracy', 0)}", True, BLACK), (col1_x, current_y))
        self.canvas.blit(self.renderer.cn_font.render(f"敏捷: {getattr(self.player, 'dodge', 0)}", True, BLACK), (col2_x, current_y))
        current_y += line_height

        # Row 10: Full Body Enhancement
        # Calculate full body enhancement level
        min_enh_level = 999
        min_slots = []
        equipped_count = 0
        
        check_slots = [
            "weapon", "armor", "helmet", "necklace", 
            "bracelet_l", "bracelet_r", "ring_l", "ring_r",
            "belt", "boots", "medal"
        ]
        
        slot_names = {
            "weapon": "武器", "armor": "衣服", "helmet": "头盔", "necklace": "项链",
            "bracelet_l": "左手镯", "bracelet_r": "右手镯", "ring_l": "左戒指", "ring_r": "右戒指",
            "belt": "腰带", "boots": "靴子", "medal": "勋章"
        }
        
        for s in check_slots:
            if self.player.equipment.get(s):
                equipped_count += 1
                lvl = getattr(self.player.equipment[s], 'enhancement_level', 0)
                if lvl < min_enh_level:
                    min_enh_level = lvl
                    min_slots = [s]
                elif lvl == min_enh_level:
                    min_slots.append(s)
            else:
                min_enh_level = 0
                min_slots.append(s)
        
        # If not fully equipped, level is 0
        if equipped_count < len(check_slots):
            min_enh_level = 0
            
        # Display Text
        fb_text = f"全身强化: +{min_enh_level}"
        self.canvas.blit(self.renderer.cn_font.render(fb_text, True, BLACK), (col1_x, current_y))
        current_y += line_height
        
        # Display Lowest Level Slot
        import random
        if min_slots:
            # Pick one random slot from the lowest level slots
            target_slot = random.choice(min_slots)
            slot_name = slot_names.get(target_slot, target_slot)
            
            min_text = f"最低部位: {slot_name}"
            self.canvas.blit(self.renderer.cn_font.render(min_text, True, BLACK), (col1_x, current_y))
            current_y += line_height
            
        # XP Bar (Bottom of Info Panel)
        needed_xp = max(1, self.player.xp_system.get_xp_for_next_level(self.player.level))
        xp_ratio = min(1.0, self.displayed_xp / needed_xp)
        
        bar_h = 15
        bar_y = info_rect.bottom - bar_h - 5
        bar_w = info_rect.width - 20
        bar_x = info_rect.x + 10
        
        pygame.draw.rect(self.canvas, (200, 200, 200), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(self.canvas, (50, 200, 50), (bar_x, bar_y, int(bar_w * xp_ratio), bar_h))
        pygame.draw.rect(self.canvas, BLACK, (bar_x, bar_y, bar_w, bar_h), 1)
        
        # XP Text on Bar
        xp_text = f"{int(self.player.current_xp)}/{needed_xp}"
        xp_surf = self.renderer.small_font.render(xp_text, True, (0, 0, 0))
        xp_rect = xp_surf.get_rect(center=(bar_x + bar_w/2, bar_y + bar_h/2))
        self.canvas.blit(xp_surf, xp_rect)

        # --- Interaction Panel (Bottom Left) ---
        inter_rect = self.layout["interaction"]
        
        # NPCs (Top part of Interaction)
        npc_area = pygame.Rect(inter_rect.x, inter_rect.y, inter_rect.width, 84)
        self.npc_rects = self.renderer.draw_npc_bar(npc_area, list(self.npc_manager.npcs.values()))
        
        # Buttons (Bottom part of Interaction)
        btn_area = pygame.Rect(inter_rect.x, inter_rect.y + 84, inter_rect.width, inter_rect.height - 84)
        self.button_rects = self.renderer.draw_ui_buttons(btn_area)
        
        # --- Function Panel (Bottom Right) ---
        func_rect = self.layout["function"]
        
        # Treasure Pity
        remaining = max(0, 100 - self.kill_count)
        pity_text = f"距离发现宝藏还需击杀：{remaining}只怪物"
        txt_surf = self.renderer.cn_font.render(pity_text, True, (255, 100, 0))
        self.canvas.blit(txt_surf, (func_rect.x + 10, func_rect.y + 20))
        
        # Control Buttons
        # Vertical Layout
        btn_w_large = 200
        btn_w_small = 95
        btn_h = 40
        start_y = func_rect.y + 60
        spacing = 10
        
        # Auto Combat
        self.auto_combat_btn_rect = pygame.Rect(func_rect.x + 12, start_y, btn_w_large, btn_h)
        btn_color = (100, 200, 100) if not self.auto_combat_enabled else (200, 100, 100)
        btn_text = "自动战斗" if not self.auto_combat_enabled else "停止挂机"
        self.draw_button(self.auto_combat_btn_rect, btn_text, btn_color)
        
        # Save
        self.save_btn_rect = pygame.Rect(func_rect.x + 12, start_y + btn_h + spacing, btn_w_small, btn_h)
        self.draw_button(self.save_btn_rect, "存档", (100, 200, 100))
        
        # Exit
        self.logout_btn_rect = pygame.Rect(func_rect.x + 12 + btn_w_small + spacing, start_y + btn_h + spacing, btn_w_small, btn_h)
        self.draw_button(self.logout_btn_rect, "退出", (200, 100, 100))

    def draw_button(self, rect, text, color):
        pygame.draw.rect(self.canvas, color, rect, border_radius=5)
        pygame.draw.rect(self.canvas, BLACK, rect, width=2, border_radius=5)
        txt = self.renderer.cn_font.render(text, True, BLACK)
        txt_rect = txt.get_rect(center=rect.center)
        self.canvas.blit(txt, txt_rect)

    async def run(self):
        print("[DEBUG] Engine Run Loop Started")
        
        # Initial check
        print("[DEBUG] Checking font initialization...")
        if self.font:
             print("[DEBUG] Font is ready")
        else:
             print("[DEBUG] Font is missing")

        while True:
            # Handle Resize Event
            # If Android, resolution might change on rotation (if allowed)
            
            # Critical for Web: Yield to browser event loop
            await asyncio.sleep(0)
            
            try:
                if self.state == "LOGIN":
                    self.update_login()
                    self.draw_login()
            
                elif self.state == "CHARACTER_SELECT":
                    self.update_character_select()
                    self.draw_character_select()
                
                elif self.state == "CREATE_CHARACTER":
                    self.update_create_character()
                    self.draw_create_character()
                
                else:
                    self.handle_input()
                    self.update_logic()
                    
                    # Draw to Canvas (Logic remains same, drawing to self.canvas via renderer)
                    self.canvas.fill(WHITE)
                    
                    # Draw Map and Entities
                    self.renderer.draw_map(self.current_map, self.map_offset_x, self.map_offset_y)
                
                    # Draw Monsters
                    for monster in self.current_map.active_monsters:
                        self.renderer.draw_entity(monster, RED, self.map_offset_x, self.map_offset_y)
                    
                    # Draw Player
                    self.renderer.draw_entity(self.player, BLUE, self.map_offset_x, self.map_offset_y)
                
                    # Draw Visual Effects
                    for anim in self.loot_animations:
                        self.renderer.draw_loot_animation(anim)
                    
                    for anim in self.skill_animations:
                        if anim.frames and anim.current_frame < len(anim.frames):
                            self.canvas.blit(anim.frames[anim.current_frame], (anim.x, anim.y))
                    
                    for ft in self.floating_texts:
                        self.renderer.draw_floating_text(ft)
                
                    # Draw UI
                    self.draw_ui()
                
                    # Draw Windows (Top layer)
                    for win in self.windows.values():
                        win.draw(self.canvas)
                    
                    # Draw UI Floating Texts (Topmost)
                    for ft in self.ui_floating_texts:
                        self.renderer.draw_floating_text(ft)
            
            except Exception as e:
                print(f"[ERROR] Exception in game loop: {e}")
                import traceback
                traceback.print_exc()

            # Final Scaling and Blit to Screen
            # Always scale canvas to screen to support mobile/web responsive layout
            
            # Clear black bars
            self.screen.fill(BLACK)
            
            # Scale canvas
            if self.scale_ratio != 1.0:
                final_w = int(self.design_width * self.scale_ratio)
                final_h = int(self.design_height * self.scale_ratio)
                scaled_surface = pygame.transform.smoothscale(self.canvas, (final_w, final_h))
                self.screen.blit(scaled_surface, (self.offset_x, self.offset_y))
            else:
                self.screen.blit(self.canvas, (self.offset_x, self.offset_y))
            
            pygame.display.flip()
            self.clock.tick(60)
            # await asyncio.sleep(0) # Moved to top of loop
