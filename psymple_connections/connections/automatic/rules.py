from typing import TypedDict

class Rule(dict):
    rule: str
    ports: set[str]

    def apply(self, all_ports: set[str]):
        rule = self.get("rule", "none")
        ports = self.get("ports", set())
        if rule == "all":
            return all_ports
        elif rule == "none":
            return set()
        elif rule == "only":
            return ports & all_ports
        elif rule == "all_except":
            return all_ports - ports
        else:
            raise ValueError(f"Unknown rule: {rule}")
        
class SearchRule(Rule):
    pass

class ExposeRule(Rule):
    aliases: dict | list[dict]

    def apply(self, all_ports: set[str]):
        ports = super().apply(all_ports)
        aliases = self.get("aliases", {})
        if isinstance(aliases, list):
            pass
        elif isinstance(aliases, dict):
            pass
        else:
            raise ValueError(f"Aliases must be a list or a dict, not {aliases}.")