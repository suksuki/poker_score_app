from lunar_python import Lunar, Solar

class WuXingEngine:
    # 1. Standard Hidden Stems Ratios (approximate standard in quantitative Bazi)
    # Ratios represent the strength of Qi hidden in Earthly Branches
    HIDDEN_STEMS_MAP = {
        "子": {"癸": 1.0},                # Rat: 100% Water
        "丑": {"己": 0.6, "癸": 0.3, "辛": 0.1}, # Ox: Earth main, Water middle, Metal residual
        "寅": {"甲": 0.6, "丙": 0.3, "戊": 0.1}, # Tiger: Wood main, Fire middle, Earth residual
        "卯": {"乙": 1.0},                # Rabbit: 100% Wood
        "辰": {"戊": 0.6, "乙": 0.3, "癸": 0.1}, # Dragon: Earth main, Wood middle, Water residual
        "巳": {"丙": 0.6, "戊": 0.3, "庚": 0.1}, # Snake: Fire main, Earth middle, Metal residual
        "午": {"丁": 0.7, "己": 0.3},      # Horse: Fire main, Earth middle
        "未": {"己": 0.6, "丁": 0.3, "乙": 0.1}, # Goat: Earth main, Fire middle, Wood residual
        "申": {"庚": 0.6, "壬": 0.3, "戊": 0.1}, # Monkey: Metal main, Water middle, Earth residual
        "酉": {"辛": 1.0},                # Rooster: 100% Metal
        "戌": {"戊": 0.6, "辛": 0.3, "丁": 0.1}, # Dog: Earth main, Metal middle, Fire residual
        "亥": {"壬": 0.7, "甲": 0.3}       # Pig: Water main, Wood middle
    }

    # 2. Base Weights for Pillar Positions (The "Place" weights)
    # Theory: Month Branch is strongest (Season/De Ling). Day Branch is next (Spouse Palace).
    POSITION_WEIGHTS = {
        "year_stem": 10, "year_branch": 15,
        "month_stem": 12, "month_branch": 40, # Month Branch commands the season
        "day_stem": 0,    "day_branch": 20, # Day Stem is "Self" (reference point, weight handled separately)
        "hour_stem": 12,  "hour_branch": 15
    }

    WU_XING_MAP = {
        "甲": "Mu", "乙": "Mu",
        "丙": "Huo", "丁": "Huo",
        "戊": "Tu",  "己": "Tu",
        "庚": "Jin", "辛": "Jin",
        "壬": "Shui", "癸": "Shui"
    }
    
    RELATIONSHIPS = {
        "Sheng": {"Mu": "Huo", "Huo": "Tu", "Tu": "Jin", "Jin": "Shui", "Shui": "Mu"}, # Generates
        "Ke":    {"Mu": "Tu", "Tu": "Shui", "Shui": "Huo", "Huo": "Jin", "Jin": "Mu"}  # Controls
    }

    def __init__(self, chart):
        """
        chart: Dictionary structure from BaziCalculator.get_chart()
        """
        self.chart = chart
        self.scores = {"Mu": 0, "Huo": 0, "Tu": 0, "Jin": 0, "Shui": 0}
        self.day_master = chart['day']['stem']
        self.day_master_element = self.get_wuxing(self.day_master)

    def get_wuxing(self, char):
        return self.WU_XING_MAP.get(char, "Unknown")

    def calculate_strength(self):
        # Reset scores
        self.scores = {k: 0 for k in self.scores}

        # 1. Process Stems (Top row)
        for pillar, weight in [("year", 10), ("month", 12), ("hour", 12)]: # Skip Day Stem
            stem = self.chart[pillar]['stem']
            element = self.get_wuxing(stem)
            if element in self.scores:
                self.scores[element] += weight

        # 2. Process Branches (Bottom row, with Hidden Stems)
        for pillar in ["year", "month", "day", "hour"]:
            branch = self.chart[pillar]['branch']
            weight_key = f"{pillar}_branch"
            total_pillar_weight = self.POSITION_WEIGHTS.get(weight_key, 15)
            
            # Get hidden stems distribution
            hiddens = self.HIDDEN_STEMS_MAP.get(branch, {})
            
            for stem_char, ratio in hiddens.items():
                element = self.get_wuxing(stem_char)
                if element in self.scores:
                     # e.g. Month Branch (40) * Ratio (0.6) = 24 points to Main Qi
                    self.scores[element] += total_pillar_weight * ratio

        # 3. Calculate Day Master Status
        # Comparison: (Self + Generating) vs (Discharging + Controlling)
        self_score = self.scores[self.day_master_element]
        
        # Add "Day Master" constant base score? Usually we consider the environment.
        # Let's say Day Stem itself has intrinsic presence, maybe add theoretical 10 points usually excluded.
        self_score += 10 
        self.scores[self.day_master_element] = self_score # Update global score

        mother_element = [k for k, v in self.RELATIONSHIPS["Sheng"].items() if v == self.day_master_element][0]
        mother_score = self.scores[mother_element]

        strong_side = self_score + mother_score
        total_score = sum(self.scores.values())
        weak_side = total_score - strong_side
        
        # Strength threshold: usually ~40-50% depending on sect. Let's use 50% for neutral.
        # But Month Command is huge. If Self is born in Season, usually Strong.
        
        is_strong = strong_side >= (total_score * 0.45) # Slight bias to Weak if not commanding season

        return {
            "scores": self.scores,
            "total": total_score,
            "day_master": {
                "element": self.day_master_element,
                "score": self_score,
                "status": "Strong (Shen Qiang)" if is_strong else "Weak (Shen Ruo)",
                "percentage": (self_score / total_score) * 100 if total_score > 0 else 0
            },
            "strong_side_pct": (strong_side / total_score) * 100 if total_score > 0 else 0
        }

    def analyze_flow(self):
        """
        Analyze flow: Year -> Month -> Day -> Hour
        """
        flow = []
        pillars = ["year", "month", "day", "hour"]
        
        # Simple analysis of Stem Flow
        for i in range(len(pillars) - 1):
            curr_p = pillars[i]
            next_p = pillars[i+1]
            
            curr_elem = self.get_wuxing(self.chart[curr_p]['stem'])
            next_elem = self.get_wuxing(self.chart[next_p]['stem'])
            
            relation = "Neutral"
            if self.RELATIONSHIPS["Sheng"].get(curr_elem) == next_elem:
                relation = "Sheng (Generate)"
            elif self.RELATIONSHIPS["Ke"].get(curr_elem) == next_elem:
                relation = "Ke (Control)"
            elif self.RELATIONSHIPS["Sheng"].get(next_elem) == curr_elem:
                relation = "Being Generated (Backward)"
            elif self.RELATIONSHIPS["Ke"].get(next_elem) == curr_elem:
                relation = "Being Controlled (Backward)"
                
            flow.append(f"{curr_p.capitalize()} ({curr_elem}) -> {next_p.capitalize()} ({next_elem}): {relation}")
            
        return flow
