class ExperienceSystem:
    def __init__(self):
        self.base_xp = 100
        self.growth_factor = 1.2  # Exponential growth

    def get_xp_for_next_level(self, current_level):
        if current_level >= 100:
            return 999999999 # Max level
            
        # Exponential growth curve for 100 levels
        # Level 1: ~100
        # Level 50: ~100 * 50^2.2 ~ 500,000
        # Level 99: ~100 * 99^2.5 ~ 10,000,000
        exponent = 1.5 + (current_level / 100.0)
        return int(self.base_xp * (current_level ** exponent))

    def check_level_up(self, current_xp, current_level):
        needed = self.get_xp_for_next_level(current_level)
        if current_xp >= needed:
            return True, current_xp - needed
        return False, current_xp
