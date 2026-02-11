import pygame


class FloatingText:
    def __init__(self, text, x, y, color, duration=60):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.duration = duration
        self.lifetime = 0
        self.velocity_y = -1  # Move up

    def update(self):
        self.y += self.velocity_y
        self.lifetime += 1
        return self.lifetime < self.duration


class UIWindow:
    def __init__(self, title, x, y, width, height, renderer, show_close_button=True):
        self.title = title
        self.rect = pygame.Rect(x, y, width, height)
        self.renderer = renderer
        self.visible = False
        self.show_close_button = show_close_button
        self.close_btn_rect = pygame.Rect(x + width - 25, y + 5, 20, 20)

    def draw(self, screen):
        if not self.visible:
            return

        # Window Background
        pygame.draw.rect(screen, (240, 240, 240), self.rect, border_radius=5)
        pygame.draw.rect(screen, (50, 50, 50), self.rect, width=2, border_radius=5)

        # Title Bar
        title_surf = self.renderer.cn_font.render(self.title, True, (0, 0, 0))
        screen.blit(title_surf, (self.rect.x + 10, self.rect.y + 10))

        # Close Button
        if self.show_close_button:
            pygame.draw.rect(screen, (200, 50, 50), self.close_btn_rect, border_radius=3)
            close_txt = self.renderer.small_font.render("X", True, (255, 255, 255))
            screen.blit(close_txt, (self.close_btn_rect.x + 6, self.close_btn_rect.y + 4))

        self.draw_content(screen)

    def _prepare_tooltip_lines(self, item, diffs=None, show_usage=True, header_text=None, slot_level=0):
        lines = []
        if header_text:
            lines.append(header_text)
        lines.append(item.name)
        
        # Stat Translation Map
        stat_map = {
            "attack": "攻击",
            "defense": "防御",
            "magic": "魔法",
            "taoism": "道术",
            "magic_defense": "魔防",
            "hp": "生命",
            "mp": "魔法",
            "accuracy": "准确",
            "dodge": "敏捷",
            "crit": "暴击",
            "luck": "幸运"
        }

        # Enhancement Level
        if hasattr(item, 'enhancement_level') and item.enhancement_level > 0:
            lines[-1] += f" +{item.enhancement_level}" # Append to item name (last line added)

        # Item Type
        lines.append(f"类型: {item.item_type.value}")
        
        # Quality
        if hasattr(item, 'quality'):
             lines.append(f"品质: {item.quality.value}")

        # Level Requirement
        req_lvl = getattr(item, 'min_level', 0)
        if req_lvl <= 1:
             req_lvl = getattr(item, 'level_req', 0)
        
        if req_lvl > 1:
            lines.append(f"需要等级: {req_lvl}")

        # Stats
        if item.stats:
            lines.append("属性:")
            for k, v in item.stats.items():
                cn_key = stat_map.get(k, k)
                
                parts = []
                # Base + Item Enhance
                val_str = f"  {cn_key}: {v}"
                
                # Calculate Item Enhancement Bonus
                item_enh = getattr(item, 'enhancement_level', 0)
                if item_enh > 0:
                     # Bonus = Level (Flat 1 point per level)
                     bonus = item_enh
                     val_str += f" (+{bonus})"
                
                parts.append({"text": val_str, "color": None})
                
                # Slot Enhance (Body Forging)
                if slot_level > 0:
                    # Bonus = Base * Level * 1%
                    slot_bonus = int(v * slot_level * 0.01)
                    # Minimum 1 bonus if forged
                    if slot_bonus < 1: slot_bonus = 1
                    parts.append({"text": f" (+{slot_bonus})", "color": (0, 255, 0)})
                
                lines.append(parts)
        
        # Comparison Changes (Unified at bottom)
        if diffs:
            if diffs.get('dual_mode'):
                lines.append("")
                # Headers
                lines.append({"is_dual": True, 
                              "left": {"text": "左手对比:", "color": (200, 200, 0)}, 
                              "right": {"text": "右手对比:", "color": (200, 200, 0)}})
                
                # Prepare lists
                l_lines = []
                if diffs['left'].get('gains'): 
                    l_lines.extend([{"text": g, "color": (0, 255, 0)} for g in diffs['left']['gains']])
                if diffs['left'].get('losses'): 
                    l_lines.extend([{"text": l, "color": (255, 0, 0)} for l in diffs['left']['losses']])
                    
                r_lines = []
                if diffs['right'].get('gains'): 
                    r_lines.extend([{"text": g, "color": (0, 255, 0)} for g in diffs['right']['gains']])
                if diffs['right'].get('losses'): 
                    r_lines.extend([{"text": l, "color": (255, 0, 0)} for l in diffs['right']['losses']])
                
                max_len = max(len(l_lines), len(r_lines))
                for i in range(max_len):
                    left = l_lines[i] if i < len(l_lines) else None
                    right = r_lines[i] if i < len(r_lines) else None
                    lines.append({"is_dual": True, "left": left, "right": right})

            elif diffs.get('gains') or diffs.get('losses'):
                lines.append("")
                lines.append("替换装备属性将发生以下变化:")
                
                # Gains (Green)
                if diffs.get('gains'):
                    for gain in diffs['gains']:
                        lines.append({"text": gain, "color": (0, 255, 0)})
                
                # Losses (Red)
                if diffs.get('losses'):
                    for loss in diffs['losses']:
                        lines.append({"text": loss, "color": (255, 0, 0)})
        
        # Description / Usage
        from src.systems.equipment.item import ItemType
        if show_usage and item.item_type in [ItemType.WEAPON, ItemType.ARMOR, ItemType.HELMET, ItemType.NECKLACE, ItemType.RING, ItemType.BRACELET, ItemType.BOOTS, ItemType.BELT, ItemType.MEDAL]:
            lines.append("")
            lines.append("鼠标右键点击穿戴")
            
        return lines

    def _calculate_tooltip_dim(self, lines):
        font = self.renderer.small_font
        max_w = 0
        
        # For dual column layout
        self.tooltip_dual_left_w = 0 
        
        for line in lines:
            w = 0
            if isinstance(line, list):
                for part in line:
                    try: w += font.size(part["text"])[0]
                    except: w += 50
            elif isinstance(line, dict):
                 if line.get("is_dual"):
                     # Dual line
                     l_w = 0
                     if line.get("left"):
                         try: l_w = font.size(line["left"]["text"])[0]
                         except: l_w = 50
                     
                     r_w = 0
                     if line.get("right"):
                         try: r_w = font.size(line["right"]["text"])[0]
                         except: r_w = 50
                         
                     if l_w > self.tooltip_dual_left_w: self.tooltip_dual_left_w = l_w
                     w = l_w + 20 + r_w
                 else:
                     try: w = font.size(line["text"])[0]
                     except: w = 100
            else:
                try: w = font.size(line)[0]
                except: w = 100
            if w > max_w: max_w = w
            
        w = max_w + 20
        h = len(lines) * 20 + 10
        return w, h

    def draw_tooltip(self, screen, item, x, y, diffs=None, show_usage=True, header_text=None, slot_level=0):
        font = self.renderer.small_font
        lines = self._prepare_tooltip_lines(item, diffs, show_usage, header_text, slot_level)
        w, h = self._calculate_tooltip_dim(lines)
        
        # Adjust position to not go off screen
        if x + w > screen.get_width():
            x = x - w - 40 
        if y + h > screen.get_height():
            y = y - h - 40 
            
        # Draw Bg
        rect = pygame.Rect(x, y, w, h)
        self.tooltip_rect = rect # Store for click detection
        pygame.draw.rect(screen, (0, 0, 0, 200), rect) 
        # Use surface for alpha
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        s.fill((0, 0, 0, 220))
        screen.blit(s, (x, y))
        
        # Border
        color = self.renderer.get_quality_color(item.quality.value)
        pygame.draw.rect(screen, color, rect, width=1)
        
        # Text
        cur_y = y + 5
        for i, line in enumerate(lines):
            c = (255, 255, 255)
            
            # Header handling
            if header_text and i == 0:
                c = (0, 255, 0) # Green for header
            elif (header_text and i == 1) or (not header_text and i == 0):
                c = color # Item Name Color
            elif isinstance(line, str) and "右键" in line: c = (0, 255, 0)
            elif isinstance(line, str) and "替换装备属性将发生以下变化" in line: c = (200, 200, 0) # Yellow for title
            
            # Render
            cur_x = x + 10
            if isinstance(line, list):
                for part in line:
                    part_color = part["color"] if part["color"] else c
                    txt = font.render(part["text"], True, part_color)
                    screen.blit(txt, (cur_x, cur_y))
                    cur_x += txt.get_width()
            elif isinstance(line, dict):
                 if line.get("is_dual"):
                     # Dual Column Draw
                     # Left Part
                     if line.get("left"):
                         part = line["left"]
                         part_color = part.get("color", c)
                         txt = font.render(part["text"], True, part_color)
                         screen.blit(txt, (x + 10, cur_y))
                     
                     # Right Part
                     if line.get("right"):
                         part = line["right"]
                         part_color = part.get("color", c)
                         txt = font.render(part["text"], True, part_color)
                         # Start = x + 10 + max_left_w + 20
                         r_x = x + 10 + getattr(self, 'tooltip_dual_left_w', 100) + 20
                         screen.blit(txt, (r_x, cur_y))
                 else:
                     # Special dict for diff lines with specific color
                     part_color = line.get("color", c)
                     txt = font.render(line["text"], True, part_color)
                     screen.blit(txt, (cur_x, cur_y))
            else:
                txt = font.render(line, True, c)
                screen.blit(txt, (cur_x, cur_y))
                
            cur_y += 20

        return rect

    def draw_content(self, screen):
        pass # To be overridden

    def handle_click(self, pos, button=1):
        if not self.visible:
            return False
        
        # Check tooltip click (Enhance button)
        if hasattr(self, 'enhance_btn_rect') and self.enhance_btn_rect and self.enhance_btn_rect.collidepoint(pos):
             if self.enhance_target_item:
                 self.enhance_item(self.enhance_target_item)
                 return True
        
        # Check close button
        if self.show_close_button and self.close_btn_rect.collidepoint(pos):
            self.visible = False
            return True
            
        return self.rect.collidepoint(pos)

class InputDialog(UIWindow):
    def __init__(self, renderer, title, prompt, callback):
        super().__init__(title, 300, 200, 300, 150, renderer)
        self.prompt = prompt
        self.callback = callback
        self.input_text = "1"
        self.input_rect = pygame.Rect(self.rect.x + 50, self.rect.y + 70, 200, 30)
        
        # Buttons
        self.ok_btn = pygame.Rect(self.rect.x + 50, self.rect.bottom - 40, 80, 30)
        self.cancel_btn = pygame.Rect(self.rect.right - 130, self.rect.bottom - 40, 80, 30)
        
        # Activate text input
        pygame.key.start_text_input()
        pygame.key.set_text_input_rect(self.input_rect)

    def draw_content(self, screen):
        font = self.renderer.cn_font
        
        # Prompt
        txt = font.render(self.prompt, True, (0, 0, 0))
        screen.blit(txt, (self.rect.x + 20, self.rect.y + 40))
        
        # Input Box
        self.input_rect.topleft = (self.rect.x + 50, self.rect.y + 70) # Update pos
        pygame.draw.rect(screen, (255, 255, 255), self.input_rect)
        pygame.draw.rect(screen, (0, 0, 255), self.input_rect, 2)
        
        inp_surf = font.render(self.input_text, True, (0, 0, 0))
        screen.blit(inp_surf, (self.input_rect.x + 5, self.input_rect.y + 5))
        
        # Buttons
        self.ok_btn.topleft = (self.rect.x + 50, self.rect.bottom - 40)
        self.cancel_btn.topleft = (self.rect.right - 130, self.rect.bottom - 40)
        
        pygame.draw.rect(screen, (100, 200, 100), self.ok_btn, border_radius=5)
        ok_txt = font.render("确定", True, (255, 255, 255))
        screen.blit(ok_txt, ok_txt.get_rect(center=self.ok_btn.center))
        
        pygame.draw.rect(screen, (200, 100, 100), self.cancel_btn, border_radius=5)
        c_txt = font.render("取消", True, (255, 255, 255))
        screen.blit(c_txt, c_txt.get_rect(center=self.cancel_btn.center))

    def handle_click(self, pos, button=1):
        if not super().handle_click(pos, button): return False
        
        if self.ok_btn.collidepoint(pos):
            if self.callback:
                self.callback(self.input_text)
            self.visible = False
            pygame.key.stop_text_input()
            return True
            
        if self.cancel_btn.collidepoint(pos):
            self.visible = False
            pygame.key.stop_text_input()
            return True
            
        return True
        
    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif event.key == pygame.K_RETURN:
                if self.callback:
                    self.callback(self.input_text)
                self.visible = False
                pygame.key.stop_text_input()
            elif event.key == pygame.K_ESCAPE:
                self.visible = False
                pygame.key.stop_text_input()
            else:
                # Allow numbers only
                if event.unicode.isdigit():
                    if len(self.input_text) < 3: # Max 999
                        self.input_text += event.unicode
        return True

        if self.close_btn_rect.collidepoint(pos):
            self.visible = False
            return True
        
        return self.rect.collidepoint(pos)

    def enhance_item(self, item):
        # Enhance logic
        if not hasattr(item, 'enhancement_level'): return
        
        if item.enhancement_level >= 15:
            # Already max
            return
            
        cost_gold = max(1, item.enhancement_level) * 1000
        
        # Check resources
        # We need access to player inventory and gold
        # We assume self.player exists in derived windows like EquipmentWindow/InventoryWindow
        # But UIWindow base doesn't have it.
        # We should move this logic or ensure player is available.
        # InventoryWindow and EquipmentWindow have self.player.
        
        if not hasattr(self, 'player'): return
        
        # Check gold
        if self.player.gold < cost_gold:
            if hasattr(self, 'game_engine') and self.game_engine:
                self.game_engine.spawn_floating_text("金币不足", self.player.x, self.player.y, (255, 0, 0))
            else:
                print("Not enough gold")
            return
            
        # Check Upgrade Stone
        # Find stone in inventory
        stone_idx = -1
        for i, it in enumerate(self.player.inventory.items):
            if it and it.name == "强化石":
                stone_idx = i
                break
                
        if stone_idx == -1:
            if hasattr(self, 'game_engine') and self.game_engine:
                self.game_engine.spawn_floating_text("强化石不足", self.player.x, self.player.y, (255, 0, 0))
            else:
                print("No Upgrade Stone")
            return
            
        # Consume
        self.player.gold -= cost_gold
        # Remove 1 stone (handle stackable if needed, but UpgradeStone is usually stackable now)
        # Check if stackable logic needs handling
        stone_item = self.player.inventory.items[stone_idx]
        if stone_item.stackable and stone_item.count > 1:
            stone_item.count -= 1
        else:
            self.player.inventory.items[stone_idx] = None
        
        # Success
        item.enhancement_level += 1
        
        # Update stats
        # Simply re-generate or just assume +1 bonus is calculated dynamically in get_stats?
        # Our Equipment class generates base stats. The bonus is calculated in draw_tooltip logic 
        # but NOT applied to actual stats dictionary?
        # User said: "对应的核心属性+1". 
        # We should update stats permanently.
        for k in item.stats:
             item.stats[k] += 1
             
        # Recalculate player stats immediately
        self.player.recalculate_stats()
             
        if hasattr(self, 'game_engine') and self.game_engine:
            self.game_engine.spawn_floating_text("强化成功", self.player.x, self.player.y, (0, 255, 0))
        else:
            print(f"Enhanced to +{item.enhancement_level}")

    def handle_event(self, event):
        pass


