import pygame
import sys
from src.ui.windows import FloatingText

# Colors
GREEN = (50, 200, 50)

def handle_input(self):
    # Long Press Detection Logic
    current_time = pygame.time.get_ticks()
    
    if not hasattr(self, 'touch_start_time'): self.touch_start_time = 0
    if not hasattr(self, 'touch_start_pos'): self.touch_start_pos = (0, 0)
    if not hasattr(self, 'is_long_press_triggered'): self.is_long_press_triggered = False
    
    # Long press threshold (ms)
    LONG_PRESS_THRESHOLD = 600 
    
    # Check Long Press
    if self.touch_start_time > 0 and not self.is_long_press_triggered:
        if current_time - self.touch_start_time > LONG_PRESS_THRESHOLD:
            # Trigger Long Press (Simulate Right Click)
            self.is_long_press_triggered = True
            
            # Create a simulated event for Right Click
            sim_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {
                'pos': self.touch_start_pos,
                'button': 3,
                'touch': True # Flag to distinguish
            })
            
            # Process this event immediately
            process_single_event(self, sim_event)
            
            # Visual feedback?
            # self.spawn_floating_text("长按触发", self.touch_start_pos[0], self.touch_start_pos[1], (200, 200, 50))

    for event in pygame.event.get():
        process_single_event(self, event)

