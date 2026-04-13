import argparse
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scripts"))

from survey.agent import run_followup_agent
from django_api import get_all_patients, get_patient_by_name


def _select_patient(patient_name=None):
    if patient_name:
        return get_patient_by_name(patient_name)

    patients = get_all_patients()
    if not patients:
        return None
    return patients[0]


def main(patient_name=None):
    patient_info = _select_patient(patient_name=patient_name)
    if not patient_info:
        print("未找到患者信息，请先在系统中录入患者。")
        return 1

    result = run_followup_agent(patient_info=patient_info, history_records=[])
    print("=== 自动随访执行完成 ===")
    print(result["dialogue_history"])
    print("\n=== 跟进决策 ===")
    print(result["decision"])
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="自动随访执行入口")
    parser.add_argument("--patient-name", help="指定患者姓名，不传则默认使用第一个患者")
    args = parser.parse_args()
    raise SystemExit(main(patient_name=args.patient_name))