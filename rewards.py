class RewardSystem:
    def __init__(self):
        self.rewards = {
            "brave_patient": "🦁 Brave Patient Badge",
            "curious_mind": "🦊 Curious Mind Badge",
            "friendly_friend": "🐼 Friendly Friend Badge"
        }
        
    async def award_badge(self, badge_type: str, child_id: str):
        # Award badge logic
        pass

    async def get_progress(self, child_id: str):
        # Get child's progress and badges
        pass 