def process_single_event(self, event):
    # Handle Touch for Long Press
    if event.type == pygame.MOUSEBUTTONDOWN:
        if event.button == 1: # Left click / Touch start
            if not hasattr(self, 'touch_start_time'): self.touch_start_time = 0
            if not hasattr(self, 'touch_start_pos'): self.touch_start_pos = (0, 0)
            if not hasattr(self, 'is_long_press_triggered'): self.is_long_press_triggered = False
            
            self.touch_start_time = pygame.time.get_ticks()
            self.touch_start_pos = event.pos
            self.is_long_press_triggered = False
    
    elif event.type == pygame.MOUSEBUTTONUP:
        if event.button == 1:
            if not hasattr(self, 'touch_start_time'): self.touch_start_time = 0
            if not hasattr(self, 'is_long_press_triggered'): self.is_long_press_triggered = False
            
            self.touch_start_time = 0 # Reset
            if self.is_long_press_triggered:
                return # Ignore the UP event if it was a long press trigger
        
    elif event.type == pygame.MOUSEMOTION:
        # Cancel long press if moved too much
        if not hasattr(self, 'touch_start_time'): self.touch_start_time = 0
        if not hasattr(self, 'touch_start_pos'): self.touch_start_pos = (0, 0)
        
        if self.touch_start_time > 0:
            dx = event.pos[0] - self.touch_start_pos[0]
            dy = event.pos[1] - self.touch_start_pos[1]
            if (dx*dx + dy*dy) > 100: # 10 pixels sq
                self.touch_start_time = 0

    # Pass events to windows first (for drag/hover/etc)
    
    # Patch event.pos if it's mouse event to handle scaling
    if event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION]:
        try:
            # We need to use transform_input from the engine (self)
            real_pos = event.pos
            trans_pos = self.transform_input(real_pos)
            
            # Update event.pos if possible.
            event.pos = trans_pos
            
            if hasattr(event, 'rel'):
                    rx, ry = event.rel
                    event.rel = (int(rx / self.scale_ratio), int(ry / self.scale_ratio))
        except:
            pass

    for win in self.windows.values():
        if hasattr(win, 'handle_event'):
            win.handle_event(event)
    
    if event.type == pygame.QUIT:
        self.save_game_state()
        pygame.quit()
        sys.exit()
    
    if event.type == pygame.VIDEORESIZE:
        self.update_scaling()
        return

    if event.type == pygame.MOUSEBUTTONDOWN:
        # Always calculate transformed position explicitly
        # Do not rely on event.pos being modified successfully
        mx, my = self.transform_input(event.pos) if hasattr(event, 'pos') else (0,0)
        # Re-calculate because event.pos might be raw if patch failed or we want to be safe
        # Actually above we patched event.pos, so event.pos is already transformed?
        # Let's trust event.pos if we patched it, BUT transform_input expects raw screen coords?
        # NO, transform_input(pos) applies offset and scale.
        # If we already patched event.pos to be transformed, applying it again is WRONG!
        
        # Let's look at line 126 in original file:
        # mx, my = self.transform_input(event.pos)
        
        # In my patch above:
        # event.pos = trans_pos
        
        # So if we call transform_input(event.pos) again, it will double transform!
        # We should fix this.
        
        # If we patched event.pos, we use it directly as mx, my.
        mx, my = event.pos
        
        # 1. Check Windows (Topmost Priority)
        window_handled = False
        win_keys = list(self.windows.keys())
        for key in reversed(win_keys):
            win = self.windows[key]
            if win.visible:
                # Special handling for Modal Dialog
                if key == "对话":
                        if win.handle_click((mx, my), event.button):
                            window_handled = True
                        else:
                            # Block clicks through modal background
                            window_handled = True 
                        break
                
                # Pass event.button to handle_click
                if win.handle_click((mx, my), event.button):
                    window_handled = True
                    
                    # Only bring to front if it's not the shop window (to prevent input dialog hiding)
                    if not hasattr(win, 'confirm_dialog') or win.confirm_dialog is None:
                            # Bring to front
                            if key in self.windows and self.windows[key] is win:
                                del self.windows[key]
                                self.windows[key] = win
                    break
                else:
                    # If click is inside window rect but not handled (e.g. background),
                    # we still consume it to prevent click-through
                    if win.rect.collidepoint(mx, my):
                        window_handled = True
                        
                        if not hasattr(win, 'confirm_dialog') or win.confirm_dialog is None:
                            # Bring to front
                            if key in self.windows and self.windows[key] is win:
                                del self.windows[key]
                                self.windows[key] = win
                        break

        if window_handled:
            return
        
        # 2. Check UI buttons FIRST (Global Priority)
        button_handled = False
        for label, rect in self.button_rects.items():
            if rect.collidepoint(mx, my):
                button_handled = True
                self.log(f"Clicked {label}")
                # Toggle window
                if label in self.windows:
                    self.windows[label].visible = not self.windows[label].visible
                    # Bring to front if opening
                    if self.windows[label].visible:
                        w = self.windows[label]
                        del self.windows[label]
                        self.windows[label] = w
                
                break # Handled button click
        
        if button_handled:
            return # Skip window/world clicks if UI button pressed
        
        # Check Save Button (Also UI)
        if self.save_btn_rect and self.save_btn_rect.collidepoint(mx, my):
            self.save_game_state()
            cx, cy = self.save_btn_rect.center
            self.floating_texts.append(FloatingText("保存成功", cx, cy - 30, GREEN))
            return
        
        # Check Logout Button
        if self.logout_btn_rect and self.logout_btn_rect.collidepoint(mx, my):
            self.save_game_state()
            # Return to Character Select instead of Login
            self.state = "CHARACTER_SELECT"
            # self.network_manager.logout() # Keep session
            return
        
        # Check Auto Combat Button
        if self.auto_combat_btn_rect and self.auto_combat_btn_rect.collidepoint(mx, my):
            self.auto_combat_enabled = not self.auto_combat_enabled
            state_text = "开启" if self.auto_combat_enabled else "停止"
            self.log(f"已{state_text}自动战斗")
            return
        
        # Check NPC Bar Clicks
        if hasattr(self, 'npc_rects'):
            npc_handled = False
            for npc_name, rect in self.npc_rects.items():
                if rect.collidepoint(mx, my):
                    self.interact_npc(npc_name)
                    npc_handled = True
                    break
            if npc_handled: return
        
        # 6. World Click (Move/Attack)
        # Convert screen to grid
        # Use engine's map offsets
        off_x = getattr(self, 'map_offset_x', 50)
        off_y = getattr(self, 'map_offset_y', 50)
        
        grid_x = (mx - off_x) // (self.renderer.tile_size + self.renderer.margin)
        grid_y = (my - off_y) // (self.renderer.tile_size + self.renderer.margin)
        
        if 0 <= grid_x < self.current_map.width and 0 <= grid_y < self.current_map.height:
            # Check for monster
            target = None
            for m in self.current_map.active_monsters:
                if m.x == grid_x and m.y == grid_y:
                    target = m
                    break
            
            if target:
                # Lock target and attack
                self.target_monster = target
                self.try_attack(target)
            else:
                # Move
                # If manual click, we set a target position for auto-pilot to pathfind?
                # Or just one step?
                # Let's set a manual target pos
                self.manual_target_pos = (grid_x, grid_y)
                self.target_monster = None # Clear target if clicking ground
                self.log(f"移动到 ({grid_x}, {grid_y})")
    
    if event.type == pygame.KEYDOWN:
        # Check for any window that wants keys (Priority to Topmost)
        key_handled = False
        win_keys = list(self.windows.keys())
        for key in reversed(win_keys):
            win = self.windows[key]
            if win.visible and hasattr(win, 'handle_input'):
                if win.handle_input(event):
                    key_handled = True
                    break
        
        if key_handled:
            return

        # Check if settings window handles it (Legacy, kept just in case)
        if self.windows["设置"].visible:
            if self.windows["设置"].handle_keydown(event):
                return
                
        dx, dy = 0, 0
        if event.key == pygame.K_UP:
            dy = -1
        elif event.key == pygame.K_DOWN:
            dy = 1
        elif event.key == pygame.K_LEFT:
            dx = -1
        elif event.key == pygame.K_RIGHT:
            dx = 1
        # elif event.key == pygame.K_SPACE:
        #     # Spawn new monster for testing
        #     m = self.current_map.spawn_monster()
        #     if m:
        #         self.log(f"生成了 {m.name} 在 ({m.x}, {m.y})")
        
        if dx != 0 or dy != 0:
            self.move_player(dx, dy)
