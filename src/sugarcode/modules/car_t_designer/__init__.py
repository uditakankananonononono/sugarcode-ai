"""CAR-T construct design: curated antigen/scFv panels with expression-risk and persistence scoring."""
from .core import design_car, antigen_selectivity, logic_gate_response, exhaustion_trajectory, killing_curve, car_report
__all__=['design_car','antigen_selectivity','logic_gate_response','exhaustion_trajectory','killing_curve','car_report']
