from src.systems.equipment.item import Item, ItemType, ItemQuality

class Inventory:
    def __init__(self, capacity=600):
        self.capacity = 600
        # Instead of unlocked_slots count, we track unlocked pages.
        # Page 1 (0-149) unlocked by default.
        # Pages 2, 3, 4 locked.
        self.unlocked_pages = 1 
        self.page_size = 150
        self.max_weight = 100000 # Default high, updated by Player
        
        # Initialize fixed size list with None
        self.items = [None] * self.capacity

    def __getattr__(self, name):
        if name == 'max_weight':
            return 100000 # Default fallback
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    @property
    def current_weight(self):
        w = 0
        for item in self.items:
            if item:
                if getattr(item, 'stackable', False):
                    # Stackable items only count as 1 unit of weight per stack (slot)
                    w += getattr(item, 'weight', 1)
                else:
                    w += getattr(item, 'weight', 1) * getattr(item, 'count', 1)
        return w

    @property
    def unlocked_slots(self):
        return self.unlocked_pages * self.page_size

    def sort_items(self):
        # Sort items only within unlocked pages? Or globally?
        # Usually globally and then pack them into first available slots.
        
        # 1. Collect valid items
        raw_items = [item for item in self.items if item is not None]
        
        # 2. Sort
        quality_priority = {
            "DIVINE": 7, "MYTHIC": 6, "LEGENDARY": 5, "EPIC": 4, 
            "RARE": 3, "HIGH": 2, "NORMAL": 1
        }
        type_priority = {
            "WEAPON": 1, "ARMOR": 2, "HELMET": 3, "NECKLACE": 4, 
            "BRACELET": 5, "RING": 6, "BELT": 7, "BOOTS": 8, "MEDAL": 9,
            "CONSUMABLE": 10, "MATERIAL": 11
        }

        def sort_key(item):
            t_p = type_priority.get(item.item_type.name, 99)
            q_p = quality_priority.get(item.quality.name, 0)
            return (t_p, -q_p, item.name)
            
        raw_items.sort(key=sort_key)
        
        # 3. Merge stacks
        merged_items = []
        if raw_items:
            current_item = raw_items[0]
            for next_item in raw_items[1:]:
                # Check if mergeable
                if (current_item.stackable and next_item.stackable and 
                    current_item.name == next_item.name and 
                    current_item.quality == next_item.quality):
                    
                    # Merge next_item into current_item
                    space = current_item.max_stack - current_item.count
                    to_add = min(space, next_item.count)
                    
                    current_item.count += to_add
                    next_item.count -= to_add
                    
                    if next_item.count > 0:
                        # Current stack full, push current and start new stack with remainder
                        merged_items.append(current_item)
                        current_item = next_item
                    else:
                        # Next item fully merged, discard it (continue using current)
                        pass
                else:
                    # Different item, push current and switch
                    merged_items.append(current_item)
                    current_item = next_item
            # Append last item
            merged_items.append(current_item)
        
        # 4. Re-populate self.items
        self.items = [None] * self.capacity
        for i, item in enumerate(merged_items):
            self.items[i] = item
            
        print("Inventory sorted and stacked.")

    def unlock_page(self, cost_type, cost_amount):
        if self.unlocked_pages < 4:
            self.unlocked_pages += 1
            return True
        return False
        
    def add_item(self, item: Item):
        limit = self.unlocked_pages * self.page_size
        
        # Check weight
        # For stackable items, we assume worst case (new slot) which adds 1 unit of weight.
        # If it merges, it adds 0 weight under new rules.
        item_weight = getattr(item, 'weight', 1)
        if getattr(item, 'stackable', False):
             weight_to_add = item_weight
        else:
             weight_to_add = item_weight * getattr(item, 'count', 1)
        
        if self.current_weight + weight_to_add > self.max_weight:
            # Only block if we strictly exceed limit even with optimal stacking?
            # Actually, if it merges, weight_to_add is 0. 
            # So we should probably check weight AFTER determining if we need a new slot.
            # But that complicates the logic flow. 
            # Given max_weight is usually high (100000), this check is mostly for safety.
            # Let's keep it simple: if adding a new slot would overflow, we might reject.
            # But if it merges, we shouldn't.
            
            # Let's verify if we can merge first.
            can_merge = False
            if item.stackable:
                 for i in range(limit):
                    existing = self.items[i]
                    if (existing and existing.stackable and 
                        existing.name == item.name and 
                        existing.quality == item.quality):
                        if existing.count < existing.max_stack:
                            can_merge = True
                            break
            
            if not can_merge:
                 # If we can't merge, we definitely add weight
                 if self.current_weight + weight_to_add > self.max_weight:
                     print(f"Inventory too heavy! Current: {self.current_weight}, Max: {self.max_weight}")
                     return False
            # If we can merge, weight change is 0, so no check needed (assuming current < max)

        # 1. Try to stack
        if item.stackable:
            for i in range(limit):
                existing = self.items[i]
                if (existing and existing.stackable and 
                    existing.name == item.name and 
                    existing.quality == item.quality):
                    
                    space = existing.max_stack - existing.count
                    if space > 0:
                        to_add = min(space, item.count)
                        existing.count += to_add
                        item.count -= to_add
                        
                        if item.count <= 0:
                            return True
                            
        # 2. Find empty slot for remainder
        if item.count > 0:
            for i in range(limit):
                if self.items[i] is None:
                    self.items[i] = item
                    return True
        return False

    def remove_item(self, item: Item, count=1):
        if item in self.items:
            # If stackable and count specified, reduce count
            if item.stackable and item.count > count:
                item.count -= count
                return True
            else:
                # Remove entirely
                idx = self.items.index(item)
                self.items[idx] = None
                return True
        return False
        
    def move_item(self, from_index, to_index):
        limit = self.unlocked_pages * self.page_size
        if 0 <= from_index < limit and 0 <= to_index < limit:
            self.items[from_index], self.items[to_index] = self.items[to_index], self.items[from_index]
            return True
        return False

    def list_items(self):
        pass

    def find_item_index(self, item_name):
        """Find the first index of an item with the given name."""
        for i, item in enumerate(self.items):
            if item and item.name == item_name:
                return i
        return -1

    def get_item_count(self, item_name):
        count = 0
        for item in self.items:
            if item and item.name == item_name:
                count += item.count
        return count

    def to_dict(self):
        # Convert items to list of dicts (filtering None)
        items_data = []
        for i, item in enumerate(self.items):
            if item:
                item_data = item.to_dict()
                item_data["slot_index"] = i # Track slot index to restore position
                items_data.append(item_data)
        
        return {
            "capacity": self.capacity,
            "unlocked_pages": self.unlocked_pages,
            "max_weight": self.max_weight,
            "items": items_data
        }

    @classmethod
    def from_dict(cls, data):
        inv = cls(data.get("capacity", 600))
        inv.unlocked_pages = data.get("unlocked_pages", 1)
        inv.max_weight = data.get("max_weight", 100000)
        
        items_data = data.get("items", [])
        for item_data in items_data:
            item = Item.from_dict(item_data)
            slot_index = item_data.get("slot_index", -1)
            
            if 0 <= slot_index < len(inv.items):
                inv.items[slot_index] = item
            else:
                # Fallback if slot index invalid
                inv.add_item(item)
                
        return inv
