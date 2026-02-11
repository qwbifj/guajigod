from enum import Enum

class QuestStatus(Enum):
    NOT_STARTED = 0
    IN_PROGRESS = 1
    READY_TO_TURN_IN = 2
    COMPLETED = 3

class QuestStage:
    def __init__(self, description, type, target=None, count=0):
        self.description = description
        self.type = type # "dialog", "kill", "collect"
        self.target = target # NPC Name or Monster Name
        self.count = count
        self.current_count = 0
        self.completed = False

    def to_dict(self):
        return {
            "description": self.description,
            "type": self.type,
            "target": self.target,
            "count": self.count,
            "current_count": self.current_count,
            "completed": self.completed
        }

    @classmethod
    def from_dict(cls, data):
        stage = cls(data["description"], data["type"], data.get("target"), data.get("count", 0))
        stage.current_count = data.get("current_count", 0)
        stage.completed = data.get("completed", False)
        return stage

class Quest:
    def __init__(self, id, title, description, reward_xp=0, reward_gold=0, reward_items=None):
        self.id = id
        self.title = title
        self.description = description
        self.reward_xp = reward_xp
        self.reward_gold = reward_gold
        self.reward_items = reward_items or []
        
        self.stages = []
        self.current_stage_index = 0
        self.status = QuestStatus.NOT_STARTED

    def to_dict(self):
        # We need to save items? Usually items are static rewards, so we don't save them.
        # But if we want to be fully generic...
        # For now, let's assume quests are static definitions and we only save state.
        # BUT, if we are serializing the whole object to replace pickle, we need everything if we can't look it up.
        # However, looking up from ID is better.
        # Let's assume we save everything for now to match pickle behavior.
        
        # Serialize reward items
        # items_data = [item.to_dict() for item in self.reward_items] 
        # But we don't have Item imported here...
        
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "reward_xp": self.reward_xp,
            "reward_gold": self.reward_gold,
            # "reward_items": items_data, # Skip for now to avoid complexity, assuming rewards are re-hydrated or not needed for save state if quests are static
            "stages": [s.to_dict() for s in self.stages],
            "current_stage_index": self.current_stage_index,
            "status": self.status.name
        }

    @classmethod
    def from_dict(cls, data):
        quest = cls(data["id"], data["title"], data["description"], 
                   data.get("reward_xp", 0), data.get("reward_gold", 0))
        
        # Restore stages
        quest.stages = [QuestStage.from_dict(s) for s in data.get("stages", [])]
        quest.current_stage_index = data.get("current_stage_index", 0)
        
        try:
            quest.status = QuestStatus[data.get("status", "NOT_STARTED")]
        except:
            quest.status = QuestStatus.NOT_STARTED
            
        return quest

    def add_stage(self, stage):
        self.stages.append(stage)
        
    def get_current_stage(self):
        if self.current_stage_index < len(self.stages):
            return self.stages[self.current_stage_index]
        return None

    def check_kill(self, monster_name):
        if self.status != QuestStatus.IN_PROGRESS:
            return False
            
        stage = self.get_current_stage()
        if stage and stage.type == "kill" and stage.target == monster_name:
            stage.current_count += 1
            if stage.current_count >= stage.count:
                stage.completed = True
                self.advance_stage()
                return True # Progress made
        return False
        
    def check_dialog(self, npc_name):
        if self.status != QuestStatus.IN_PROGRESS:
            return False
            
        stage = self.get_current_stage()
        if stage and stage.type == "dialog" and stage.target == npc_name:
            stage.completed = True
            self.advance_stage()
            return True
        return False

    def advance_stage(self):
        self.current_stage_index += 1
        if self.current_stage_index >= len(self.stages):
            self.status = QuestStatus.READY_TO_TURN_IN
            print(f"Quest '{self.title}' ready to turn in!")
        else:
            print(f"Quest '{self.title}' stage updated: {self.get_current_stage().description}")

    def complete(self, player):
        if self.status == QuestStatus.READY_TO_TURN_IN:
            self.status = QuestStatus.COMPLETED
            player.gain_xp(self.reward_xp)
            player.gold += self.reward_gold
            for item in self.reward_items:
                player.inventory.add_item(item)
            print(f"Quest '{self.title}' completed!")
            return True
        return False

class QuestManager:
    def __init__(self):
        self.quests = {} # id -> Quest
        self.active_quests = [] # list of Quest objects

    def add_quest(self, quest: Quest):
        self.quests[quest.id] = quest

    def get_quest(self, quest_id):
        return self.quests.get(quest_id)

    def accept_quest(self, quest_id):
        quest = self.quests.get(quest_id)
        if quest and quest.status == QuestStatus.NOT_STARTED:
            quest.status = QuestStatus.IN_PROGRESS
            self.active_quests.append(quest)
            print(f"Accepted quest: {quest.title}")
            return True
        return False

    def update_kill(self, monster_name):
        # Return true if any quest updated
        updated = False
        for q in self.active_quests:
            if q.check_kill(monster_name):
                updated = True
        return updated
        
    def update_dialog(self, npc_name):
        for q in self.active_quests:
            if q.check_dialog(npc_name):
                return True
        return False

    def to_dict(self):
        # We save all quests because their state might change?
        # Or just active quests? 
        # Usually we want to persist all known quests states.
        return {
            "quests": {qid: q.to_dict() for qid, q in self.quests.items()},
            # active_quests can be derived from quests where status == IN_PROGRESS
        }

    @classmethod
    def from_dict(cls, data):
        qm = cls()
        quests_data = data.get("quests", {})
        for qid, q_data in quests_data.items():
            quest = Quest.from_dict(q_data)
            qm.add_quest(quest)
            if quest.status == QuestStatus.IN_PROGRESS:
                qm.active_quests.append(quest)
        return qm