class RecycleWindow(UIWindow):
    def __init__(self, renderer, player, game_engine=None):
        # Increased size to prevent overflow (Width 450, Height 400)
        super().__init__("装备回收", 300, 150, 450, 400, renderer)
        self.player = player
        self.game_engine = game_engine
        self.checkboxes = {
            "普通": False,
            "优良": False,
            "精品": False,
            "极品": False,
            "传说": False,
            "史诗": False,
            "神话": False
        }
        
        # Load checkboxes from engine if available
        if self.game_engine and hasattr(self.game_engine, 'recycle_qualities'):
            for k, v in self.game_engine.recycle_qualities.items():
                if k in self.checkboxes:
                    self.checkboxes[k] = v
        
        # Auto Recycle Checkbox
        self.auto_recycle_rect = pygame.Rect(self.rect.x + 30, self.rect.y + 335, 20, 20)
        self.auto_recycle_checked = False
        if self.game_engine:
            self.auto_recycle_checked = self.game_engine.auto_recycle_enabled
        
        # Init button rect relative logic
        # Center the button
        btn_w = 140
        btn_h = 30
        btn_x = (self.rect.width - btn_w) // 2
        btn_y = self.rect.height - 50
        self.recycle_btn_rect = pygame.Rect(self.rect.x + btn_x, self.rect.y + btn_y, btn_w, btn_h)
        
        self.confirm_dialog = None

    def draw(self, screen):
        if not self.visible: return
        
        # Window Background (Gray)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, border_radius=5) 
        pygame.draw.rect(screen, (50, 50, 50), self.rect, width=2, border_radius=5)

        # Title Bar
        title_surf = self.renderer.cn_font.render(self.title, True, (0, 0, 0))
        screen.blit(title_surf, (self.rect.x + 10, self.rect.y + 10))

        # Close Button
        # Re-calculate close button rect in case window size changed in init vs base
        self.close_btn_rect = pygame.Rect(self.rect.x + self.rect.width - 25, self.rect.y + 5, 20, 20)
        pygame.draw.rect(screen, (200, 50, 50), self.close_btn_rect, border_radius=3)
        close_txt = self.renderer.small_font.render("X", True, (255, 255, 255))
        screen.blit(close_txt, (self.close_btn_rect.x + 6, self.close_btn_rect.y + 4))

        self.draw_content(screen)
        
        if self.confirm_dialog and self.confirm_dialog.visible:
            self.confirm_dialog.draw(screen)

    def draw_content(self, screen):
        font = self.renderer.cn_font
        small_font = self.renderer.small_font
        
        # Reward Info Map
        rewards_info = {
            "普通": "100金币 + 强化石x1",
            "优良": "200金币 + 强化石x1",
            "精品": "300金币 + 强化石x1",
            "极品": "1元宝 + 强化石x2",
            "传说": "2元宝 + 强化石x3",
            "史诗": "3元宝 + 强化石x4",
            "神话": "4元宝 + 神话石x1 + 强化石x5"
        }
        
        y_offset = 50
        x_offset = 30
        spacing = 40
        
        for q, checked in self.checkboxes.items():
            abs_rect = pygame.Rect(self.rect.x + x_offset, self.rect.y + y_offset, 20, 20)
            
            # Checkbox
            pygame.draw.rect(screen, (255, 255, 255), abs_rect)
            pygame.draw.rect(screen, (0, 0, 0), abs_rect, 1)
            
            if checked:
                pygame.draw.line(screen, (0, 0, 0), (abs_rect.x + 4, abs_rect.y + 10), (abs_rect.x + 8, abs_rect.y + 16), 2)
                pygame.draw.line(screen, (0, 0, 0), (abs_rect.x + 8, abs_rect.y + 16), (abs_rect.x + 16, abs_rect.y + 4), 2)
                
            # Label (Quality)
            color = self.renderer.get_quality_color(q)
            lbl = font.render(q, True, color)
            screen.blit(lbl, (abs_rect.right + 10, abs_rect.y))
            
            # Reward Info
            info = rewards_info.get(q, "")
            info_surf = small_font.render(info, True, (50, 50, 50))
            screen.blit(info_surf, (abs_rect.right + 60, abs_rect.y + 2))
            
            y_offset += spacing

        # Auto Recycle Checkbox
        self.auto_recycle_rect = pygame.Rect(self.rect.x + 30, self.rect.y + 335, 20, 20)
        pygame.draw.rect(screen, (255, 255, 255), self.auto_recycle_rect)
        pygame.draw.rect(screen, (0, 0, 0), self.auto_recycle_rect, 1)
        if self.auto_recycle_checked:
            pygame.draw.line(screen, (0, 0, 0), (self.auto_recycle_rect.x + 4, self.auto_recycle_rect.y + 10), (self.auto_recycle_rect.x + 8, self.auto_recycle_rect.y + 16), 2)
            pygame.draw.line(screen, (0, 0, 0), (self.auto_recycle_rect.x + 8, self.auto_recycle_rect.y + 16), (self.auto_recycle_rect.x + 16, self.auto_recycle_rect.y + 4), 2)
            
        ar_lbl = small_font.render("开启自动回收(10秒/次)", True, (0, 0, 0))
        screen.blit(ar_lbl, (self.auto_recycle_rect.right + 10, self.auto_recycle_rect.y + 2))

        # Recycle Button
        # Re-calc position to be safe
        btn_w = 140
        btn_h = 30
        btn_x = (self.rect.width - btn_w) // 2
        btn_y = self.rect.height - 50
        self.recycle_btn_rect = pygame.Rect(self.rect.x + btn_x, self.rect.y + btn_y, btn_w, btn_h)
        
        pygame.draw.rect(screen, (200, 50, 50), self.recycle_btn_rect, border_radius=5)
        pygame.draw.rect(screen, (0, 0, 0), self.recycle_btn_rect, width=1, border_radius=5)
        
        txt = font.render("开始回收", True, (255, 255, 255))
        txt_rect = txt.get_rect(center=self.recycle_btn_rect.center)
        screen.blit(txt, txt_rect)

    def handle_click(self, pos, button=1):
        if not self.visible: return False
        
        # Check confirm dialog
        if self.confirm_dialog and self.confirm_dialog.visible:
            if self.confirm_dialog.handle_click(pos, button):
                return True
            return True
        
        if self.close_btn_rect.collidepoint(pos):
            self.visible = False
            return True
            
        mx, my = pos
        
        # Check checkboxes
        y_offset = 50
        x_offset = 30
        spacing = 40
        
        for q in self.checkboxes.keys():
            abs_rect = pygame.Rect(self.rect.x + x_offset, self.rect.y + y_offset, 20, 20)
            if abs_rect.collidepoint(mx, my):
                self.checkboxes[q] = not self.checkboxes[q]
                # Sync with engine settings
                if self.game_engine:
                    self.game_engine.recycle_qualities[q] = self.checkboxes[q]
                return True
            y_offset += spacing
            
        # Check Auto Recycle
        self.auto_recycle_rect = pygame.Rect(self.rect.x + 30, self.rect.y + 335, 20, 20)
        if self.auto_recycle_rect.collidepoint(mx, my):
            self.auto_recycle_checked = not self.auto_recycle_checked
            if self.game_engine:
                self.game_engine.auto_recycle_enabled = self.auto_recycle_checked
            return True
                
        # Check Recycle Button
        if self.recycle_btn_rect.collidepoint(mx, my):
            self.try_recycle()
            return True
            
        return True

    def try_recycle(self):
        # Check if confirmation is needed
        skip = False
        if self.game_engine:
            skip = self.game_engine.skip_recycle_confirmation
            
        if skip:
            self.perform_recycle()
        else:
            # Show confirmation
            def on_confirm(opt):
                if opt == "确定":
                    self.perform_recycle()
                    
            def on_checkbox(checked):
                if self.game_engine:
                    self.game_engine.skip_recycle_confirmation = checked
            
            msg = "当前操作将回收所有选中的品质装备。"
            self.confirm_dialog = DialogWindow(self.renderer, "确认回收", msg, ["确定", "取消"], on_confirm, 
                                             show_checkbox=True, checkbox_text="下次不再提示，关闭后将无法再开启二次确认",
                                             on_checkbox_toggle=on_checkbox)
            self.confirm_dialog.rect.center = (1024//2, 768//2)

    def perform_recycle(self):
        if not self.player: return
        
        # Use centralized recycle logic
        results = self.player.recycle_items(self.checkboxes)
        count = results["count"]
        
        if count > 0:
            msg = f"回收了 {count} 件装备。\n获得: 金币 {results['gold']}, 元宝 {results['ingots']}, 强化石 {results['stone']}, 神话强化石 {results['mythic_stone']}"
            print(msg)
            if self.game_engine:
                self.game_engine.log(msg)
                # Spawn floating text
                if self.player:
                    self.game_engine.spawn_floating_text(f"回收成功", self.player.x, self.player.y, (0, 255, 0))
        else:
            if self.game_engine:
                self.game_engine.log("没有符合条件的装备可回收")

class QuestDetailWindow(UIWindow):
    def __init__(self, renderer, quest):
        super().__init__("任务详情", 300, 150, 400, 400, renderer)
        self.quest = quest
        self.visible = True

    def draw_content(self, screen):
        y = self.rect.y + 40
        x = self.rect.x + 20
        width = self.rect.width - 40
        font = self.renderer.cn_font
        small_font = self.renderer.small_font
        
        # Title
        title_surf = font.render(f"任务: {self.quest.title}", True, (0, 0, 0))
        screen.blit(title_surf, (x, y))
        y += 30
        
        # Description
        desc_lines = self.wrap_text(self.quest.description, width, font)
        for line in desc_lines:
            txt = font.render(line, True, (50, 50, 50))
            screen.blit(txt, (x, y))
            y += 20
        y += 10
        
        # Current Stage
        stage = self.quest.get_current_stage()
        if stage:
            status_txt = f"当前目标: {stage.description}"
            if stage.type == "kill":
                status_txt += f" ({stage.current_count}/{stage.count})"
            
            st_surf = font.render(status_txt, True, (200, 0, 0))
            screen.blit(st_surf, (x, y))
            y += 30
        elif self.quest.status.name == "READY_TO_TURN_IN":
             st_surf = font.render("当前目标: 去交付任务", True, (0, 200, 0))
             screen.blit(st_surf, (x, y))
             y += 30
        elif self.quest.status.name == "COMPLETED":
             st_surf = font.render("任务已完成", True, (0, 100, 0))
             screen.blit(st_surf, (x, y))
             y += 30
             
        # Rewards
        y += 10
        rew_surf = font.render("奖励:", True, (0, 0, 0))
        screen.blit(rew_surf, (x, y))
        y += 25
        
        if self.quest.reward_xp > 0:
            txt = small_font.render(f"经验: {self.quest.reward_xp}", True, (0, 0, 200))
            screen.blit(txt, (x + 10, y))
            y += 20
            
        if self.quest.reward_gold > 0:
            txt = small_font.render(f"金币: {self.quest.reward_gold}", True, (200, 150, 0))
            screen.blit(txt, (x + 10, y))
            y += 20
            
        if self.quest.reward_items:
            txt = small_font.render("物品:", True, (0, 0, 0))
            screen.blit(txt, (x + 10, y))
            y += 20
            
            # Draw Item Slots
            slot_size = 40
            spacing = 10
            start_item_x = x + 20
            
            for i, item in enumerate(self.quest.reward_items):
                item_x = start_item_x + i * (slot_size + spacing)
                self.renderer.draw_item_slot(item_x, y, slot_size, item)
            
            y += slot_size + 10

    def wrap_text(self, text, width, font):
        lines = []
        current_line = ""
        for char in text:
            if font.size(current_line + char)[0] > width:
                lines.append(current_line)
                current_line = char
            else:
                current_line += char
        lines.append(current_line)
        return lines

class QuestWindow(UIWindow):
    def __init__(self, renderer, game_engine):
        super().__init__("任务列表", 200, 100, 300, 500, renderer)
        self.game_engine = game_engine
        self.detail_window = None

    def draw(self, screen):
        super().draw(screen)
        if self.detail_window and self.detail_window.visible:
            self.detail_window.draw(screen)

    def draw_content(self, screen):
        # List Active Quests
        quests = self.game_engine.quest_manager.active_quests
        # Also list completed? Maybe just active for now as per requirement "task interface displays different task names"
        
        y = self.rect.y + 50
        x = self.rect.x + 20
        
        if not quests:
            txt = self.renderer.cn_font.render("当前无进行中任务", True, (100, 100, 100))
            screen.blit(txt, (x, y))
            return

        for q in quests:
            # Color based on status
            color = (0, 0, 0)
            if q.status.name == "READY_TO_TURN_IN":
                color = (0, 150, 0)
            
            # Draw clickable area background if hovered? (Skip for now)
            txt = self.renderer.cn_font.render(f"[{q.id}] {q.title}", True, color)
            screen.blit(txt, (x, y))
            
            # Store rect for click detection? 
            # We can re-calculate in handle_click since list is simple
            y += 30

    def handle_click(self, pos, button=1):
        # Check detail window first
        if self.detail_window and self.detail_window.visible:
            if self.detail_window.handle_click(pos, button):
                return True
                
        if not super().handle_click(pos, button):
            return False
            
        # Check quest list clicks
        quests = self.game_engine.quest_manager.active_quests
        y = self.rect.y + 50
        x = self.rect.x + 20
        width = self.rect.width - 40
        height = 25
        
        for q in quests:
            rect = pygame.Rect(x, y, width, height)
            if rect.collidepoint(pos):
                # Open detail window
                self.detail_window = QuestDetailWindow(self.renderer, q)
                return True
            y += 30
            
        return True

class SkillWindow(UIWindow):
    def __init__(self, renderer, player):
        super().__init__("技能列表", 150, 150, 300, 400, renderer)
        self.player = player
        self.skill_rects = []

    def draw_content(self, screen):
        y = self.rect.y + 50
        x = self.rect.x + 20
        
        self.skill_rects = []
        
        if not self.player.skills:
            txt = self.renderer.cn_font.render("暂无技能", True, (100, 100, 100))
            screen.blit(txt, (x, y))
            return

        for skill in self.player.skills:
            if not skill: continue
            
            # Determine color (Active or not)
            color = (0, 0, 0)
            bg_color = (200, 200, 200)
            if self.player.active_skill and self.player.active_skill.name == skill.name:
                color = (255, 0, 0)
                bg_color = (255, 200, 200)
            
            rect = pygame.Rect(x, y, self.rect.width - 40, 40)
            pygame.draw.rect(screen, bg_color, rect, border_radius=5)
            pygame.draw.rect(screen, color, rect, width=1, border_radius=5)
            
            # Icon (if exists)
            # For now just text
            txt = self.renderer.cn_font.render(skill.name, True, color)
            txt_rect = txt.get_rect(midleft=(rect.x + 10, rect.centery))
            screen.blit(txt, txt_rect)
            
            # Info
            info = f"MP: {skill.mp_cost}"
            info_txt = self.renderer.small_font.render(info, True, (100, 100, 100))
            info_rect = info_txt.get_rect(midright=(rect.right - 10, rect.centery))
            screen.blit(info_txt, info_rect)
            
            self.skill_rects.append((rect, skill))
            y += 50

    def handle_click(self, pos, button=1):
        if not super().handle_click(pos, button):
            return False
            
        for rect, skill in self.skill_rects:
            if rect.collidepoint(pos):
                # Toggle active skill
                if self.player.active_skill and self.player.active_skill.name == skill.name:
                    self.player.active_skill = None # Deactivate
                else:
                    self.player.active_skill = skill
                return True
        return True

class AttributeWindow(UIWindow):
    def __init__(self, renderer, player):
        super().__init__("角色属性", 100, 100, 250, 400, renderer)
        self.player = player

    def draw_content(self, screen):
        lines = [
            f"姓名: {self.player.name}",
            f"职业: {self.player.profession.value}",
            f"等级: {self.player.level}",
            f"经验: {self.player.current_xp}",
            f"生命值: {self.player.hp} / {self.player.max_hp}",
            f"魔法值: {self.player.mp} / {self.player.max_mp}",
            f"攻击力: {self.player.attack}",
            f"魔法力: {self.player.magic}",
            f"道术力: {self.player.taoism}",
            f"防御力: {self.player.defense}",
            f"魔法防御: {self.player.magic_defense}",
            f"攻击速度: {getattr(self.player, 'attack_speed', 0)}",
            f"冷却缩减: {getattr(self.player, 'cooldown_reduction', 0)}%",
        ]
        
        y_off = 50
        for line in lines:
            txt = self.renderer.cn_font.render(line, True, (0, 0, 0))
            screen.blit(txt, (self.rect.x + 20, self.rect.y + y_off))
            y_off += 25

class EquipmentWindow(UIWindow):
    def __init__(self, renderer, player):
        super().__init__("已穿戴装备", 360, 50, 320, 450, renderer) # Adjusted size
        self.player = player
        self.hover_item = None
        self.hover_rect = None
        
        # Define slot positions (relative to window)
        # Center X is 160
        cx = 160
        
        self.slot_positions = {
            "helmet": (cx, 50),
            "necklace": (cx, 100),
            "weapon": (cx - 80, 160),
            "armor": (cx, 160),
            "medal": (cx + 80, 160),
            "bracelet_l": (cx - 80, 220),
            "belt": (cx, 220),
            "bracelet_r": (cx + 80, 220),
            "ring_l": (cx - 80, 280),
            "boots": (cx, 340),
            "ring_r": (cx + 80, 280)
        }
        
        self.slot_names = {
            "weapon": "武器", "armor": "衣服", "helmet": "头盔",
            "necklace": "项链", "bracelet_l": "手左", "bracelet_r": "手右",
            "ring_l": "戒左", "ring_r": "戒右",
            "belt": "腰带", "boots": "鞋子", "medal": "勋章"
        }
        
        # Enhance Button & Forge Button
        # Total width: 80 + 20 + 80 = 180
        start_x = (self.rect.width - 180) // 2
        self.enhance_btn_rect = pygame.Rect(start_x, self.rect.height - 40, 80, 25)
        self.forge_btn_rect = pygame.Rect(start_x + 100, self.rect.height - 40, 80, 25)
        
        self.selected_item = None
        self.selected_slot = None

    def get_enhance_cost(self, item):
        if not item or not hasattr(item, 'enhancement_level'): return None
        # Show cost for NEXT level, not current level
        # Current level 0 -> Cost for +1
        # Current level 1 -> Cost for +2
        next_level = item.enhancement_level + 1
        cost_gold = max(1, next_level) * 1000
        cost_stone = next_level # Stone cost usually matches target level or similar scaling
        
        stone_count = self.player.inventory.get_item_count("强化石")
        return {"金币": (cost_gold, self.player.gold), "强化石": (cost_stone, stone_count)}

    def get_forge_cost(self, slot):
        level = self.player.equipment_slot_levels.get(slot, 0)
        cost_bone = level + 1
        cost_ingots = level + 1
        
        bone_count = self.player.inventory.get_item_count("骨粉")
        
        return {"骨粉": (cost_bone, bone_count), "元宝": (cost_ingots, self.player.ingots)}
        
    def draw_cost_tooltip(self, screen, rect, costs, title):
        font = self.renderer.small_font
        lines = [title, "所需材料:"]
        
        for name, (need, have) in costs.items():
            lines.append({"name": name, "need": need, "have": have})
            
        max_w = 0
        for line in lines:
            if isinstance(line, str):
                try: w = font.size(line)[0]
                except: w = 100
            else:
                txt = f"{line['name']}: {line['need']}({line['have']})"
                try: w = font.size(txt)[0]
                except: w = 100
            if w > max_w: max_w = w
            
        w = max_w + 20
        h = len(lines) * 20 + 10
        
        x, y = rect.centerx - w // 2, rect.top - h - 10
        if y < 0: y = rect.bottom + 10
        
        # Adjust horizontal
        if x < 0: x = 0
        if x + w > screen.get_width(): x = screen.get_width() - w
        
        # Draw Bg
        draw_rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(screen, (0, 0, 0, 200), draw_rect)
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        s.fill((0, 0, 0, 220))
        screen.blit(s, (x, y))
        pygame.draw.rect(screen, (200, 200, 200), draw_rect, 1)
        
        cur_y = y + 5
        for line in lines:
            if isinstance(line, str):
                txt = font.render(line, True, (255, 255, 255))
                screen.blit(txt, (x + 10, cur_y))
            else:
                part1 = f"{line['name']}: {line['need']}("
                c1 = (255, 255, 255)
                
                part2 = str(line['have'])
                c2 = (255, 0, 0) if line['have'] < line['need'] else (255, 255, 255)
                
                part3 = ")"
                c3 = (255, 255, 255)
                
                cur_x = x + 10
                
                t1 = font.render(part1, True, c1)
                screen.blit(t1, (cur_x, cur_y))
                cur_x += t1.get_width()
                
                t2 = font.render(part2, True, c2)
                screen.blit(t2, (cur_x, cur_y))
                cur_x += t2.get_width()
                
                t3 = font.render(part3, True, c3)
                screen.blit(t3, (cur_x, cur_y))
                
            cur_y += 20

    def draw_content(self, screen):
        slot_size = 40
        self.hover_item = None
        self.hover_rect = None
        self.hover_slot = None
        
        # Use existing self.slot_positions from __init__ (Restored original layout logic)
        for slot_key, pos in self.slot_positions.items():
            # Calculate absolute position
            x = self.rect.x + pos[0] - slot_size // 2
            y = self.rect.y + pos[1]
            
            item = self.player.equipment.get(slot_key)
            label = self.slot_names.get(slot_key, "")
            
            # Draw empty slot placeholder
            self.renderer.draw_item_slot(x, y, slot_size, None, label)
            
            # If item exists, draw item
            if item:
                self.renderer.draw_item_slot(x, y, slot_size, item)
            
            # Draw Forging Level if > 0
            slot_lvl = self.player.equipment_slot_levels.get(slot_key, 0)
            if slot_lvl > 0:
                 lvl_surf = self.renderer.small_font.render(f"+{slot_lvl}", True, (0, 255, 255))
                 screen.blit(lvl_surf, (x + 2, y + slot_size - 15))

            # Check hover
            mx, my = pygame.mouse.get_pos()
            if x <= mx <= x + slot_size and y <= my <= y + slot_size:
                self.hover_item = item
                self.hover_rect = pygame.Rect(x, y, slot_size, slot_size)
                self.hover_slot = slot_key
            
            # Highlight selected
            if (self.selected_item and item == self.selected_item) or (self.selected_slot == slot_key):
                pygame.draw.rect(screen, (255, 255, 0), (x-2, y-2, slot_size+4, slot_size+4), 2)

        # --- Enhance / Forge Buttons (Always Visible) ---
        # Draw at predefined positions in __init__
        
        # Enhance Button
        abs_enhance_rect = pygame.Rect(self.rect.x + self.enhance_btn_rect.x, self.rect.y + self.enhance_btn_rect.y, self.enhance_btn_rect.width, self.enhance_btn_rect.height)
        pygame.draw.rect(screen, (50, 50, 50), abs_enhance_rect, width=0, border_radius=3)
        pygame.draw.rect(screen, (200, 200, 200), abs_enhance_rect, width=1, border_radius=3)
        enh_txt = self.renderer.small_font.render("强化", True, (255, 255, 255))
        enh_txt_rect = enh_txt.get_rect(center=abs_enhance_rect.center)
        screen.blit(enh_txt, enh_txt_rect)
        
        # Forge Button
        abs_forge_rect = pygame.Rect(self.rect.x + self.forge_btn_rect.x, self.rect.y + self.forge_btn_rect.y, self.forge_btn_rect.width, self.forge_btn_rect.height)
        pygame.draw.rect(screen, (50, 50, 50), abs_forge_rect, width=0, border_radius=3)
        pygame.draw.rect(screen, (200, 200, 200), abs_forge_rect, width=1, border_radius=3)
        forge_txt = self.renderer.small_font.render("锻体", True, (255, 255, 255))
        forge_txt_rect = forge_txt.get_rect(center=abs_forge_rect.center)
        screen.blit(forge_txt, forge_txt_rect)

        # Check Button Hover for Cost Tooltip (Optional, good for UX)
        mx, my = pygame.mouse.get_pos()
        
        # Enhance Tooltip
        if abs_enhance_rect.collidepoint(mx, my):
             if self.selected_item:
                 costs = self.get_enhance_cost(self.selected_item)
                 if costs:
                     self.draw_cost_tooltip(screen, abs_enhance_rect, costs, "装备强化")
             else:
                 pass # Or show "Select item" tooltip?
                 
        # Forge Tooltip
        if abs_forge_rect.collidepoint(mx, my):
             if self.selected_slot:
                 costs = self.get_forge_cost(self.selected_slot)
                 if costs:
                     self.draw_cost_tooltip(screen, abs_forge_rect, costs, "装备锻体")

        # Draw Tooltip if hovering
        if self.hover_item and self.hover_rect:
            target_x = self.hover_rect.right
            target_y = self.hover_rect.bottom
            
            # Get slot level
            slot_lvl = 0
            if self.hover_slot:
                slot_lvl = self.player.equipment_slot_levels.get(self.hover_slot, 0)
                
            self.draw_tooltip(screen, self.hover_item, target_x, target_y, slot_level=slot_lvl)

        # --- Full Body Enhancement Level Display ---
        # Calculate Min Level
        min_level = 15
        equipped_count = 0
        total_slots = 0
        
        check_slots = ["weapon", "armor", "helmet", "necklace", "bracelet_l", "bracelet_r", "ring_l", "ring_r", "belt", "boots", "medal"]
        
        for slot in check_slots:
            total_slots += 1
            item = self.player.equipment.get(slot)
            if item:
                equipped_count += 1
                lvl = getattr(item, 'enhancement_level', 0)
                if lvl < min_level:
                    min_level = lvl
            else:
                min_level = 0
        
        # If not all slots are equipped, min_level is effectively 0 for "Full Body" concept usually,
        # or strictly following "lowest of worn equipment"?
        # User said: "depends on the lowest enhancement level of *all worn equipment*".
        # If I only wear 1 item +15, is full body +15?
        # "If *whole body* enhancement level *all* reach n".
        # This implies all slots must be filled.
        if equipped_count < len(check_slots):
            min_level = 0
            
        # Draw Text
        info_text = f"全身强化: +{min_level} (全属性+{min_level}%)"
        info_surf = self.renderer.small_font.render(info_text, True, (0, 255, 0)) # Green
        # Position: Top right or somewhere visible. 
        # Window title is at (10, 10). Window width 320.
        # Let's put it below title or at bottom.
        # Bottom has buttons.
        # Top right seems fine.
        info_rect = info_surf.get_rect(topright=(self.rect.width - 20, 15))
        screen.blit(info_surf, (self.rect.x + info_rect.x, self.rect.y + info_rect.y))

    def handle_click(self, pos, button=1):
        if hasattr(self, 'confirm_dialog') and self.confirm_dialog and self.confirm_dialog.visible:
            if self.confirm_dialog.handle_click(pos, button):
                return True
            return True

        if not super().handle_click(pos, button):
            return False
            
        # Check unequip
        slot_size = 40
        mx, my = pos
        
        # Check Buttons (Always Active)
        # Enhance
        if self.enhance_btn_rect:
            abs_enhance_rect = pygame.Rect(self.rect.x + self.enhance_btn_rect.x, self.rect.y + self.enhance_btn_rect.y, self.enhance_btn_rect.width, self.enhance_btn_rect.height)
            if abs_enhance_rect.collidepoint(mx, my):
                 if self.selected_item:
                     self.enhance_item(self.selected_item)
                 else:
                     if hasattr(self, 'game_engine') and self.game_engine:
                         self.game_engine.spawn_floating_text("请先选择要强化的装备", self.player.x, self.player.y, (255, 0, 0))
                 return True
                 
        # Forge
        if self.forge_btn_rect:
            abs_forge_rect = pygame.Rect(self.rect.x + self.forge_btn_rect.x, self.rect.y + self.forge_btn_rect.y, self.forge_btn_rect.width, self.forge_btn_rect.height)
            if abs_forge_rect.collidepoint(mx, my):
                 if self.selected_slot:
                     self.forge_slot()
                 else:
                     if hasattr(self, 'game_engine') and self.game_engine:
                         self.game_engine.spawn_floating_text("请先选择要锻体的部位", self.player.x, self.player.y, (255, 0, 0))
                 return True
        
        for slot_key, pos in self.slot_positions.items():
            x = self.rect.x + pos[0] - slot_size // 2
            y = self.rect.y + pos[1]
            rect = pygame.Rect(x, y, slot_size, slot_size)
            
            if rect.collidepoint(mx, my):
                if button == 1: # Left Click
                    # Select
                    item = self.player.equipment.get(slot_key)
                    # Always set selected_slot to allow forging empty slots (conceptually forging the body part)
                    self.selected_slot = slot_key
                    self.selected_item = item # Can be None
                elif button == 3: # Right click to unequip
                    self.player.unequip_item(slot_key)
                    if self.selected_item and self.selected_slot == slot_key:
                        self.selected_item = None
                        # Keep slot selected? No, unequip clears slot.
                        # self.selected_slot = None 
                return True
                
        return True

    def forge_slot(self):
        if not self.selected_slot: return
        
        current_level = self.player.equipment_slot_levels.get(self.selected_slot, 0)
        if current_level >= 15:
            # Maybe show a toast?
            return
            
        # Cost: (Level + 1) Bone Powder, (Level + 1) Ingots
        cost_bone = current_level + 1
        cost_ingots = current_level + 1
        
        # Check Resources
        # Check Bone Powder
        bone_count = self.player.inventory.get_item_count("骨粉")
                
        if bone_count < cost_bone:
            if hasattr(self, 'game_engine') and self.game_engine:
                 self.game_engine.spawn_floating_text("骨粉不足", self.player.x, self.player.y, (255, 0, 0))
            else:
                 print(f"Not enough Bone Powder. Need {cost_bone}, have {bone_count}")
            return
            
        if self.player.ingots < cost_ingots:
            if hasattr(self, 'game_engine') and self.game_engine:
                 self.game_engine.spawn_floating_text("元宝不足", self.player.x, self.player.y, (255, 0, 0))
            else:
                 print(f"Not enough Ingots. Need {cost_ingots}, have {self.player.ingots}")
            return
            
        # Confirm Dialog
        msg = f"消耗 {cost_bone} 骨粉 和 {cost_ingots} 元宝 进行锻体？\n当前等级: {current_level} -> {current_level + 1}\n基础属性 +1%"
        
        def on_confirm(opt):
            if opt == "确定":
                # Deduct Ingots
                self.player.ingots -= cost_ingots
                
                # Deduct Bone Powder
                remaining_cost = cost_bone
                for i in range(len(self.player.inventory.items)):
                    it = self.player.inventory.items[i]
                    if it and it.name == "骨粉":
                        if it.count >= remaining_cost:
                            it.count -= remaining_cost
                            remaining_cost = 0
                            if it.count == 0:
                                self.player.inventory.items[i] = None
                            break
                        else:
                            remaining_cost -= it.count
                            self.player.inventory.items[i] = None
                            
                # Upgrade
                self.player.equipment_slot_levels[self.selected_slot] = current_level + 1
                self.player.recalculate_stats()
                
                if hasattr(self, 'game_engine') and self.game_engine:
                    self.game_engine.spawn_floating_text("锻体成功", self.player.x, self.player.y, (0, 255, 0))
                else:
                    print(f"Forged {self.selected_slot} to level {current_level + 1}")
                
        self.confirm_dialog = DialogWindow(self.renderer, "锻体确认", msg, ["确定", "取消"], on_confirm)
        self.confirm_dialog.rect.center = (1024//2, 768//2)

    def draw(self, screen):
        super().draw(screen)
        if hasattr(self, 'confirm_dialog') and self.confirm_dialog and self.confirm_dialog.visible:
            self.confirm_dialog.draw(screen)

    def handle_click(self, pos, button=1):
        if hasattr(self, 'confirm_dialog') and self.confirm_dialog and self.confirm_dialog.visible:
            if self.confirm_dialog.handle_click(pos, button):
                return True
            return True

        if not super().handle_click(pos, button):
            return False
            
        # Check unequip
        slot_size = 40
        mx, my = pos
        
        # Check Buttons
        if self.selected_item: 
            # Enhance
            if self.enhance_btn_rect:
                abs_enhance_rect = pygame.Rect(self.rect.x + self.enhance_btn_rect.x, self.rect.y + self.enhance_btn_rect.y, self.enhance_btn_rect.width, self.enhance_btn_rect.height)
                if abs_enhance_rect.collidepoint(mx, my):
                     # Call the method if it exists, otherwise ignore or log error
                     if hasattr(self, 'enhance_item'):
                         self.enhance_item(self.selected_item)
                     else:
                         print("[ERROR] enhance_item not implemented in EquipmentWindow")
                     return True
                 
            # Forge
            if self.forge_btn_rect:
                abs_forge_rect = pygame.Rect(self.rect.x + self.forge_btn_rect.x, self.rect.y + self.forge_btn_rect.y, self.forge_btn_rect.width, self.forge_btn_rect.height)
                if abs_forge_rect.collidepoint(mx, my):
                     self.forge_slot()
                     return True
        
        for slot_key, rel_pos in self.slot_positions.items():
            x = self.rect.x + rel_pos[0] - slot_size // 2
            y = self.rect.y + rel_pos[1]
            rect = pygame.Rect(x, y, slot_size, slot_size)
            
            if rect.collidepoint(mx, my):
                if button == 1: # Left Click
                    # Select
                    item = self.player.equipment.get(slot_key)
                    if item:
                        self.selected_item = item
                        self.selected_slot = slot_key
                elif button == 3: # Right click to unequip
                    self.player.unequip_item(slot_key)
                    if self.selected_item and self.selected_slot == slot_key:
                        self.selected_item = None
                        self.selected_slot = None
                return True
                
        return True

    def enhance_item(self, item):
        if not item: return
        
        # Max level check
        current_enh = getattr(item, 'enhancement_level', 0)
        if current_enh >= 15:
            if hasattr(self, 'game_engine') and self.game_engine:
                 self.game_engine.spawn_floating_text("已达到最高强化等级", self.player.x, self.player.y, (255, 255, 0))
            return

        # Cost: (Level + 1) Upgrade Stones, (Level + 1) * 1000 Gold
        cost_stone = current_enh + 1
        cost_gold = (current_enh + 1) * 1000
        
        # Check Resources
        stone_count = self.player.inventory.get_item_count("强化石")
        
        if stone_count < cost_stone:
            if hasattr(self, 'game_engine') and self.game_engine:
                 self.game_engine.spawn_floating_text("强化石不足", self.player.x, self.player.y, (255, 0, 0))
            return
            
        if self.player.gold < cost_gold:
            if hasattr(self, 'game_engine') and self.game_engine:
                 self.game_engine.spawn_floating_text("金币不足", self.player.x, self.player.y, (255, 0, 0))
            return
            
        # Confirm Dialog
        msg = f"消耗 {cost_stone} 强化石 和 {cost_gold} 金币 进行强化？\n当前等级: +{current_enh} -> +{current_enh + 1}\n基础属性 +1点"
        
        def on_confirm(opt):
            if opt == "确定":
                # Double check resources (in case changed)
                stone_count_now = self.player.inventory.get_item_count("强化石")
                if self.player.gold < cost_gold:
                     if hasattr(self, 'game_engine') and self.game_engine:
                         self.game_engine.spawn_floating_text("金币不足", self.player.x, self.player.y, (255, 0, 0))
                     return
                if stone_count_now < cost_stone:
                     if hasattr(self, 'game_engine') and self.game_engine:
                         self.game_engine.spawn_floating_text("强化石不足", self.player.x, self.player.y, (255, 0, 0))
                     return

                # Deduct Gold
                self.player.gold -= cost_gold
                
                # Deduct Stones
                remaining_cost = cost_stone
                for i in range(len(self.player.inventory.items)):
                    it = self.player.inventory.items[i]
                    if it and it.name == "强化石":
                        if it.count >= remaining_cost:
                            it.count -= remaining_cost
                            remaining_cost = 0
                            if it.count == 0:
                                self.player.inventory.items[i] = None
                            break
                        else:
                            remaining_cost -= it.count
                            self.player.inventory.items[i] = None
                            
                # Upgrade
                item.enhancement_level = current_enh + 1
                self.player.recalculate_stats()
                
                if hasattr(self, 'game_engine') and self.game_engine:
                    self.game_engine.spawn_floating_text("强化成功", self.player.x, self.player.y, (0, 255, 0))
                
        self.confirm_dialog = DialogWindow(self.renderer, "装备强化", msg, ["确定", "取消"], on_confirm)
        self.confirm_dialog.rect.center = (1024//2, 768//2)


class InventoryWindow(UIWindow):
    def __init__(self, renderer, player):
        # 80% width and height
        w = int(1024 * 0.8)
        h = int(768 * 0.8)
        x = (1024 - w) // 2
        y = (768 - h) // 2
        super().__init__("背包", x, y, w, h, renderer)
        self.player = player
        self.game_engine = None # Assigned externally
        self.hover_item = None
        self.hover_rect = None
        
        self.recycle_window = None # Nested recycle window
        self.recycle_btn_rect = pygame.Rect(w - 150, h - 35, 60, 25) # Position next to Sort
        
        # Equipment Lock Button (Left of Recycle)
        self.lock_btn_rect = pygame.Rect(w - 220, h - 35, 60, 25)
        self.lock_mode = False # Toggle state for locking

        # Tabs
        self.current_tab = 0 # 0 to 3
        self.tabs = ["第一页", "第二页", "第三页", "第四页"]
        self.tab_rects = []
        
        # UI Elements
        self.slot_size = 40
        self.margin = 10
        
        # Calculate columns based on width
        self.grid_start_x = 20
        self.grid_start_y = 80 # Lowered to make room for tabs
        
        available_width = self.rect.width - 40 
        self.cols = available_width // (self.slot_size + self.margin)
        
        available_height = self.rect.height - 120 
        self.visible_rows = available_height // (self.slot_size + self.margin)
        
        # Ensure 150 items fit? 
        # 150 items per page. If we can't show all, we might need scrolling or smaller icons?
        # Requirement: "每一个背包标签页有独立的150个物品格"
        # 150 / cols = rows. 
        # If cols is say 18, rows needed is 9.
        # Let's see if 9 rows fit. 9 * 50 = 450px. Window height is ~600. Fits.
        
        self.grid_width = self.cols * (self.slot_size + self.margin) - self.margin
        self.grid_height = self.visible_rows * (self.slot_size + self.margin) - self.margin
        
        # Init Tabs Rects
        tab_w = 80
        tab_h = 30
        for i, title in enumerate(self.tabs):
            rect = pygame.Rect(self.rect.x + 20 + i * (tab_w + 5), self.rect.y + 40, tab_w, tab_h)
            self.tab_rects.append((rect, title))
        
        # Drag & Drop Item
        self.dragging_item_index = None # Index in inventory
        self.dragging_item = None # Item object
        self.dragging_icon_pos = None # (x, y) for drawing icon
        
        # Sort Button
        self.sort_btn_rect = pygame.Rect(self.rect.width - 80, self.rect.height - 35, 60, 25)
        
        # Confirmation Dialog (Nested)
        self.confirm_dialog = None
        
        # Auto Recycle Timer
        self.auto_recycle_timer = 10.0 # Seconds
        self.last_update_time = pygame.time.get_ticks()

    def update(self):
        # Update auto recycle timer logic moved to GameEngine to avoid duplication
        pass

    def perform_auto_recycle(self):
        # Logic moved to GameEngine.perform_auto_recycle
        pass

    def draw(self, screen):
        # self.update() # Removed to prevent double update if it was doing logic
        super().draw(screen)
        
        # Draw dragged item icon on top of everything
        if self.dragging_item and self.dragging_icon_pos:
            # Simple icon representation (text or small rect)
            mx, my = pygame.mouse.get_pos()
            # Center icon on mouse
            x = mx - self.slot_size // 2
            y = my - self.slot_size // 2
            self.renderer.draw_item_slot(x, y, self.slot_size, self.dragging_item)
            
        if self.confirm_dialog and self.confirm_dialog.visible:
            self.confirm_dialog.draw(screen)
            
        if self.recycle_window and self.recycle_window.visible:
            self.recycle_window.draw(screen)

    def handle_click(self, pos, button=1):
        # Check nested dialog first
        if self.confirm_dialog and self.confirm_dialog.visible:
            if self.confirm_dialog.handle_click(pos, button):
                return True
            # Modal: ignore other clicks if dialog is open
            return True
            
        if self.recycle_window and self.recycle_window.visible:
            if self.recycle_window.handle_click(pos, button):
                return True
            # Not strictly modal but let's prioritize it
            # Or allow closing by clicking outside? UIWindow handles close button.
            return True

        handled_by_base = super().handle_click(pos, button)
        if not handled_by_base:
             return False
             
        if not self.visible:
            return True

        # Adjust pos to window local
        mx, my = pos
        rel_x = mx - self.rect.x
        rel_y = my - self.rect.y
        
        # Check Tabs
        for i, (rect, title) in enumerate(self.tab_rects):
            if rect.collidepoint(mx, my):
                # Check unlock logic
                page_idx = i
                # Page 0 is always unlocked (unlocked_pages >= 1)
                # Page 1 requires unlocked_pages >= 2
                if page_idx + 1 > self.player.inventory.unlocked_pages:
                    # Locked, ask to unlock
                    cost = 50 # Example cost
                    msg = f"是否花费 {cost} 元宝解锁 {title}？"
                    def on_confirm(opt):
                        if opt == "确定":
                            if self.player.ingots >= cost:
                                if self.player.inventory.unlock_page("ingots", cost):
                                    self.player.ingots -= cost
                                    self.current_tab = page_idx
                            else:
                                # Show error dialog
                                # Use a small delay or just overwrite the current dialog reference
                                # We need to set it on the next frame or immediately?
                                # self.confirm_dialog is currently the one calling this callback.
                                # If we set self.confirm_dialog now, it replaces the old one.
                                self.confirm_dialog = DialogWindow(self.renderer, "提示", "元宝不足，无法解锁！", ["确定"], None)
                                self.confirm_dialog.rect.center = (1024//2, 768//2)
                    
                    self.confirm_dialog = DialogWindow(self.renderer, "解锁背包页", msg, ["确定", "取消"], on_confirm)
                    self.confirm_dialog.rect.center = (1024//2, 768//2) # Center on screen
                else:
                    self.current_tab = page_idx
                return True
        
        # Check Sort Button
        abs_sort_rect = pygame.Rect(self.rect.x + self.sort_btn_rect.x, self.rect.y + self.sort_btn_rect.y, self.sort_btn_rect.width, self.sort_btn_rect.height)
        if abs_sort_rect.collidepoint(mx, my):
            if self.lock_mode: return True # Disable sort in lock mode
            self.player.inventory.sort_items()
            return True
            
        # Check Recycle Button
        abs_recycle_rect = pygame.Rect(self.rect.x + self.recycle_btn_rect.x, self.rect.y + self.recycle_btn_rect.y, self.recycle_btn_rect.width, self.recycle_btn_rect.height)
        if abs_recycle_rect.collidepoint(mx, my):
            if self.lock_mode: return True # Disable recycle in lock mode
            # Open Recycle Window
            if not self.recycle_window:
                self.recycle_window = RecycleWindow(self.renderer, self.player, self.game_engine)
            else:
                self.recycle_window.game_engine = self.game_engine # Ensure updated engine
                
            self.recycle_window.visible = True
            # Center it
            self.recycle_window.rect.center = self.rect.center
            return True

        # Check Lock Button
        abs_lock_rect = pygame.Rect(self.rect.x + self.lock_btn_rect.x, self.rect.y + self.lock_btn_rect.y, self.lock_btn_rect.width, self.lock_btn_rect.height)
        if abs_lock_rect.collidepoint(mx, my):
             self.lock_mode = not self.lock_mode
             # Reset dragging if active?
             if self.dragging_item:
                 self.dragging_item = None
                 self.dragging_item_index = None
             return True

        # Check Grid Clicks
        # Only check visible area
        grid_abs_rect = pygame.Rect(self.rect.x + self.grid_start_x, self.rect.y + self.grid_start_y, self.grid_width, self.grid_height + self.margin) 
        if grid_abs_rect.collidepoint(mx, my):
            col = (rel_x - self.grid_start_x) // (self.slot_size + self.margin)
            row = (rel_y - self.grid_start_y) // (self.slot_size + self.margin)
            
            if 0 <= col < self.cols and 0 <= row < self.visible_rows:
                # Index within current page
                local_idx = row * self.cols + col
                
                if local_idx < self.player.inventory.page_size:
                    # Global index
                    global_idx = self.current_tab * self.player.inventory.page_size + local_idx
                    
                    if global_idx < self.player.inventory.capacity:
                        # Handle Item Click
                        if button == 1: # Left Click
                            
                            # Lock Mode Logic
                            if self.lock_mode:
                                item = self.player.inventory.items[global_idx]
                                if item and getattr(item, 'is_equipment', False):
                                    # Toggle lock
                                    item.locked = not getattr(item, 'locked', False)
                                    # Maybe show small feedback? Or icon update is enough.
                                return True

                            # Normal Logic
                            if self.dragging_item:
                                # Drop / Swap
                                if global_idx == self.dragging_item_index:
                                    self.dragging_item = None
                                    self.dragging_item_index = None
                                else:
                                    # Can only drop if slot is unlocked?
                                    # Actually, current logic allows dropping anywhere in unlocked pages.
                                    # Since we can only access unlocked pages via tabs, this check is implicit.
                                    self.player.inventory.move_item(self.dragging_item_index, global_idx)
                                    self.dragging_item = None
                                    self.dragging_item_index = None
                            else:
                                # Pick Up
                                item = self.player.inventory.items[global_idx]
                                if item:
                                    self.dragging_item = item
                                    self.dragging_item_index = global_idx
                                    self.dragging_icon_pos = (mx, my)
                                    
                        elif button == 3: # Right click
                            if self.dragging_item:
                                self.dragging_item = None
                                self.dragging_item_index = None
                            else:
                                # Use / Equip
                                item = self.player.inventory.items[global_idx]
                                if item:
                                    # Check type
                                    from src.systems.equipment.item import ItemType
                                    if item.item_type in [ItemType.CONSUMABLE, ItemType.SKILL_BOOK]:
                                        success, msg = self.player.use_item(item, global_idx)
                                        if success:
                                            if self.game_engine:
                                                self.game_engine.spawn_floating_text(msg, self.player.x, self.player.y, (0, 255, 0))
                                        else:
                                            # Show failure message
                                            if self.game_engine:
                                                self.game_engine.spawn_floating_text(msg, self.player.x, self.player.y, (255, 0, 0))
                                            else:
                                                print(msg)
                                    else:
                                        # Assume equipment
                                        # Special handling for Rings/Bracelets
                                        if item.item_type in [ItemType.RING, ItemType.BRACELET]:
                                            self.show_equip_selection_dialog(item)
                                            return True
                                            
                                        success, msg = self.player.equip_item(item)
                                        if not success:
                                            if self.game_engine:
                                                self.game_engine.spawn_ui_floating_text(msg, mx, my, (255, 0, 0))
                                            else:
                                                print(msg)
        
        return True

    def show_equip_selection_dialog(self, item):
        from src.systems.equipment.item import ItemType
        
        slot_l = "ring_l" if item.item_type == ItemType.RING else "bracelet_l"
        slot_r = "ring_r" if item.item_type == ItemType.RING else "bracelet_r"
        
        name_l = "左手"
        name_r = "右手"
        
        msg = f"请选择佩戴位置:\n{item.name}"
        
        def on_select(opt):
            target_slot = None
            if opt == name_l:
                target_slot = slot_l
            elif opt == name_r:
                target_slot = slot_r
                
            if target_slot:
                success, result_msg = self.player.equip_item(item, target_slot)
                if success:
                    if self.game_engine:
                        self.game_engine.spawn_floating_text("佩戴成功", self.player.x, self.player.y, (0, 255, 0))
                else:
                    if self.game_engine:
                        self.game_engine.spawn_floating_text(result_msg, self.player.x, self.player.y, (255, 0, 0))
        
        self.confirm_dialog = DialogWindow(self.renderer, "佩戴选择", msg, [name_l, name_r, "取消"], on_select)
        self.confirm_dialog.rect.center = (1024//2, 768//2)

    def draw_content(self, screen):
        self.hover_item = None
        self.hover_rect = None 
        
        # Draw Tabs
        for i, (rect, title) in enumerate(self.tab_rects):
            is_active = (i == self.current_tab)
            is_locked = (i + 1 > self.player.inventory.unlocked_pages)
            
            bg_color = (200, 200, 200)
            if is_active: bg_color = (255, 255, 255)
            elif is_locked: bg_color = (150, 150, 150)
            
            pygame.draw.rect(screen, bg_color, rect, border_radius=5)
            pygame.draw.rect(screen, (0, 0, 0), rect, width=1, border_radius=5)
            
            color = (0, 0, 0)
            if is_locked:
                title += " (锁)"
                color = (100, 100, 100)
                
            txt = self.renderer.small_font.render(title, True, color)
            txt_rect = txt.get_rect(center=rect.center)
            screen.blit(txt, txt_rect)

        # Draw Auto Recycle Status next to 4th tab (index 3)
        # 4th tab rect is self.tab_rects[3][0]
        if len(self.tab_rects) > 3:
            tab4_rect = self.tab_rects[3][0]
            status_x = tab4_rect.right + 20
            status_y = tab4_rect.centery
            
            prefix = "自动回收: "
            prefix_surf = self.renderer.small_font.render(prefix, True, (0, 0, 0))
            prefix_rect = prefix_surf.get_rect(midleft=(status_x, status_y))
            screen.blit(prefix_surf, prefix_rect)
            
            if self.game_engine and self.game_engine.auto_recycle_enabled:
                # Enabled: Black text, Countdown
                # Map engine timer (frames) to seconds
                # Engine runs at 60 FPS. Timer goes 0 -> 600.
                frames_remaining = max(0, 600 - self.game_engine.auto_recycle_timer)
                seconds_remaining = int(frames_remaining / 60) + 1
                
                status_text = f"{seconds_remaining}秒"
                color = (0, 0, 0)
            else:
                # Disabled: Red text, "未开启"
                status_text = "未开启"
                color = (255, 0, 0)
                
            status_surf = self.renderer.small_font.render(status_text, True, color)
            status_rect = status_surf.get_rect(midleft=(prefix_rect.right + 5, status_y))
            screen.blit(status_surf, status_rect)

        # Draw Grid for Current Page
        start_index = self.current_tab * self.player.inventory.page_size
        end_index = start_index + self.player.inventory.page_size
        
        # Determine if current page is locked (shouldn't happen if logic prevents switching)
        page_locked = (self.current_tab + 1 > self.player.inventory.unlocked_pages)
        
        for i in range(start_index, end_index):
            if i >= self.player.inventory.capacity: break
            
            local_idx = i - start_index
            row = local_idx // self.cols
            col = local_idx % self.cols
            
            x = self.rect.x + self.grid_start_x + col * (self.slot_size + self.margin)
            y = self.rect.y + self.grid_start_y + row * (self.slot_size + self.margin)
            
            # If row exceeds visible area, stop drawing (simple clipping)
            if row >= self.visible_rows: break
            
            # Determine content
            if page_locked:
                 self.renderer.draw_item_slot(x, y, self.slot_size, None, label="锁", locked=True)
            else:
                item = self.player.inventory.items[i]
                
                if item and self.dragging_item and i == self.dragging_item_index:
                    self.renderer.draw_item_slot(x, y, self.slot_size, None, locked=False) # Empty
                else:
                    self.renderer.draw_item_slot(x, y, self.slot_size, item, locked=False)
                
                # Hover
                mx, my = pygame.mouse.get_pos()
                if x <= mx <= x + self.slot_size and y <= my <= y + self.slot_size:
                    if not (self.confirm_dialog and self.confirm_dialog.visible):
                        if item and not self.dragging_item:
                            self.hover_item = item
                            self.hover_rect = pygame.Rect(x, y, self.slot_size, self.slot_size)
                
        # Draw Sort Button
        abs_sort_rect = pygame.Rect(self.rect.x + self.sort_btn_rect.x, self.rect.y + self.sort_btn_rect.y, self.sort_btn_rect.width, self.sort_btn_rect.height)
        pygame.draw.rect(screen, (150, 200, 150), abs_sort_rect, border_radius=3)
        pygame.draw.rect(screen, (0, 0, 0), abs_sort_rect, 1, border_radius=3)
        sort_txt = self.renderer.small_font.render("整理", True, (0, 0, 0))
        txt_rect = sort_txt.get_rect(center=abs_sort_rect.center)
        screen.blit(sort_txt, txt_rect)
        
        # Draw Recycle Button
        abs_recycle_rect = pygame.Rect(self.rect.x + self.recycle_btn_rect.x, self.rect.y + self.recycle_btn_rect.y, self.recycle_btn_rect.width, self.recycle_btn_rect.height)
        pygame.draw.rect(screen, (200, 100, 100), abs_recycle_rect, border_radius=3)
        pygame.draw.rect(screen, (0, 0, 0), abs_recycle_rect, 1, border_radius=3)
        rec_txt = self.renderer.small_font.render("回收", True, (0, 0, 0))
        rec_txt_rect = rec_txt.get_rect(center=abs_recycle_rect.center)
        screen.blit(rec_txt, rec_txt_rect)

        # Draw Lock Button
        abs_lock_rect = pygame.Rect(self.rect.x + self.lock_btn_rect.x, self.rect.y + self.lock_btn_rect.y, self.lock_btn_rect.width, self.lock_btn_rect.height)
        # Color based on state
        lock_bg = (255, 200, 0) if self.lock_mode else (200, 200, 200)
        pygame.draw.rect(screen, lock_bg, abs_lock_rect, border_radius=3)
        pygame.draw.rect(screen, (0, 0, 0), abs_lock_rect, 1, border_radius=3)
        lock_txt = self.renderer.small_font.render("装备锁定", True, (0, 0, 0))
        lock_txt_rect = lock_txt.get_rect(center=abs_lock_rect.center)
        screen.blit(lock_txt, lock_txt_rect)
        
        # Lock Mode Tooltip
        if self.lock_mode:
             mx, my = pygame.mouse.get_pos()
             # Follow mouse
             tooltip_bg = pygame.Surface((150, 30))
             tooltip_bg.fill((0, 0, 0))
             pygame.draw.rect(tooltip_bg, (255, 255, 255), tooltip_bg.get_rect(), 1)
             
             tip_txt = self.renderer.small_font.render("请点击要锁定的装备", True, (255, 255, 255))
             tooltip_bg.blit(tip_txt, (10, 5))
             
             screen.blit(tooltip_bg, (mx + 15, my + 15))

        # Draw Gold & Ingots
        gold_text = f"金币: {self.player.gold}"
        gold_surf = self.renderer.small_font.render(gold_text, True, (255, 215, 0))
        gold_rect = pygame.Rect(self.rect.x + 15, self.rect.y + self.rect.height - 35, 130, 25)
        pygame.draw.rect(screen, (40, 40, 40), gold_rect, border_radius=4)
        gold_txt_rect = gold_surf.get_rect(center=gold_rect.center)
        screen.blit(gold_surf, gold_txt_rect)
        
        ingot_text = f"元宝: {self.player.ingots}"
        ingot_surf = self.renderer.small_font.render(ingot_text, True, (255, 165, 0))
        ingot_rect = pygame.Rect(self.rect.x + 155, self.rect.y + self.rect.height - 35, 130, 25)
        pygame.draw.rect(screen, (40, 40, 40), ingot_rect, border_radius=4)
        ingot_txt_rect = ingot_surf.get_rect(center=ingot_rect.center)
        screen.blit(ingot_surf, ingot_txt_rect)
        
        # Draw Tooltip
        # If lock mode is active, do not show standard tooltips
        if self.lock_mode:
            pass # Tooltip is handled by the "following mouse" tooltip
        elif self.hover_item and self.hover_rect:
            target_x = self.hover_rect.right
            target_y = self.hover_rect.bottom
            
            # Comparison Logic
            diffs = None
            equipped_item = None
            slot = None
            slot_lvl = 0
            
            from src.systems.equipment.item import ItemType
            
            # Check if equipment
            if hasattr(self.hover_item, 'item_type'):
                itype = self.hover_item.item_type
                
                # Mapping
                compare_slots = []
                if itype == ItemType.WEAPON: compare_slots = ["weapon"]
                elif itype == ItemType.ARMOR: compare_slots = ["armor"]
                elif itype == ItemType.HELMET: compare_slots = ["helmet"]
                elif itype == ItemType.NECKLACE: compare_slots = ["necklace"]
                elif itype == ItemType.BELT: compare_slots = ["belt"]
                elif itype == ItemType.BOOTS: compare_slots = ["boots"]
                elif itype == ItemType.MEDAL: compare_slots = ["medal"]
                elif itype == ItemType.BRACELET: compare_slots = ["bracelet_l", "bracelet_r"]
                elif itype == ItemType.RING: compare_slots = ["ring_l", "ring_r"]
                
                if compare_slots:
                    # Default slot level (use first slot)
                    default_slot_lvl = self.player.equipment_slot_levels.get(compare_slots[0], 0)
                    
                    # Data collection
                    primary_diffs = None
                    left_diffs = None
                    right_diffs = None
                    equipped_tips_data = [] # List of (item, slot_lvl, title, lines, w, h)
                    
                    stat_map = {
                        "attack": "攻击", "defense": "防御", "magic": "魔法",
                        "taoism": "道术", "magic_defense": "魔防", "hp": "生命",
                        "mp": "魔法", "accuracy": "准确", "dodge": "敏捷",
                        "crit": "暴击", "luck": "幸运"
                    }

                    for slot in compare_slots:
                        slot_lvl = self.player.equipment_slot_levels.get(slot, 0)
                        eq_item = self.player.equipment.get(slot)
                        
                        if eq_item:
                            # Calculate Diffs
                            current_diffs = {'gains': [], 'losses': []}
                            
                            all_keys = set(self.hover_item.stats.keys()) | set(eq_item.stats.keys())
                            for k in all_keys:
                                # New Item Effective Stats
                                base_new = self.hover_item.stats.get(k, 0)
                                item_enh_new = getattr(self.hover_item, 'enhancement_level', 0)
                                item_bonus_new = item_enh_new
                                slot_bonus_new = int(base_new * slot_lvl * 0.01)
                                if slot_lvl > 0 and slot_bonus_new < 1: slot_bonus_new = 1
                                val_new = base_new + item_bonus_new + slot_bonus_new

                                # Old Item Effective Stats
                                base_old = eq_item.stats.get(k, 0)
                                item_enh_old = getattr(eq_item, 'enhancement_level', 0)
                                item_bonus_old = item_enh_old
                                slot_bonus_old = int(base_old * slot_lvl * 0.01)
                                if slot_lvl > 0 and slot_bonus_old < 1: slot_bonus_old = 1
                                val_old = base_old + item_bonus_old + slot_bonus_old
                                
                                diff = val_new - val_old
                                if diff != 0:
                                    cn_key = stat_map.get(k, k)
                                    sign = "+" if diff > 0 else ""
                                    line = f"{cn_key} {sign}{diff}"
                                    if diff > 0: current_diffs['gains'].append(line)
                                    else: current_diffs['losses'].append(line)
                            
                            # Store diffs for dual mode construction or single mode
                            if slot.endswith('_l'): left_diffs = current_diffs
                            elif slot.endswith('_r'): right_diffs = current_diffs
                            else: primary_diffs = current_diffs
                                
                            # Prepare title
                            if slot.endswith('_l'): title = "当前穿戴(左)"
                            elif slot.endswith('_r'): title = "当前穿戴(右)"
                            else: title = "当前穿戴"
                            
                            # Prepare lines
                            lines = self._prepare_tooltip_lines(eq_item, show_usage=False, header_text=title, slot_level=slot_lvl)
                            w, h = self._calculate_tooltip_dim(lines)
                            
                            equipped_tips_data.append({
                                'item': eq_item,
                                'slot_lvl': slot_lvl,
                                'title': title,
                                'lines': lines,
                                'w': w,
                                'h': h
                            })

                    # Construct dual mode diffs if applicable
                    if len(compare_slots) > 1:
                         if left_diffs or right_diffs:
                             primary_diffs = {
                                 'dual_mode': True,
                                 'left': left_diffs if left_diffs else {'gains':[], 'losses':[]},
                                 'right': right_diffs if right_diffs else {'gains':[], 'losses':[]}
                             }
                         else:
                             primary_diffs = None

                    # --- Calculate Tooltip Layout ---
                    
                    # 1. Prepare Hover Item Lines
                    inv_lines = self._prepare_tooltip_lines(self.hover_item, primary_diffs, slot_level=default_slot_lvl)
                    inv_w, inv_h = self._calculate_tooltip_dim(inv_lines)
                    
                    # 2. Determine Position
                    screen_w = screen.get_width()
                    screen_h = screen.get_height()
                    
                    target_x = self.hover_rect.right
                    target_y = self.hover_rect.bottom
                    
                    # Default Inv Position: Right of item
                    inv_x = target_x
                    
                    # Vertical Check
                    inv_y = target_y
                    if inv_y + inv_h > screen_h:
                        inv_y = screen_h - inv_h - 10
                    
                    # Layout Logic
                    if len(equipped_tips_data) == 2:
                        # Special Dual Layout: Left Tip - Inv Tip - Right Tip
                        left_data = equipped_tips_data[0]
                        right_data = equipped_tips_data[1]
                        
                        # Calculate ideal positions centered on Inv
                        
                        # Check if Inv fits on right
                        if inv_x + inv_w > screen_w:
                            # Inv doesn't fit on right, move Inv to left of slot
                            inv_x = self.hover_rect.left - inv_w
                            
                        # Now we have Inv pos.
                        # Calculate L and R relative to Inv (Tight layout, no spacing)
                        l_x = inv_x - left_data['w']
                        r_x = inv_x + inv_w
                        
                        # Check Boundaries
                        l_ok = (l_x >= 0)
                        r_ok = (r_x + right_data['w'] <= screen_w)
                        
                        final_l_x = l_x
                        final_r_x = r_x
                        
                        if not l_ok:
                            # Left doesn't fit on left side.
                            # Move Left to Right side? -> Inv | L | R
                            final_l_x = inv_x + inv_w
                            final_r_x = final_l_x + left_data['w']
                            
                            # Check if they fit on right
                            if final_r_x + right_data['w'] > screen_w:
                                # Doesn't fit on right either.
                                # Try moving everything left? -> L | R | Inv (Inv at left of slot)
                                # But we already set Inv pos.
                                # Maybe force Inv to left of slot if it was on right?
                                if inv_x > self.hover_rect.left:
                                     inv_x = self.hover_rect.left - inv_w
                                     # Re-calc L | Inv | R
                                     final_l_x = inv_x - left_data['w']
                                     final_r_x = inv_x + inv_w
                                     
                                     if final_l_x < 0:
                                         # Still no space on left for L.
                                         # Try L | R | Inv
                                         final_r_x = inv_x - right_data['w']
                                         final_l_x = final_r_x - left_data['w']
                        
                        elif not r_ok:
                            # Right doesn't fit on right side.
                            # Move Right to Left side? -> L | R | Inv
                            final_r_x = inv_x - right_data['w']
                            final_l_x = final_r_x - left_data['w']
                            
                            # Check if they fit on left
                            if final_l_x < 0:
                                # Doesn't fit on left either.
                                # Move Inv to Left of slot?
                                if inv_x > self.hover_rect.left:
                                    inv_x = self.hover_rect.left - inv_w
                                    # Try L | Inv | R again
                                    final_l_x = inv_x - left_data['w']
                                    final_r_x = inv_x + inv_w
                                    
                                    if final_r_x + right_data['w'] > screen_w:
                                        # Still no fit. Try Inv | L | R
                                        final_l_x = inv_x + inv_w
                                        final_r_x = final_l_x + left_data['w']

                        # Apply Y align
                        left_data['x'] = final_l_x
                        left_data['y'] = inv_y
                        right_data['x'] = final_r_x
                        right_data['y'] = inv_y
                        
                        # Handle vertical overflow for equipped items
                        if left_data['y'] + left_data['h'] > screen_h: left_data['y'] = screen_h - left_data['h'] - 10
                        if right_data['y'] + right_data['h'] > screen_h: right_data['y'] = screen_h - right_data['h'] - 10

                    else:
                        # Single or No Equipped Item (Original Logic)
                        max_eq_w = 0
                        total_eq_h = 0
                        for data in equipped_tips_data:
                            if data['w'] > max_eq_w: max_eq_w = data['w']
                            total_eq_h += data['h'] + 10
                        if total_eq_h > 0: total_eq_h -= 10
                        
                        eq_start_x = inv_x + inv_w # Tight layout
                        
                        # Check Inv Fit
                        if inv_x + inv_w > screen_w:
                            inv_x = self.hover_rect.left - inv_w
                            eq_start_x = inv_x - max_eq_w # Tight layout
                        
                        # Check Eq Fit (if originally on right)
                        if equipped_tips_data:
                            if inv_x < self.hover_rect.left:
                                # Inv is on Left. Eq on Left of Inv.
                                eq_start_x = inv_x - max_eq_w
                            else:
                                # Inv is on Right. Eq on Right of Inv.
                                if eq_start_x + max_eq_w > screen_w:
                                    # Eq doesn't fit Right. Move to Left of Item?
                                    eq_start_x = self.hover_rect.left - max_eq_w
                                    
                                    # If Eq overlaps Inv (because Inv is on Left?), check overlap
                                    # Actually we just decided Inv pos above.
                                    pass

                        # Clamp Left
                        if inv_x < 0: inv_x = 0
                        
                        # Set positions
                        current_eq_y = inv_y
                        for data in equipped_tips_data:
                            data['x'] = eq_start_x
                            if data['x'] < 0: data['x'] = 0 # Clamp
                            data['y'] = current_eq_y
                            
                            # Vertical check
                            if data['y'] + data['h'] > screen_h:
                                data['y'] = screen_h - data['h'] - 10
                                # Align inv if needed?
                                if inv_y > data['y']: inv_y = data['y']
                                else: data['y'] = inv_y
                                
                            current_eq_y += data['h'] + 10

                    # 3. Draw
                    self.draw_tooltip(screen, self.hover_item, inv_x, inv_y, primary_diffs, slot_level=default_slot_lvl)
                    
                    for data in equipped_tips_data:
                        self.draw_tooltip(screen, data['item'], data['x'], data['y'], show_usage=False, header_text=data['title'], slot_level=data['slot_lvl'])

    def update_scrollbar(self):
        pass # Removed
    def handle_scroll(self, dy):
        pass # Removed

class SettingsWindow(UIWindow):
    def __init__(self, renderer, game_engine):
        super().__init__("游戏设置", 400, 150, 300, 350, renderer)
        self.game_engine = game_engine
        
        # Auto Save
        self.as_input_rect = pygame.Rect(self.rect.x + 160, self.rect.y + 60, 80, 25)
        self.as_checkbox_rect = pygame.Rect(self.rect.x + 160, self.rect.y + 100, 20, 20)
        
        # Auto Potion
        # HP Threshold
        self.hp_input_rect = pygame.Rect(self.rect.x + 160, self.rect.y + 150, 80, 25)
        # MP Threshold
        self.mp_input_rect = pygame.Rect(self.rect.x + 160, self.rect.y + 190, 80, 25)
        # Enabled Checkbox
        self.ap_checkbox_rect = pygame.Rect(self.rect.x + 160, self.rect.y + 230, 20, 20)
        
        self.active_input = None # None, "as_interval", "hp_threshold", "mp_threshold"
        
        # Init inputs from data
        self.input_texts = {
            "as_interval": str(self.game_engine.auto_save_interval),
            "hp_threshold": str(self.game_engine.player.auto_potion_settings.get("hp_threshold", 70)),
            "mp_threshold": str(self.game_engine.player.auto_potion_settings.get("mp_threshold", 30))
        }

    def draw_content(self, screen):
        font = self.renderer.cn_font
        small_font = self.renderer.small_font
        
        # --- Auto Save Section ---
        # Label for interval
        lbl_interval = font.render("自动存档间隔(分):", True, (0, 0, 0))
        screen.blit(lbl_interval, (self.rect.x + 20, self.rect.y + 65))
        
        # Input Box
        color = (255, 255, 255) if self.active_input == "as_interval" else (240, 240, 240)
        pygame.draw.rect(screen, color, self.as_input_rect)
        pygame.draw.rect(screen, (0, 0, 0), self.as_input_rect, 1)
        
        txt_surf = font.render(self.input_texts["as_interval"], True, (0, 0, 0))
        screen.blit(txt_surf, (self.as_input_rect.x + 5, self.as_input_rect.y + 5))
        
        # Label for Checkbox
        lbl_enable = font.render("开启自动存档:", True, (0, 0, 0))
        screen.blit(lbl_enable, (self.rect.x + 20, self.rect.y + 100))
        
        # Checkbox
        pygame.draw.rect(screen, (255, 255, 255), self.as_checkbox_rect)
        pygame.draw.rect(screen, (0, 0, 0), self.as_checkbox_rect, 1)
        if self.game_engine.auto_save_enabled:
            pygame.draw.line(screen, (0, 0, 0), (self.as_checkbox_rect.x + 4, self.as_checkbox_rect.y + 10), (self.as_checkbox_rect.x + 8, self.as_checkbox_rect.y + 16), 2)
            pygame.draw.line(screen, (0, 0, 0), (self.as_checkbox_rect.x + 8, self.as_checkbox_rect.y + 16), (self.as_checkbox_rect.x + 16, self.as_checkbox_rect.y + 4), 2)
            
        pygame.draw.line(screen, (200, 200, 200), (self.rect.x + 20, self.rect.y + 135), (self.rect.right - 20, self.rect.y + 135), 2)
        
        # --- Auto Potion Section ---
        # HP Threshold
        lbl_hp = font.render("HP保护百分比:", True, (0, 0, 0))
        screen.blit(lbl_hp, (self.rect.x + 20, self.rect.y + 155))
        
        color = (255, 255, 255) if self.active_input == "hp_threshold" else (240, 240, 240)
        pygame.draw.rect(screen, color, self.hp_input_rect)
        pygame.draw.rect(screen, (0, 0, 0), self.hp_input_rect, 1)
        
        txt_surf = font.render(self.input_texts["hp_threshold"], True, (0, 0, 0))
        screen.blit(txt_surf, (self.hp_input_rect.x + 5, self.hp_input_rect.y + 5))
        
        # MP Threshold
        lbl_mp = font.render("MP保护百分比:", True, (0, 0, 0))
        screen.blit(lbl_mp, (self.rect.x + 20, self.rect.y + 195))
        
        color = (255, 255, 255) if self.active_input == "mp_threshold" else (240, 240, 240)
        pygame.draw.rect(screen, color, self.mp_input_rect)
        pygame.draw.rect(screen, (0, 0, 0), self.mp_input_rect, 1)
        
        txt_surf = font.render(self.input_texts["mp_threshold"], True, (0, 0, 0))
        screen.blit(txt_surf, (self.mp_input_rect.x + 5, self.mp_input_rect.y + 5))
        
        # Enabled Checkbox
        lbl_ap_enable = font.render("开启自动喝药:", True, (0, 0, 0))
        screen.blit(lbl_ap_enable, (self.rect.x + 20, self.rect.y + 230))
        
        pygame.draw.rect(screen, (255, 255, 255), self.ap_checkbox_rect)
        pygame.draw.rect(screen, (0, 0, 0), self.ap_checkbox_rect, 1)
        if self.game_engine.player.auto_potion_settings.get("enabled", False):
            pygame.draw.line(screen, (0, 0, 0), (self.ap_checkbox_rect.x + 4, self.ap_checkbox_rect.y + 10), (self.ap_checkbox_rect.x + 8, self.ap_checkbox_rect.y + 16), 2)
            pygame.draw.line(screen, (0, 0, 0), (self.ap_checkbox_rect.x + 8, self.ap_checkbox_rect.y + 16), (self.ap_checkbox_rect.x + 16, self.ap_checkbox_rect.y + 4), 2)

        # Info
        info = small_font.render("关闭窗口或点击X即可保存设置", True, (100, 100, 100))
        screen.blit(info, (self.rect.x + 20, self.rect.y + 280))
        
        info2 = small_font.render("注: 自动使用背包中可用的恢复药水", True, (100, 100, 100))
        screen.blit(info2, (self.rect.x + 20, self.rect.y + 300))

    def handle_click(self, pos, button=1):
        if not super().handle_click(pos, button):
            self.active_input = None
            return False
            
        # Check Input Boxes
        if self.as_input_rect.collidepoint(pos):
            self.active_input = "as_interval"
        elif self.hp_input_rect.collidepoint(pos):
            self.active_input = "hp_threshold"
        elif self.mp_input_rect.collidepoint(pos):
            self.active_input = "mp_threshold"
        else:
            self.active_input = None
            
        # Check Checkboxes
        if self.as_checkbox_rect.collidepoint(pos):
            self.game_engine.auto_save_enabled = not self.game_engine.auto_save_enabled
            
        if self.ap_checkbox_rect.collidepoint(pos):
            enabled = self.game_engine.player.auto_potion_settings.get("enabled", False)
            self.game_engine.player.auto_potion_settings["enabled"] = not enabled
            
        return True

    def handle_keydown(self, event):
        if not self.visible or not self.active_input:
            return False
            
        current_text = self.input_texts[self.active_input]
            
        if event.key == pygame.K_BACKSPACE:
            current_text = current_text[:-1]
        elif event.unicode.isdigit():
            current_text += event.unicode
            # Limit length
            if len(current_text) > 3:
                current_text = current_text[:3]
                
        self.input_texts[self.active_input] = current_text
        
        # Apply changes immediately
        try:
            val = int(current_text)
            if self.active_input == "as_interval":
                if val > 0: self.game_engine.auto_save_interval = val
            elif self.active_input == "hp_threshold":
                if 0 <= val <= 100: self.game_engine.player.auto_potion_settings["hp_threshold"] = val
            elif self.active_input == "mp_threshold":
                if 0 <= val <= 100: self.game_engine.player.auto_potion_settings["mp_threshold"] = val
        except:
            pass
                
        return True

class DialogWindow(UIWindow):
    def __init__(self, renderer, title, text, options=None, callback=None, show_checkbox=False, checkbox_text="", on_checkbox_toggle=None, show_close_button=True, layout="horizontal"):
        super().__init__(title, 200, 500, 624, 200, renderer, show_close_button) # Increased height
        self.text = text
        self.options = options or ["继续"]
        self.callback = callback
        self.visible = True
        self.layout = layout
        
        # Checkbox
        self.show_checkbox = show_checkbox
        self.checkbox_text = checkbox_text
        self.on_checkbox_toggle = on_checkbox_toggle
        self.checkbox_checked = False
        self.checkbox_rect = None
        if self.show_checkbox:
            # Place above buttons
            self.checkbox_rect = pygame.Rect(20, 120, 20, 20) # Relative
        
        # Options rects (relative to window)
        self.option_rects = []
        btn_width = 80
        btn_height = 30
        
        if self.layout == "matrix":
            # Grid Layout (e.g., for Map Selection)
            # Increase window height to fit options if needed
            cols = 3
            btn_width = 180 # Wider buttons for map names
            spacing_x = 10
            spacing_y = 10
            
            start_x = (self.rect.width - (cols * btn_width + (cols - 1) * spacing_x)) // 2
            start_y = 100 # Start lower (adjusted)
            
            rows = (len(self.options) + cols - 1) // cols
            needed_height = start_y + rows * (btn_height + spacing_y) + 30
            
            if needed_height > self.rect.height:
                self.rect.height = needed_height
                
            # Center on screen for Matrix layout
            self.rect.center = (1024 // 2, 768 // 2)
                
            for i, opt in enumerate(self.options):
                col = i % cols
                row = i // cols
                
                x = start_x + col * (btn_width + spacing_x)
                y = start_y + row * (btn_height + spacing_y)
                
                rect = pygame.Rect(x, y, btn_width, btn_height)
                self.option_rects.append((rect, opt))
                
        else:
            # Horizontal Layout (Standard)
            # Calculate total width of buttons
            total_btn_width = len(self.options) * (btn_width + 10) - 10
            start_x = (self.rect.width - total_btn_width) // 2 # Center buttons
            y = self.rect.height - 40
            
            for i, opt in enumerate(self.options):
                # Store RELATIVE rect
                rect = pygame.Rect(start_x + i * (btn_width + 10), y, btn_width, btn_height)
                self.option_rects.append((rect, opt))

    def draw_content(self, screen):
        # Draw Text (multiline)
        font = self.renderer.cn_font
        small_font = self.renderer.small_font
        
        y = self.rect.y + 40
        
        # Check if text is a list of segments (Rich Text)
        if isinstance(self.text, list):
            # Rich Text Rendering
            # Example: [{"text": "Hello", "color": (0,0,0), "bold": False}, ...]
            
            # Simple line wrapping
            current_x = self.rect.x + 20
            start_x = self.rect.x + 20
            max_width = self.rect.width - 40
            
            for segment in self.text:
                seg_text = segment.get("text", "")
                seg_color = segment.get("color", (0, 0, 0))
                is_bold = segment.get("bold", False)
                
                # We need to process character by character or word by word to handle wrapping
                # Simplest is char by char
                
                for char in seg_text:
                    if char == '\n':
                        current_x = start_x
                        y += 20
                        continue
                        
                    char_w = font.size(char)[0]
                    if current_x + char_w > start_x + max_width:
                        current_x = start_x
                        y += 20
                    
                    # Render char
                    txt_surf = font.render(char, True, seg_color)
                    screen.blit(txt_surf, (current_x, y))
                    
                    if is_bold:
                        screen.blit(txt_surf, (current_x + 1, y)) # Fake bold
                        
                    current_x += char_w
            
            y += 20 # Add padding after text
            
        else:
            # Legacy String Rendering
            lines = []
            
            # Split by explicit newlines first
            raw_lines = self.text.split('\n')
            
            for raw_line in raw_lines:
                current_line = ""
                for char in raw_line:
                    if font.size(current_line + char)[0] > self.rect.width - 40:
                        lines.append(current_line)
                        current_line = char
                    else:
                        current_line += char
                lines.append(current_line)
            
            for line in lines:
                txt = font.render(line, True, (0, 0, 0))
                screen.blit(txt, (self.rect.x + 20, y))
                y += 20
            
        # Draw Checkbox
        if self.show_checkbox and self.checkbox_rect:
            abs_check_rect = pygame.Rect(self.rect.x + self.checkbox_rect.x, self.rect.y + self.checkbox_rect.y, 20, 20)
            pygame.draw.rect(screen, (255, 255, 255), abs_check_rect)
            pygame.draw.rect(screen, (0, 0, 0), abs_check_rect, 1)
            
            if self.checkbox_checked:
                pygame.draw.line(screen, (0, 0, 0), (abs_check_rect.x + 4, abs_check_rect.y + 10), (abs_check_rect.x + 8, abs_check_rect.y + 16), 2)
                pygame.draw.line(screen, (0, 0, 0), (abs_check_rect.x + 8, abs_check_rect.y + 16), (abs_check_rect.x + 16, abs_check_rect.y + 4), 2)
                
            if self.checkbox_text:
                lbl = small_font.render(self.checkbox_text, True, (0, 0, 0))
                screen.blit(lbl, (abs_check_rect.right + 10, abs_check_rect.y + 2))
            
        # Draw Options
        for rel_rect, label in self.option_rects:
            # Convert to absolute position for drawing
            abs_rect = pygame.Rect(self.rect.x + rel_rect.x, self.rect.y + rel_rect.y, rel_rect.width, rel_rect.height)
            
            pygame.draw.rect(screen, (200, 200, 200), abs_rect, border_radius=5)
            pygame.draw.rect(screen, (0, 0, 0), abs_rect, width=1, border_radius=5)
            txt = font.render(label, True, (0, 0, 0))
            txt_rect = txt.get_rect(center=abs_rect.center)
            screen.blit(txt, txt_rect)

    def handle_click(self, pos, button=1):
        if not self.visible: return False
        
        # Check close button first (if inherited from UIWindow, though Dialog usually doesn't have X if modal?)
        # UIWindow has close button.
        if self.close_btn_rect.collidepoint(pos):
            self.visible = False
            return True
            
        mx, my = pos
        
        # Check Checkbox
        if self.show_checkbox and self.checkbox_rect:
             # Calculate absolute position for checkbox
             abs_check_rect = pygame.Rect(self.rect.x + self.checkbox_rect.x, self.rect.y + self.checkbox_rect.y, self.checkbox_rect.width, self.checkbox_rect.height)
             if abs_check_rect.collidepoint(mx, my):
                 self.checkbox_checked = not self.checkbox_checked
                 if self.on_checkbox_toggle:
                     self.on_checkbox_toggle(self.checkbox_checked)
                 return True
        
        for rel_rect, label in self.option_rects:
            # Calculate absolute position for option buttons
            abs_rect = pygame.Rect(self.rect.x + rel_rect.x, self.rect.y + rel_rect.y, rel_rect.width, rel_rect.height)
            
            if abs_rect.collidepoint(mx, my):
                if self.callback:
                    self.callback(label)
                self.visible = False # Auto close on click
                return True
        return self.rect.collidepoint(pos)

class ShopWindow(UIWindow):
    def __init__(self, renderer, player):
        super().__init__("商店", 250, 100, 500, 500, renderer)
        self.player = player
        self.tabs = ["药店", "书店"]
        self.current_tab = 0
        self.tab_rects = []
        
        # Init Tabs
        tab_w = 100
        tab_h = 30
        for i, title in enumerate(self.tabs):
            rect = pygame.Rect(self.rect.x + 20 + i * (tab_w + 10), self.rect.y + 40, tab_w, tab_h)
            self.tab_rects.append((rect, title))
            
        # Items
        self.items = {
            "药店": [
                "金创药(小)", "金创药(中)", "强效金创药",
                "魔法药(小)", "魔法药(中)", "强效魔法药",
                "太阳水", "万年雪霜"
            ],
            "书店": [
                # Warrior
                "基本剑术", "攻杀剑术", "刺杀剑术", "半月弯刀", "野蛮冲撞", "烈火剑法",
                # Mage
                "火球术", "抗拒火环", "诱惑之光", "地狱火", "雷电术", "瞬息移动", "大火球", 
                "爆裂火焰", "火墙", "疾光电影", "地狱雷光", "魔法盾", "圣言术", "冰咆哮",
                # Taoist
                "治愈术", "精神力战法", "施毒术", "灵魂火符", "幽灵盾", "神圣战甲术", "困魔咒", "群体治愈术", "召唤神兽"
            ]
        }
        
        self.hover_item = None
        self.hover_rect = None
        self.confirm_dialog = None
        
        # Pagination & Grid
        self.page = 0
        self.items_per_page = 9 # 3x3
        self.cols = 3
        self.rows = 3
        
        # Pagination Buttons
        self.prev_btn_rect = pygame.Rect(0, 0, 60, 30)
        self.next_btn_rect = pygame.Rect(0, 0, 60, 30)
        
        # Quantity Input (Permanent)
        self.quantity_input_text = "1"
        self.quantity_input_rect = pygame.Rect(0, 0, 80, 30)
        self.is_input_active = False

    def handle_input(self, event):
        if self.visible:
            # Handle Modal Input first
            if hasattr(self, 'confirm_dialog') and self.confirm_dialog and self.confirm_dialog.visible:
                 if hasattr(self.confirm_dialog, 'handle_input'):
                     return self.confirm_dialog.handle_input(event)
            
            # Handle Permanent Input
            if self.is_input_active and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self.quantity_input_text = self.quantity_input_text[:-1]
                    if not self.quantity_input_text: self.quantity_input_text = ""
                elif event.key == pygame.K_RETURN:
                    self.is_input_active = False # unfocus
                    pygame.key.stop_text_input()
                elif event.key == pygame.K_ESCAPE:
                    self.is_input_active = False
                    pygame.key.stop_text_input()
                else:
                    if event.unicode.isdigit():
                         if len(self.quantity_input_text) < 3:
                             self.quantity_input_text += event.unicode
                return True
        return False
        
    def draw(self, screen):
        # Override to draw modal dialog on top
        super().draw(screen)
        # Ensure InputDialog is drawn on top if active
        if hasattr(self, 'confirm_dialog') and self.confirm_dialog and self.confirm_dialog.visible:
            self.confirm_dialog.draw(screen)

    def draw_content(self, screen):
        font = self.renderer.cn_font
        small_font = self.renderer.small_font
        
        # Draw Tabs
        for i, (rect, title) in enumerate(self.tab_rects):
            is_active = (i == self.current_tab)
            bg_color = (200, 200, 200)
            if is_active: bg_color = (255, 255, 255)
            
            pygame.draw.rect(screen, bg_color, rect, border_radius=5)
            pygame.draw.rect(screen, (0, 0, 0), rect, width=1, border_radius=5)
            
            txt = font.render(title, True, (0, 0, 0))
            txt_rect = txt.get_rect(center=rect.center)
            screen.blit(txt, txt_rect)
            
        # --- Grid Layout ---
        current_cat = self.tabs[self.current_tab]
        all_items = self.items.get(current_cat, [])
        
        # Pagination Logic
        total_pages = (len(all_items) + self.items_per_page - 1) // self.items_per_page
        if self.page >= total_pages: self.page = max(0, total_pages - 1)
        
        start_idx = self.page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(all_items))
        page_items = all_items[start_idx:end_idx]
        
        # Grid Config
        grid_x = self.rect.x + 20
        grid_y = self.rect.y + 80
        cell_w = 140
        cell_h = 100
        gap_x = 10
        gap_y = 10
        
        from src.systems.equipment.database import EQUIPMENT_DB
        from src.systems.equipment.item import Item
        
        self.buy_buttons = [] # Reset
        self.hover_item = None
        self.hover_rect = None
        
        for idx, name in enumerate(page_items):
            row = idx // self.cols
            col = idx % self.cols
            
            cx = grid_x + col * (cell_w + gap_x)
            cy = grid_y + row * (cell_h + gap_y)
            cell_rect = pygame.Rect(cx, cy, cell_w, cell_h)
            
            # Draw Cell
            pygame.draw.rect(screen, (245, 245, 245), cell_rect, border_radius=5)
            pygame.draw.rect(screen, (200, 200, 200), cell_rect, width=1, border_radius=5)
            
            if name in EQUIPMENT_DB:
                data = EQUIPMENT_DB[name]
                
                # Mock Item for display
                class DummyItem:
                    def __init__(self, n, d):
                        self.name = n
                        from src.systems.equipment.item import ItemQuality
                        self.quality = ItemQuality.NORMAL 
                        self.item_type = d["type"]
                        self.stats = d.get("stats", {})
                        self.price = d.get("price", 0)
                        self.min_level = d.get("level", 1)
                        self.weight = d.get("weight", 1)
                
                d_item = DummyItem(name, data)
                
                # Icon (Centered Top)
                self.renderer.draw_item_slot(cx + (cell_w - 40)//2, cy + 10, 40, d_item)
                
                # Name (Below Icon)
                name_surf = small_font.render(name, True, (0, 0, 0))
                name_rect = name_surf.get_rect(center=(cx + cell_w//2, cy + 60))
                screen.blit(name_surf, name_rect)
                
                # Price (Bottom)
                price_surf = small_font.render(f"{d_item.price} 金币", True, (200, 150, 0))
                price_rect = price_surf.get_rect(center=(cx + cell_w//2, cy + 80))
                screen.blit(price_surf, price_rect)
                
                # Register Buy Button
                self.buy_buttons.append((cell_rect, name, d_item.price))
                
                # Hover for Tooltip
                mx, my = pygame.mouse.get_pos()
                if cell_rect.collidepoint(mx, my):
                    self.hover_item = d_item
                    self.hover_rect = cell_rect
                    
                    # Highlight cell
                    pygame.draw.rect(screen, (100, 100, 255), cell_rect, width=2, border_radius=5)

        # --- Pagination Controls ---
        # Bottom area
        bottom_y = self.rect.bottom - 45
        center_x = self.rect.centerx
        
        # Prev Button
        self.prev_btn_rect.topleft = (center_x - 80, bottom_y)
        if self.page > 0:
            pygame.draw.rect(screen, (220, 220, 220), self.prev_btn_rect, border_radius=3)
            pygame.draw.rect(screen, (100, 100, 100), self.prev_btn_rect, 1, border_radius=3)
            prev_txt = small_font.render("上一页", True, (0, 0, 0))
            screen.blit(prev_txt, prev_txt.get_rect(center=self.prev_btn_rect.center))
            
        # Next Button
        self.next_btn_rect.topleft = (center_x + 20, bottom_y)
        if self.page < total_pages - 1:
            pygame.draw.rect(screen, (220, 220, 220), self.next_btn_rect, border_radius=3)
            pygame.draw.rect(screen, (100, 100, 100), self.next_btn_rect, 1, border_radius=3)
            next_txt = small_font.render("下一页", True, (0, 0, 0))
            screen.blit(next_txt, next_txt.get_rect(center=self.next_btn_rect.center))
            
        # Page Info
        page_info = small_font.render(f"{self.page + 1}/{max(1, total_pages)}", True, (0, 0, 0))
        screen.blit(page_info, page_info.get_rect(center=(center_x, bottom_y + 15)))

        # Player Gold (Left Bottom)
        gold_txt = small_font.render(f"金币: {self.player.gold}", True, (255, 215, 0))
        screen.blit(gold_txt, (self.rect.x + 20, self.rect.bottom - 25))
        
        # Quantity Input (Right Bottom)
        self.quantity_input_rect.topleft = (self.rect.right - 100, self.rect.bottom - 35)
        
        # Label
        q_label = small_font.render("数量:", True, (0, 0, 0))
        screen.blit(q_label, (self.quantity_input_rect.x - 40, self.quantity_input_rect.y + 5))
        
        # Box
        box_color = (255, 255, 255)
        border_color = (0, 0, 0)
        if self.is_input_active:
            border_color = (0, 0, 255)
            
        pygame.draw.rect(screen, box_color, self.quantity_input_rect)
        pygame.draw.rect(screen, border_color, self.quantity_input_rect, 1)
        
        # Text
        if self.quantity_input_text:
            q_txt = small_font.render(self.quantity_input_text, True, (0, 0, 0))
            screen.blit(q_txt, (self.quantity_input_rect.x + 5, self.quantity_input_rect.y + 5))
        
        # Tooltip (Draw last)
        if self.hover_item and self.hover_rect:
            # Calculate best position
            tx = self.hover_rect.right + 10
            ty = self.hover_rect.top
            self.draw_tooltip(screen, self.hover_item, tx, ty)

    def handle_click(self, pos, button=1):
        if hasattr(self, 'confirm_dialog') and self.confirm_dialog and self.confirm_dialog.visible:
            # Pass button to confirm dialog
            if self.confirm_dialog.handle_click(pos, button):
                return True
            return True # Consume click if modal

        if not super().handle_click(pos, button):
            return False
            
        if self.close_btn_rect.collidepoint(pos):
            self.visible = False
            return True
            
        mx, my = pos
        
        # Check Quantity Input Click
        if self.quantity_input_rect.collidepoint(pos):
            self.is_input_active = True
            pygame.key.start_text_input()
            pygame.key.set_text_input_rect(self.quantity_input_rect)
            return True
        else:
            if self.is_input_active:
                 self.is_input_active = False
                 pygame.key.stop_text_input()
        
        # Tabs (Left Click Only)
        if button == 1:
            for i, (rect, title) in enumerate(self.tab_rects):
                if rect.collidepoint(pos):
                    self.current_tab = i
                    self.page = 0 # Reset page on tab switch
                    return True
        
        # Pagination (Left Click Only)
        if button == 1:
            current_cat = self.tabs[self.current_tab]
            all_items = self.items.get(current_cat, [])
            total_pages = (len(all_items) + self.items_per_page - 1) // self.items_per_page
            
            if self.page > 0 and self.prev_btn_rect.collidepoint(pos):
                self.page -= 1
                return True
                
            if self.page < total_pages - 1 and self.next_btn_rect.collidepoint(pos):
                self.page += 1
                return True

        # Buy Items (Grid Cells)
        # Left Click to Buy (Button 1)
        if button == 1:
            for rect, name, price in self.buy_buttons:
                if rect.collidepoint(pos):
                    # Check if stackable
                    from src.systems.equipment.database import EQUIPMENT_DB
                    from src.systems.equipment.item import ItemType
                    
                    if name in EQUIPMENT_DB:
                        data = EQUIPMENT_DB[name]
                        is_stackable = False
                        
                        if data["type"] == ItemType.CONSUMABLE:
                            is_stackable = True
                        
                        if is_stackable:
                            # Get quantity from permanent input
                            try:
                                qty = int(self.quantity_input_text)
                                if qty < 1: qty = 1
                            except:
                                qty = 1
                                
                            # Clamp max stack (99)
                            qty = min(qty, 99)
                            
                            # Show Confirm Dialog
                            total_cost = price * qty
                            msg = f"确认购买 {name} x{qty} 吗？\n总价: {total_cost}"
                            
                            def on_confirm_buy():
                                self.buy_item(name, price, qty)
                                self.confirm_dialog = None
                                
                            self.confirm_dialog = DialogWindow(self.renderer, "购买确认", msg, ["确定", "取消"], 
                                lambda label: on_confirm_buy() if label == "确定" else None)
                            self.confirm_dialog.rect.center = (1024//2, 768//2)
                            
                        else:
                            # Direct Buy 1 (Non-stackable)
                            # Or confirm? User said "default only buy 1", implying direct or simpler flow.
                            # Let's keep direct buy for equipment to be fast, or safe confirm?
                            # User: "无论数量框...都默认只能买一个...也只会扣除一件商品的价格"
                            # I'll use direct buy for speed as per usual game UX for equipment.
                            self.buy_item(name, price, 1)
                    return True
        
        return True
        
    def show_quantity_dialog(self, name, price, max_stack):
        pass # Deprecated by permanent input box

    def buy_item(self, name, price, quantity=1):
        total_price = price * quantity
        if self.player.gold < total_price:
            self.confirm_dialog = DialogWindow(self.renderer, "提示", "金币不足！", ["确定"], None)
            self.confirm_dialog.rect.center = (1024//2, 768//2)
            return
            
        # Add to inventory
        from src.systems.equipment.database import EQUIPMENT_DB
        from src.systems.equipment.item import Item
        
        if name in EQUIPMENT_DB:
            # Construct real item
            data = EQUIPMENT_DB[name]
            
            # Helper to create item from DB
            from src.systems.equipment.item import ItemQuality, Equipment, ItemType
            
            # Check if it is Equipment
            equip_types = [
                ItemType.WEAPON, ItemType.ARMOR, ItemType.HELMET, ItemType.NECKLACE,
                ItemType.BRACELET, ItemType.RING, ItemType.BOOTS, ItemType.BELT, ItemType.MEDAL
            ]
            
            if data["type"] in equip_types:
                # Equipment is usually not stackable, so quantity loop if needed, but shop usually sells 1
                # If user forced quantity > 1 for equipment, we add multiple items
                items_to_add = []
                for _ in range(quantity):
                    new_item = Equipment(name, data["type"], ItemQuality.NORMAL, min_level=data.get("level", 1), weight=data.get("weight", 1))
                    new_item.stats = data.get("stats", {}).copy()
                    items_to_add.append(new_item)
                
                # Try add all
                success_count = 0
                for item in items_to_add:
                    if self.player.inventory.add_item(item):
                        success_count += 1
                    else:
                        break # Inventory full
                
                if success_count > 0:
                    cost = price * success_count
                    self.player.gold -= cost
                    if hasattr(self, 'game_engine'):
                        self.game_engine.spawn_floating_text(f"购买成功: {name} x{success_count}", self.player.x, self.player.y, (0, 255, 0))
                    
                    if success_count < quantity:
                         self.confirm_dialog = DialogWindow(self.renderer, "提示", f"背包已满！成功购买 {success_count} 个。", ["确定"], None)
                         self.confirm_dialog.rect.center = (1024//2, 768//2)
                else:
                     self.confirm_dialog = DialogWindow(self.renderer, "提示", "背包已满！", ["确定"], None)
                     self.confirm_dialog.rect.center = (1024//2, 768//2)

            else:
                 # Stackable Logic (Consumables)
                 new_item = Item(name, data["type"], ItemQuality.NORMAL, price=price, weight=data.get("weight", 1))
                 new_item.stats = data.get("stats", {}).copy()
                 
                 if data["type"].name == "CONSUMABLE":
                    new_item.stackable = True
                    new_item.max_stack = 99
                    new_item.count = quantity # Set stack count directly
                 elif data["type"].name == "SKILL_BOOK":
                    new_item.stackable = False
                    # Treat like equipment loop if multiple? usually 1
                    new_item.count = 1 
                 
                 # Add
                 if self.player.inventory.add_item(new_item):
                    self.player.gold -= total_price
                    if hasattr(self, 'game_engine'):
                        self.game_engine.spawn_floating_text(f"购买成功: {name} x{quantity}", self.player.x, self.player.y, (0, 255, 0))
                 else:
                    self.confirm_dialog = DialogWindow(self.renderer, "提示", "背包已满！", ["确定"], None)
                    self.confirm_dialog.rect.center = (1024//2, 768//2)

class TreasureWindow(UIWindow):
    def __init__(self, renderer, item, on_collect_callback):
        super().__init__("获得宝藏", 300, 200, 400, 300, renderer)
        self.item = item
        self.on_collect = on_collect_callback
        self.visible = True # Ensure window is visible upon creation
        
        # Collect Button
        btn_w = 120
        btn_h = 40
        # Store RELATIVE coordinates for button rect
        self.collect_btn_rect = pygame.Rect((self.rect.width - btn_w)//2, self.rect.height - 60, btn_w, btn_h)

    def draw_content(self, screen):
        # Draw Item Centered
        cx = self.rect.x + self.rect.width // 2
        cy = self.rect.y + 80
        
        self.renderer.draw_item_slot(cx - 30, cy - 30, 60, self.item)
        
        # Name
        color = self.renderer.get_quality_color(self.item.quality.value)
        txt = self.renderer.cn_font.render(self.item.name, True, color)
        txt_rect = txt.get_rect(center=(cx, cy + 50))
        screen.blit(txt, txt_rect)
        
        # Button
        # Calculate ABSOLUTE position for drawing
        abs_btn = pygame.Rect(self.rect.x + self.collect_btn_rect.x, self.rect.y + self.collect_btn_rect.y, self.collect_btn_rect.width, self.collect_btn_rect.height)
        pygame.draw.rect(screen, (50, 200, 50), abs_btn, border_radius=5)
        pygame.draw.rect(screen, (0, 0, 0), abs_btn, 1, border_radius=5)
        
        btn_txt = self.renderer.cn_font.render("收入囊中", True, (255, 255, 255))
        btn_rect = btn_txt.get_rect(center=abs_btn.center)
        screen.blit(btn_txt, btn_rect)
        
        # Hover for tooltip
        mx, my = pygame.mouse.get_pos()
        item_rect = pygame.Rect(cx - 30, cy - 30, 60, 60)
        if item_rect.collidepoint(mx, my):
             self.draw_tooltip(screen, self.item, item_rect.right + 10, item_rect.bottom + 10)

    def handle_click(self, pos, button=1):
        # UIWindow.handle_click handles close button (X) and background click
        if not super().handle_click(pos, button): return False
        
        mx, my = pos
        # Calculate ABSOLUTE position for hit testing
        abs_btn = pygame.Rect(self.rect.x + self.collect_btn_rect.x, self.rect.y + self.collect_btn_rect.y, self.collect_btn_rect.width, self.collect_btn_rect.height)
        
        if abs_btn.collidepoint(mx, my):
            if self.on_collect:
                if self.on_collect():
                    self.visible = False
            return True
            
        return True
