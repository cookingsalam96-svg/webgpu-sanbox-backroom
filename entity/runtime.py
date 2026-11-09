"""HARDAM V1.1 orchestration boundary: Dreamer -> Critic -> memory/action/output."""
from entity.attention.attention_engine import rank_observations
from entity.reasoning.reasoning_engine import dreamer_propose, critic_review
from entity.memory.memory_manager import MemoryManager
from entity.action.action_controller import ActionController
from entity.validation.output_validator import validate_output

class EntityRuntime:
    """Inference-engine and renderer independent controller."""
    def __init__(self, memory=None, actions=None, dreamer=dreamer_propose):
        self.memory = memory or MemoryManager()
        self.actions = actions or ActionController()
        self.dreamer = dreamer

    def process(self, observations, *, task="", remember=False, authorize_response=True):
        if len(observations) > 20: raise ValueError("at most 20 observations are accepted")
        ranked = rank_observations(observations, task)
        ordered = [row["observation"] for row in ranked]
        proposal = self.dreamer(ordered, task)
        critic = critic_review(proposal, ordered)
        output_observations = []
        for o in ordered:
            verified = bool(o.provenance) and o.data_kind == "hardware" and o.measurement_quality == "valid" and o.evidence_class in {"E1", "E2"}
            output_observations.append({"source":o.source,"type":o.type,"value":o.value,"verified":verified,"unit":o.unit,"data_kind":o.data_kind,"provenance":o.provenance,"evidence_class":o.evidence_class})
        status = critic["status"]
        output_actions = []
        for candidate in proposal.actions[:5]:
            name = candidate.get("action") if isinstance(candidate, dict) else ""
            authorized = bool(authorize_response and name == "respond_to_user" and critic["passed"])
            result = self.actions.execute(name, authorized=authorized, validated=critic["passed"])
            output_actions.append({"action":name,"authorized":authorized,"reason":result["status"]})
        memory_result = {"write_requested":bool(remember),"write_verified":False,"record_id":None}
        if remember and critic["passed"] and ordered:
            # Preserve E5 only if every source is simulated; mixed records are hypotheses (E4).
            mem_class = "E5" if all(o.data_kind == "simulation" for o in ordered) else "E4"
            provenance = [o.provenance for o in ordered if isinstance(o.provenance, str) and o.provenance.strip()]
            try:
                record = self.memory.append("decision", proposal.assessment, [o.source for o in ordered], evidence_class=mem_class, provenance=provenance)
                memory_result = {"write_requested":True,"write_verified":True,"record_id":record["id"]}
            except (ValueError, OSError): status = "DEGRADED"
        result = {"entity_id":"hardam_entity","status":status,"observation":output_observations[:20],"assessment":(proposal.assessment if critic["passed"] else critic["reason"])[:4000],"confidence":float(max(0.0,min(1.0,proposal.confidence if critic["passed"] else 0.0))),"uncertainties":list(proposal.uncertainties[:10]),"actions":output_actions,"memory":memory_result,"validation":{"schema_valid":False,"critic_passed":bool(critic["passed"]),"source_traceable":all(bool(o.provenance) for o in ordered)}}
        valid, errors = validate_output(result)
        result["validation"]["schema_valid"] = valid
        if not valid:
            result["status"]="BLOCKED"; result["assessment"]="Output rejected by contract: "+"; ".join(errors[:5]); result["actions"]=[]; result["memory"]={"write_requested":bool(remember),"write_verified":False,"record_id":None}
        return result
