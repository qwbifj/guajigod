import pygame
import math
import os
import time
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if getattr(sys, 'frozen', False):
        # Running as compiled exe (onedir)
        base_path = os.path.dirname(sys.executable)
    else:
        # Running from source
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class Renderer:
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        # Try to load a Chinese font
        # Check local asset first, then system
        local_font = resource_path("simhei.ttf")
        sys_font_path = "C:\\Windows\\Fonts\\simhei.ttf"
        
        self.cn_font = None
        self.small_font = None
        
        if os.path.exists(local_font):
             try:
                self.cn_font = pygame.font.Font(local_font, 14)
                self.small_font = pygame.font.Font(local_font, 12)
             except: pass
        
        if self.cn_font is None and os.path.exists(sys_font_path):
            try:
                self.cn_font = pygame.font.Font(sys_font_path, 14)
                self.small_font = pygame.font.Font(sys_font_path, 12)
            except:
                pass
        
        if self.cn_font is None:
            try:
                self.cn_font = pygame.font.SysFont("simhei", 14)
                self.small_font = pygame.font.SysFont("simhei", 12)
            except:
                self.cn_font = font
                self.small_font = font
            
        self.tile_size = 40
        self.margin = 0
        
        self.quality_animations = {}
        self.load_quality_animations()

    def load_quality_animations(self):
        # Qualities with folders
        qualities = ["极品", "传说", "史诗", "神话"]
        base_path = resource_path("pic")
        
        for q in qualities:
            path = os.path.join(base_path, q)
            if not os.path.exists(path):
                continue
                
            frames = []
            # Try loading 1.PNG, 2.PNG ...
            i = 1
            while True:
                img_path = os.path.join(path, f"{i}.PNG")
                if not os.path.exists(img_path):
                    # Try lowercase png
                    img_path = os.path.join(path, f"{i}.png")
                    if not os.path.exists(img_path):
                        break
                
                try:
                    img = pygame.image.load(img_path)
                    # Use original size (no scaling)
                    # img = pygame.transform.scale(img, (self.tile_size, self.tile_size))
                    frames.append(img)
                except:
                    print(f"Failed to load {img_path}")
                
                i += 1
            
            if frames:
                self.quality_animations[q] = frames
                print(f"Loaded {len(frames)} frames for {q}")

    def get_quality_color(self, quality_name):
        if quality_name == "普通": return (255, 255, 255) # White
        if quality_name == "优良": return (144, 238, 144) # Light Green
        if quality_name == "精品": return (65, 105, 225)  # Royal Blue
        if quality_name == "极品": return (148, 0, 211)   # Dark Violet
        if quality_name == "传说": return (255, 140, 0)   # Dark Orange
        if quality_name == "史诗": return (220, 20, 60)   # Crimson
        if quality_name == "神话": return (255, 215, 0)   # Gold (Rainbow placeholder)
        return (255, 255, 255)

    def draw_item_slot(self, x, y, size, item=None, label=None, locked=False):
        rect = pygame.Rect(x, y, size, size)
        
        # Background
        if locked:
            bg_color = (255, 255, 255) # White background for locked
            border_color = (0, 0, 0)   # Black border for locked
        else:
            bg_color = (0, 0, 0)       # Black background for unlocked
            border_color = (255, 255, 255) # White border for unlocked
            
        pygame.draw.rect(self.screen, bg_color, rect, border_radius=4)
        
        has_animation = False
        anim_frames = []
        
        if item:
            # Check for animation
            if item.quality.value in self.quality_animations:
                has_animation = True
                anim_frames = self.quality_animations[item.quality.value]
            else:
                # Fallback to static color but without glow
                # Or if user wants to "cancel original effect", maybe keep it white?
                # I'll keep the color for info but remove the glow code.
                border_color = self.get_quality_color(item.quality.value)

        # Draw Border or Animation
        if has_animation and anim_frames:
            # Calculate frame index
            # Speed: 10 FPS
            frame_idx = int(time.time() * 10) % len(anim_frames)
            frame = anim_frames[frame_idx]
            
            # Center the frame over the slot
            frame_rect = frame.get_rect(center=rect.center)
            self.screen.blit(frame, frame_rect)
        else:
            # Standard border
            pygame.draw.rect(self.screen, border_color, rect, width=2, border_radius=4)
        
        # Draw Content
        if item:
            # If animated, maybe we don't need text color to match quality? 
            # But text is useful.
            text_color = self.get_quality_color(item.quality.value)
            
            label = item.name
            # Auto-split for long names (copying from draw_entity logic)
            if len(label) > 3:
                mid = math.ceil(len(label) / 2)
                label = label[:mid] + "\n" + label[mid:]
            
            # Handle multi-line rendering
            lines = label.split('\n')
            surfaces = []
            max_line_w = 0
            total_h = 0
            
            for line in lines:
                s = self.small_font.render(line, True, text_color)
                surfaces.append(s)
                max_line_w = max(max_line_w, s.get_width())
                total_h += s.get_height()
                
            # Calculate constraints
            max_w = max(1, size - 4)
            max_h = max(1, size - 4) 
            
            scale = 1.0
            if max_line_w > max_w or total_h > max_h:
                scale = min(max_w / max_line_w, max_h / total_h)
                
            # Draw
            current_y = rect.centery - (total_h * scale) / 2
            
            for s in surfaces:
                new_w = max(1, int(s.get_width() * scale))
                new_h = max(1, int(s.get_height() * scale))
                
                if scale != 1.0:
                    s = pygame.transform.scale(s, (new_w, new_h))
                    
                s_rect = s.get_rect(centerx=rect.centerx, top=current_y)
                self.screen.blit(s, s_rect)
                current_y += new_h
            
            # Draw Count if > 1
            if hasattr(item, 'count') and item.count > 1:
                count_str = str(item.count)
                # Use a slightly smaller font if possible, or just small_font
                # If count is large (e.g. 99999), scale it down if needed
                count_surf = self.small_font.render(count_str, True, (255, 255, 255))
                
                # Check width
                if count_surf.get_width() > size - 4:
                    scale = (size - 4) / count_surf.get_width()
                    new_size = (int(count_surf.get_width() * scale), int(count_surf.get_height() * scale))
                    count_surf = pygame.transform.scale(count_surf, new_size)
                
                # Draw shadow
                shadow_surf = self.small_font.render(count_str, True, (0, 0, 0))
                if count_surf.get_width() != shadow_surf.get_width():
                     shadow_surf = pygame.transform.scale(shadow_surf, count_surf.get_size())
                     
                count_rect = count_surf.get_rect(bottomright=(rect.right - 2, rect.bottom - 2))
                self.screen.blit(shadow_surf, (count_rect.x + 1, count_rect.y + 1))
                self.screen.blit(count_surf, count_rect)

            # Draw Lock Icon if locked
            if getattr(item, 'locked', False):
                lock_str = "锁"
                lock_surf = self.small_font.render(lock_str, True, (255, 0, 0)) # Red lock
                # Draw shadow
                lock_shadow = self.small_font.render(lock_str, True, (0, 0, 0))
                
                # Position: Bottom Right (if count exists, maybe shift or overlay?)
                # User requirement: "icon's bottom right adds a Lock character"
                # If count exists (stackable items), it might overlap.
                # Let's check if count > 1.
                
                if hasattr(item, 'count') and item.count > 1:
                    # Stackable item with count.
                    # Put Lock to the left of count? Or Top Right?
                    # User said "bottom right".
                    # Let's put it at Top Right to avoid overlap with count, OR overlay it.
                    # Or maybe put it at Bottom Left?
                    # Let's try Bottom Right but slightly offset if count exists?
                    # Actually, for Equipment (which is main use case for Lock), count is usually 1 (not drawn).
                    # So Bottom Right is fine for Equipment.
                    # For stackable items, maybe we just draw it over count or next to it.
                    # Let's draw it at Bottom Right. If count exists, it might be messy.
                    # Let's prioritize Lock visibility.
                    pass
                
                # Draw at Bottom Right
                lock_rect = lock_surf.get_rect(bottomright=(rect.right - 2, rect.bottom - 2))
                # If count exists, move lock up? Or left?
                if hasattr(item, 'count') and item.count > 1:
                    # Move to Top Right for stackable items to avoid mess?
                    # Or just left of count.
                    # Let's try Top Right for better visibility on stackables if any.
                    # But requirement says "bottom right".
                    # Let's stick to bottom right. If count is there, it will overlap.
                    # Let's shift count to the left if locked?
                    # No, let's just draw lock.
                    pass

                self.screen.blit(lock_shadow, (lock_rect.x + 1, lock_rect.y + 1))
                self.screen.blit(lock_surf, lock_rect)

        elif label:
            # Draw slot label (e.g. "头盔")
            # For locked slots, we don't show "锁" anymore as per new requirement, 
            # unless label is something else. But caller passes "锁".
            # Requirement: "未解锁的背包格子中不再显示“锁”字"
            if label == "锁":
                pass # Don't draw text
            else:
                txt = self.small_font.render(label, True, (150, 150, 150))
                txt_rect = txt.get_rect(center=rect.center)
                self.screen.blit(txt, txt_rect)

    def draw_rounded_rect_with_text(self, x, y, text, color, bg_color, size=None, reserved_bottom=0):
        if size is None: size = self.tile_size
        
        # Ensure positive size
        if size < 1: return
        
        rect = pygame.Rect(x, y, size, size)
        pygame.draw.rect(self.screen, bg_color, rect, border_radius=8)
        pygame.draw.rect(self.screen, (0, 0, 0), rect, width=1, border_radius=8)
        
        if not text: return
        
        # Handle multi-line
        lines = text.split('\n')
        surfaces = []
        max_line_w = 0
        total_h = 0
        
        for line in lines:
            s = self.cn_font.render(line, True, color)
            surfaces.append(s)
            max_line_w = max(max_line_w, s.get_width())
            total_h += s.get_height()
            
        # Calculate constraints
        max_w = max(1, size - 4)
        max_h = max(1, size - 4 - reserved_bottom) # Respect reserved bottom area
        
        scale = 1.0
        if max_line_w > max_w or total_h > max_h:
            scale = min(max_w / max_line_w, max_h / total_h)
            
        # Draw
        final_total_h = total_h * scale
        
        # Center vertically within the available top space
        available_h = size - reserved_bottom
        center_y_of_available = rect.top + available_h / 2
        current_y = center_y_of_available - final_total_h / 2
        
        for s in surfaces:
            new_w = max(1, int(s.get_width() * scale))
            new_h = max(1, int(s.get_height() * scale))
            
            if scale != 1.0:
                s = pygame.transform.scale(s, (new_w, new_h))
                
            s_rect = s.get_rect(centerx=rect.centerx, top=current_y)
            self.screen.blit(s, s_rect)
            current_y += new_h

    def draw_map(self, game_map, offset_x=50, offset_y=50):
        # Draw grid background
        for y in range(game_map.height):
            for x in range(game_map.width):
                screen_x = offset_x + x * (self.tile_size + self.margin)
                screen_y = offset_y + y * (self.tile_size + self.margin)
                
                # Check for treasure event
                if hasattr(game_map, 'treasure_events') and (x, y) in game_map.treasure_events:
                    event = game_map.treasure_events[(x, y)]
                    q_value = event['quality'].value
                    
                    # Draw base tile first
                    self.draw_rounded_rect_with_text(screen_x, screen_y, "", (0,0,0), (220, 220, 220))
                    
                    rect = pygame.Rect(screen_x, screen_y, self.tile_size, self.tile_size)
                    
                    if q_value in self.quality_animations:
                        anim_frames = self.quality_animations[q_value]
                        frame_idx = int(time.time() * 10) % len(anim_frames)
                        frame = anim_frames[frame_idx]
                        frame_rect = frame.get_rect(center=rect.center)
                        self.screen.blit(frame, frame_rect)
                        
                        # Add a small text indicator "宝"
                        txt = self.small_font.render("宝", True, self.get_quality_color(q_value))
                        txt_rect = txt.get_rect(center=rect.center)
                        self.screen.blit(txt, txt_rect)
                    else:
                        # Fallback
                        color = self.get_quality_color(q_value)
                        pygame.draw.rect(self.screen, color, rect, width=2, border_radius=8)
                        txt = self.small_font.render("宝", True, color)
                        txt_rect = txt.get_rect(center=rect.center)
                        self.screen.blit(txt, txt_rect)
                        
                else:
                    # Default ground tile
                    self.draw_rounded_rect_with_text(screen_x, screen_y, "", (0,0,0), (220, 220, 220))

    def draw_entity(self, entity, color, offset_x=50, offset_y=50):
        screen_x = offset_x + entity.x * (self.tile_size + self.margin)
        screen_y = offset_y + entity.y * (self.tile_size + self.margin)
        
        label = entity.name
        is_player = hasattr(entity, 'profession')
        
        # Auto-split for long names (e.g. > 3 chars)
        if len(label) > 3:
            mid = math.ceil(len(label) / 2)
            label = label[:mid] + "\n" + label[mid:]
        
        # Scale Calculation for Spawn Animation
        scale = 1.0
        if hasattr(entity, 'spawn_anim_progress') and entity.spawn_anim_progress < 1.0:
            p = entity.spawn_anim_progress
            if p < 0.7:
                # 0 to 1.2
                scale = (p / 0.7) * 1.2
            else:
                # 1.2 to 1.0
                scale = 1.2 - ((p - 0.7) / 0.3) * 0.2
        
        current_size = int(self.tile_size * scale)
        
        # Adjust position to keep centered
        center_x = screen_x + self.tile_size // 2
        center_y = screen_y + self.tile_size // 2
        draw_x = center_x - current_size // 2
        draw_y = center_y - current_size // 2
        
        # Draw Entity Body
        # Reserve space for HP bar (height 8 + margin 2 = 10, let's use 12 for safety)
        self.draw_rounded_rect_with_text(draw_x, draw_y, label, (255, 255, 255), color, size=current_size, reserved_bottom=12)
        
        # Draw HP Bar (Inside the tile, below name)
        # Scale bar as well? Or keep fixed?
        # If scaling entity, bar should probably scale or hide if too small.
        # Let's scale bar width.
        
        bar_height = 8
        bar_width = current_size - 4
        if bar_width < 4: return # Too small to draw
        
        bar_x = draw_x + 2
        bar_y = draw_y + current_size - bar_height - 2
        
        # Calculate ratio
        ratio = max(0, min(1, entity.hp / max(1, entity.max_hp)))
        
        # Colors
        if is_player:
            fill_color = (0, 255, 0) # Green
            text_color = (0, 0, 0)   # Black text
        else:
            fill_color = (0, 0, 0)   # Black
            text_color = (255, 255, 255) # White text
            
        # Draw Bar Background (Gray)
        pygame.draw.rect(self.screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
        # Draw Fill
        pygame.draw.rect(self.screen, fill_color, (bar_x, bar_y, int(bar_width * ratio), bar_height))
        # Draw Border
        pygame.draw.rect(self.screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height), 1)
        
        # Draw HP Text (Centered on bar)
        # Font needs to be very small
        hp_text = f"{int(entity.hp)}/{int(entity.max_hp)}"
        # Use small font, maybe scale down further if needed
        # self.small_font is 12px, bar is 8px. 
        # We need a tiny font or just scale existing small font.
        
        txt_surf = self.small_font.render(hp_text, True, text_color)
        # Scale to fit height of bar? Or just overlay.
        # Let's scale to height 8 if it's taller
        if txt_surf.get_height() > bar_height:
             scale = bar_height / txt_surf.get_height()
             txt_surf = pygame.transform.scale(txt_surf, (int(txt_surf.get_width() * scale), int(txt_surf.get_height() * scale)))
             
        txt_rect = txt_surf.get_rect(center=(bar_x + bar_width/2, bar_y + bar_height/2))
        self.screen.blit(txt_surf, txt_rect)

    def draw_floating_text(self, text_obj, offset_x=50, offset_y=50):
        # text_obj needs x, y (grid coords) or absolute pixel coords?
        # Let's assume text_obj stores absolute pixel coords or relative to grid
        # For simplicity, let's assume text_obj has screen_x and screen_y
        
        text_surf = self.cn_font.render(text_obj.text, True, text_obj.color)
        # Add a black outline for visibility
        outline_surf = self.cn_font.render(text_obj.text, True, (0, 0, 0))
        
        self.screen.blit(outline_surf, (text_obj.x + 1, text_obj.y + 1))
        self.screen.blit(text_surf, (text_obj.x, text_obj.y))

    def draw_loot_animation(self, anim):
        # anim.x, anim.y are current pixel coordinates
        rect = pygame.Rect(anim.x, anim.y, 24, 24) # Slightly larger
        
        # Determine Color and Text based on item_type
        bg_color = (255, 215, 0) # Gold default
        text_char = "宝"
        text_color = (0, 0, 0)
        
        if hasattr(anim, 'item_type'):
            if anim.item_type == "gold":
                bg_color = (255, 223, 0) # Gold
                text_char = "金"
                # Circle for coins
                pygame.draw.circle(self.screen, (0,0,0), rect.center, 12)
                pygame.draw.circle(self.screen, bg_color, rect.center, 10)
                text_surf = self.small_font.render(text_char, True, text_color)
                text_rect = text_surf.get_rect(center=rect.center)
                self.screen.blit(text_surf, text_rect)
                return

            elif anim.item_type == "ingot":
                bg_color = (255, 165, 0) # Orange
                text_char = "元"
                # Ingot shape (Trapezoid) - simplified as Rect
            elif anim.item_type == "item":
                bg_color = (200, 200, 200) # Silver/Gray
                text_char = "物"
                if anim.item_data and hasattr(anim.item_data, 'quality'):
                    # Use quality color
                    try:
                        q_name = anim.item_data.quality.name
                        if q_name == "DIVINE": bg_color = (255, 0, 0) # Red
                        elif q_name == "MYTHIC": bg_color = (255, 140, 0) # Dark Orange
                        elif q_name == "LEGENDARY": bg_color = (255, 215, 0) # Gold
                        elif q_name == "EPIC": bg_color = (138, 43, 226) # Purple
                        elif q_name == "RARE": bg_color = (30, 144, 255) # Blue
                        elif q_name == "HIGH": bg_color = (50, 205, 50) # Green
                        elif q_name == "NORMAL": bg_color = (200, 200, 200)
                    except:
                        pass
                
                # Try to use item name char
                if anim.item_data and hasattr(anim.item_data, 'name'):
                    text_char = anim.item_data.name[0]
                    
            elif anim.item_type == "bone_powder":
                bg_color = (240, 240, 240) # White
                text_char = "粉"
        
        # Default Rect Drawing
        pygame.draw.rect(self.screen, (0,0,0), rect.inflate(2,2), border_radius=4)
        pygame.draw.rect(self.screen, bg_color, rect, border_radius=4)
        pygame.draw.rect(self.screen, (255, 255, 255), rect, width=1, border_radius=4) # Inner highlight
        
        text_surf = self.small_font.render(text_char, True, text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        self.screen.blit(text_surf, text_rect)

    def draw_quest_tracker(self, rect, active_quests):
        if not active_quests:
            return
            
        # Draw in passed rect
        # x = 750 -> rect.x
        
        # Background
        # pygame.draw.rect(self.screen, (240, 240, 240), rect)
        # pygame.draw.rect(self.screen, (0, 0, 0), rect, 1)
        
        # Title
        title = self.cn_font.render("当前任务", True, (0, 0, 0))
        self.screen.blit(title, (rect.x + 10, rect.y + 5))
        
        # List first 3 active quests
        y_off = 25
        for i, q in enumerate(active_quests[:3]):
            # Quest Title
            q_title = self.small_font.render(f"[{q.title}]", True, (50, 50, 50))
            self.screen.blit(q_title, (rect.x + 10, rect.y + y_off))
            y_off += 15
            
            # Current Stage
            stage = q.get_current_stage()
            if stage:
                stage_desc = stage.description
                if stage.type == "kill":
                    stage_desc += f" ({stage.current_count}/{stage.count})"
                elif q.status.name == "READY_TO_TURN_IN":
                    stage_desc = "任务已完成"
                    
                st_txt = self.small_font.render(f" - {stage_desc}", True, (100, 100, 100))
                self.screen.blit(st_txt, (rect.x + 10, rect.y + y_off))
                y_off += 20
            elif q.status.name == "READY_TO_TURN_IN":
                st_txt = self.small_font.render(" - 任务已完成", True, (0, 150, 0))
                self.screen.blit(st_txt, (rect.x + 10, rect.y + y_off))
                y_off += 20

    def draw_npc_bar(self, rect, npcs, active_quests=None):
        # Draw NPCs in the rect provided (Top of Interaction Panel)
        # Center NPCs
        
        slot_width = 60
        spacing = 20
        total_width = len(npcs) * slot_width + (len(npcs) - 1) * spacing
        
        # Ensure it fits
        if total_width > rect.width:
            start_x = rect.x + 10 # Left align if overflow
        else:
            start_x = rect.x + (rect.width - total_width) // 2
            
        y_pos = rect.centery - slot_width // 2
        
        npc_rects = {}
        
        for i, npc in enumerate(npcs):
            x = start_x + i * (slot_width + spacing)
            r = pygame.Rect(x, y_pos, slot_width, slot_width)
            
            # Border Color logic (Fixed color, no flash)
            border_color = (100, 100, 100) # Default
            
            pygame.draw.rect(self.screen, (200, 200, 220), r, border_radius=5)
            pygame.draw.rect(self.screen, border_color, r, width=2, border_radius=5)
            
            # Name Layout: 2 lines, 2 chars per line
            if len(npc.name) >= 2:
                line1 = npc.name[:2]
                line2 = npc.name[2:]
                
                txt1 = self.small_font.render(line1, True, (0, 0, 0))
                txt2 = self.small_font.render(line2, True, (0, 0, 0))
                
                # Center vertically
                total_h = txt1.get_height() + txt2.get_height() + 2
                start_y = r.centery - total_h / 2
                
                rect1 = txt1.get_rect(centerx=r.centerx, top=start_y)
                rect2 = txt2.get_rect(centerx=r.centerx, top=rect1.bottom + 2)
                
                self.screen.blit(txt1, rect1)
                self.screen.blit(txt2, rect2)
            else:
                # Fallback for short names
                name_txt = self.small_font.render(npc.name, True, (0, 0, 0))
                name_rect = name_txt.get_rect(center=r.center)
                self.screen.blit(name_txt, name_rect)
            
            npc_rects[npc.name] = r
            
        return npc_rects

    def draw_ui_buttons(self, rect):
        # Draw Buttons in rect (Bottom of Interaction Panel)
        # Wide Layout: 1 Row of 6 Buttons
        btn_width = 100
        btn_height = 40
        spacing_x = 20
        spacing_y = 0
        
        labels = ["装备", "背包", "技能", "设置", "任务"]
        
        # 6 cols, 1 row
        cols = 5
        rows = 1
        
        total_w = cols * btn_width + (cols - 1) * spacing_x
        total_h = btn_height
        
        start_x = rect.x + (rect.width - total_w) // 2
        start_y = rect.y + (rect.height - total_h) // 2
        
        button_rects = {}
        
        for i, label in enumerate(labels):
            # row = 0
            col = i
            
            x = start_x + col * (btn_width + spacing_x)
            y = start_y
            
            r = pygame.Rect(x, y, btn_width, btn_height)
            
            # Button style
            bg_color = (100, 100, 100)
            
            pygame.draw.rect(self.screen, bg_color, r, border_radius=5)
            pygame.draw.rect(self.screen, (200, 200, 200), r, width=2, border_radius=5)
            
            text_color = (255, 255, 255)
            
            text_surf = self.cn_font.render(label, True, text_color)
            text_rect = text_surf.get_rect(center=r.center)
            self.screen.blit(text_surf, text_rect)
            
            button_rects[label] = r
            
        return button_rects
