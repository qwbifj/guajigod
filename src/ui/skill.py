import pygame

class SkillAnimation:
    def __init__(self, x, y, gif_path, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.frames = []
        self.current_frame = 0
        self.frame_delay = 5
        self.timer = 0
        self.loaded = False
        self.load_gif(gif_path)
        
    def load_gif(self, path):
        # Folder loading logic (from Skill 'Dynamic')
        import os
        if os.path.isdir(path):
            i = 0 # Folder often starts at 0 or 1
            # Check if 0.png exists
            if not os.path.exists(os.path.join(path, "0.png")):
                i = 1
                
            while True:
                p = os.path.join(path, f"{i}.png")
                # Also try .PNG
                if not os.path.exists(p):
                    p = os.path.join(path, f"{i}.PNG")
                    if not os.path.exists(p):
                        break
                
                try:
                    surf = pygame.image.load(p)
                    if self.width and self.height:
                        surf = pygame.transform.scale(surf, (self.width, self.height))
                    self.frames.append(surf)
                    self.loaded = True
                except:
                    print(f"Failed to load frame {p}")
                    break
                i += 1
        else:
            # File loading (GIF or single image)
            try:
                # Try loading as single image first if PIL missing
                surf = pygame.image.load(path)
                # Scale
                if self.width and self.height:
                    surf = pygame.transform.scale(surf, (self.width, self.height))
                self.frames.append(surf)
                self.loaded = True
                
                # If we want real GIF support we need PIL, but let's stick to basic pygame load 
                # which usually only loads first frame of GIF. 
                # For "dynamic effect", we can simulate it if we only have one frame
                # by fading it or scaling it.
                # But let's try to see if we can do better if PIL is present.
                try:
                    from PIL import Image, ImageSequence
                    img = Image.open(path)
                    self.frames = [] # Clear the single frame
                    for frame in ImageSequence.Iterator(img):
                        data = frame.convert("RGBA").tobytes()
                        mode = "RGBA"
                        size = frame.size
                        surf = pygame.image.fromstring(data, size, mode)
                        # Scale
                        if self.width and self.height:
                            surf = pygame.transform.scale(surf, (self.width, self.height))
                        self.frames.append(surf)
                except ImportError:
                    pass # Stick with single frame
                    
            except:
                print(f"Failed to load {path}")

    def update(self):
        if not self.frames: return False
        
        self.timer += 1
        if self.timer >= self.frame_delay:
            self.timer = 0
            self.current_frame += 1
        
        # If single frame, maybe just show it for a duration
        if len(self.frames) == 1:
            if self.current_frame > 10: # Show for 10 'frames' (updates) * 5 = 50 ticks
                return False
            # Force current_frame to 0 for display
            self.current_frame = 0 
            return True
            
        if self.current_frame >= len(self.frames):
            return False # Finished
        return True
