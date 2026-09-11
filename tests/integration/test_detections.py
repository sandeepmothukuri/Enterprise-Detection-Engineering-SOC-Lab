import os, sys, yaml
def test_sigma_rule_syntax():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(os.path.dirname(current_dir))
    rules_dir = os.path.join(base_dir, "detections", "rules")
    required_fields = ["title", "id", "description", "author", "logsource", "detection", "level", "lab_metadata"]
    errors = []
    if not os.path.exists(rules_dir):
        print(f"ERROR: Directory {rules_dir} not found.")
        return False
    file_count = 0
    for filename in os.listdir(rules_dir):
        if filename.endswith(".yml") or filename.endswith(".yaml"):
            file_count += 1
            filepath = os.path.join(rules_dir, filename)
            with open(filepath, 'r') as f:
                try:
                    rule = yaml.safe_load(f)
                    if not isinstance(rule, dict):
                        errors.append(f"{filename}: Not a valid YAML dictionary")
                        continue
                    for field in required_fields:
                        if field not in rule:
                            errors.append(f"{filename}: Missing required field '{field}'")
                except yaml.YAMLError as e:
                    errors.append(f"{filename}: Invalid YAML syntax - {e}")
    if errors:
        print("DETECTION TEST FAILED:")
        for err in errors:
            print(f"  - {err}")
        return False
    print(f"DETECTION TEST PASSED: All {file_count} rule(s) have valid syntax and required fields.")
    return True
if __name__ == "__main__":
    success = test_sigma_rule_syntax()
    sys.exit(0 if success else 1)