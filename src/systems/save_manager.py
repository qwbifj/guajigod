import pickle
import os
import datetime
import hashlib
import hmac
import zlib

class SaveManager:
    # A fixed secret key for HMAC. In a real game, this might be obfuscated or user-specific.
    # For this implementation, a hardcoded key is sufficient to prevent casual editing.
    SECRET_KEY = b"killmonster_secure_save_key_2026"

    def __init__(self, save_file="savegame.dat"):
        self.save_file = save_file

    def save_game(self, characters, auto_save_settings, filename=None, username=None):
        target_file = filename if filename else self.save_file
        
        data = {
            "characters": characters,
            "auto_save_settings": auto_save_settings,
            "timestamp": datetime.datetime.now(),
            "owner_username": username
        }
        try:
            # 1. Serialize
            serialized_data = pickle.dumps(data)
            
            # 2. Compress (Obfuscate)
            compressed_data = zlib.compress(serialized_data)
            
            # 3. Sign (Integrity Check)
            signature = hmac.new(self.SECRET_KEY, compressed_data, hashlib.sha256).digest()
            
            # 4. Write: Signature (32 bytes) + Compressed Data
            with open(target_file, "wb") as f:
                f.write(signature)
                f.write(compressed_data)
                
            print(f"Game saved to {target_file} (Secured)")
            return True
        except Exception as e:
            print(f"Failed to save game: {e}")
            return False

    def load_game(self, filename=None, expected_username=None):
        target_file = filename if filename else self.save_file
        
        if not os.path.exists(target_file):
            return None
        
        try:
            with open(target_file, "rb") as f:
                file_content = f.read()
            
            # Check minimum length (Signature 32 bytes)
            if len(file_content) < 32:
                print("Save file too short/corrupted.")
                return None
                
            file_signature = file_content[:32]
            file_data = file_content[32:]
            
            # 1. Verify Signature
            expected_signature = hmac.new(self.SECRET_KEY, file_data, hashlib.sha256).digest()
            if not hmac.compare_digest(file_signature, expected_signature):
                print("Save file signature mismatch! File may have been tampered with.")
                return None
            
            # 2. Decompress
            try:
                serialized_data = zlib.decompress(file_data)
            except zlib.error:
                print("Save file decompression failed.")
                return None
                
            # 3. Deserialize
            data = pickle.loads(serialized_data)
            
            # 4. Username validation
            if expected_username:
                owner = data.get("owner_username")
                if owner != expected_username:
                    print(f"Save file belongs to {owner}, expected {expected_username}. Load aborted.")
                    return None
            
            # 5. Migration for Legacy Save (Single Player -> Characters List)
            if "characters" not in data and "player" in data:
                print("Migrating legacy save to multi-character format...")
                char0 = {
                    "player": data["player"],
                    "map_name": data.get("map_name", "新手村"),
                    "quest_manager": data.get("quest_manager")
                }
                data["characters"] = [char0, None, None]
                
            print(f"Game loaded from {target_file} (Secured)")
            return data
        except Exception as e:
            print(f"Failed to load game: {e}")
            return None

    def get_save_dict(self, characters, auto_save_settings):
        # Convert objects to dicts for JSON
        chars_json = []
        for char in characters:
            if char:
                chars_json.append({
                    "player": char["player"].to_dict(),
                    "map_name": char["map_name"],
                    "quest_manager": char["quest_manager"].to_dict() if char["quest_manager"] else None
                })
            else:
                chars_json.append(None)

        return {
            "characters": chars_json,
            "auto_save_settings": auto_save_settings,
            "timestamp": datetime.datetime.now().isoformat()
        }

    def load_from_dict(self, data):
        # This returns a dictionary similar to pickle.load but constructed from JSON data
        from src.systems.character.player import Player
        from src.systems.quest.manager import QuestManager
        
        # Legacy Cloud Migration
        if "characters" not in data and "player" in data:
            # Construct single char list
            player_data = data.get("player")
            player = Player.from_dict(player_data) if player_data else None
            
            quest_data = data.get("quest_manager")
            quest_manager = QuestManager.from_dict(quest_data) if quest_data else None
            
            char0 = {
                "player": player,
                "map_name": data.get("map_name", "Unknown"),
                "quest_manager": quest_manager
            }
            return {
                "characters": [char0, None, None],
                "auto_save_settings": data.get("auto_save_settings", {}),
                "timestamp": data.get("timestamp")
            }

        # Normal Multi-char Load
        characters = []
        if "characters" in data:
             for char_data in data["characters"]:
                 if char_data:
                     p_data = char_data.get("player")
                     player = Player.from_dict(p_data) if p_data else None
                     
                     q_data = char_data.get("quest_manager")
                     qm = QuestManager.from_dict(q_data) if q_data else None
                     
                     characters.append({
                         "player": player,
                         "map_name": char_data.get("map_name", "新手村"),
                         "quest_manager": qm
                     })
                 else:
                     characters.append(None)
        
        return {
            "characters": characters,
            "auto_save_settings": data.get("auto_save_settings", {}),
            "timestamp": data.get("timestamp")
        }
