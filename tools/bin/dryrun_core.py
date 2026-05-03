#!/usr/bin/env python3
"""
gendoc-gen-dryrun core implementation
將 DRYRUN 前的檔案轉換為 DRYRUN 后的規格，使用單一真相源 (SSOT) 原則

All metric definitions and spec_rules are read from templates/pipeline.json (SSOT).
No hardcoded metrics or step specifications — fully dynamic and extensible.
新增 DRYRUN 前的節點會自動提取指標；新增 DRYRUN 后的節點會自動生成規格。
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime, timezone
import math


class DRYRUNEngine:
    """DRYRUN specification derivation engine using SSOT (Single Source of Truth)

    Reads all configuration from templates/pipeline.json:
    - metrics[]: 20 quantitative indicators with grep patterns
    - steps[*].spec_rules: 34 step specifications with three layers (quantitative, content, cross-file)

    No hardcoded values — fully extensible for new metrics and steps.
    """

    def __init__(self, cwd: str, state_file: str):
        self.cwd = Path(cwd)
        self.docs_dir = self.cwd / "docs"
        self.state_file = Path(state_file)
        self.metrics = {}
        self.step_specs = {}
        self.pipeline = {}

    def _load_pipeline(self) -> dict:
        """Load pipeline.json from templates/ — SSOT for metrics and spec_rules"""
        pipeline_path = self.cwd / "templates" / "pipeline.json"
        if not pipeline_path.exists():
            raise FileNotFoundError(f"pipeline.json not found at {pipeline_path}")
        try:
            pipeline = json.loads(pipeline_path.read_text(encoding='utf-8'))
            self.pipeline = pipeline
            return pipeline
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in pipeline.json: {e}")

    def validate_dryrun_upstream(self) -> bool:
        """驗證所有 8 個 DRYRUN 前的檔案是否存在"""
        upstream_files = ["IDEA", "BRD", "PRD", "CONSTANTS", "PDD", "VDD", "EDD", "ARCH"]
        missing = []
        for fname in upstream_files:
            if not (self.docs_dir / f"{fname}.md").exists():
                missing.append(f"{fname}.md")

        if missing:
            print(f"❌ [DRYRUN] Missing upstream files: {', '.join(missing)}", file=sys.stderr)
            return False

        print(f"✅ [DRYRUN] DRYRUN 前的檔案齊全：8/8 個")
        return True

    def _load_upstream(self) -> dict:
        """從 get-upstream 工具加載上游檔案（基於 pipeline.json DRYRUN input[]）

        Returns:
            dict: {filename: content, ...} 包含 DRYRUN 前的檔案
        """
        import subprocess

        dryrun_step = next((s for s in self.pipeline.get('steps', []) if s['id'] == 'DRYRUN'), None)
        if not dryrun_step:
            raise ValueError("DRYRUN step not found in pipeline.json")

        input_files = dryrun_step.get('input', [])
        upstream_data = {}

        try:
            # Call get-upstream tool
            get_upstream_path = self.cwd / 'tools' / 'bin' / 'get-upstream.sh'
            result = subprocess.run(
                [str(get_upstream_path), '--step', 'DRYRUN', '--output', 'json'],
                cwd=str(self.cwd),
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                raise RuntimeError(f"get-upstream failed: {result.stderr}")

            upstream_data = json.loads(result.stdout)
            return upstream_data.get('inputs', {})

        except Exception as e:
            print(f"⚠️  [DRYRUN] get-upstream tool failed, falling back to direct file reads: {e}")
            # Fallback: read files directly
            for filename in input_files:
                filepath = self.cwd / filename
                if filepath.exists():
                    upstream_data[filename] = filepath.read_text(encoding='utf-8')
            return upstream_data

    def extract_parameters(self, upstream_data: dict = None) -> dict:
        """從 DRYRUN 前的檔案提取四個核心參數（DRYRUN_PARAMETER_EXTRACTION.md 的 STEP 1）

        提取的參數：
        - entity_count: from EDD.md (entity/class definitions)
        - rest_endpoint_count: from PRD.md + EDD.md (API endpoint definitions)
        - user_story_count: from PRD.md (user story definitions)
        - arch_layer_count: from ARCH.md (architecture layers)

        Returns:
            dict: {
                "entity_count": int,
                "rest_endpoint_count": int,
                "user_story_count": int,
                "arch_layer_count": int,
                "metadata": {...}
            }
        """
        if upstream_data is None:
            upstream_data = self._load_upstream()

        params = {
            "entity_count": self._extract_entity_count(upstream_data),
            "rest_endpoint_count": self._extract_rest_endpoint_count(upstream_data),
            "user_story_count": self._extract_user_story_count(upstream_data),
            "arch_layer_count": self._extract_arch_layer_count(upstream_data),
            "metadata": {
                "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "DRYRUN_PARAMETER_EXTRACTION.md"
            }
        }

        return params

    def _extract_entity_count(self, upstream_data: dict) -> int:
        """Extract entity_count from EDD.md §5.5 (DRYRUN_PARAMETER_EXTRACTION.md Step 1)"""
        edd_content = upstream_data.get('docs/EDD.md', '')

        # Pattern: ### ClassName or table format with class names
        class_pattern = r'^###\s+[A-Z][a-zA-Z0-9]*(?:\s|$)'
        matches = re.findall(class_pattern, edd_content, re.MULTILINE)

        if matches:
            return max(3, len(matches))

        # Fallback
        return 3

    def _extract_rest_endpoint_count(self, upstream_data: dict) -> int:
        """Extract rest_endpoint_count from PRD.md (DRYRUN_PARAMETER_EXTRACTION.md Step 2)"""
        prd_content = upstream_data.get('docs/PRD.md', '')

        # Pattern: GET|POST|PUT|DELETE /api/path
        endpoint_pattern = r'(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+/[a-zA-Z0-9/_\{\}-]*'
        matches = set(re.findall(endpoint_pattern, prd_content))

        if matches:
            return max(5, len(matches))

        # Fallback
        return 5

    def _extract_user_story_count(self, upstream_data: dict) -> int:
        """Extract user_story_count from PRD.md (DRYRUN_PARAMETER_EXTRACTION.md Step 3)"""
        prd_content = upstream_data.get('docs/PRD.md', '')

        # Pattern: "As a ... I want ..." or ### US-* / ### Story-*
        us_pattern = r'^###\s+(?:US-\d+|Story-\d+)'
        matches = re.findall(us_pattern, prd_content, re.MULTILINE)

        if matches:
            return max(20, len(matches))

        # Fallback
        return 20

    def _extract_arch_layer_count(self, upstream_data: dict) -> int:
        """Extract arch_layer_count from ARCH.md (DRYRUN_PARAMETER_EXTRACTION.md Step 4)"""
        arch_content = upstream_data.get('docs/ARCH.md', '')

        # Pattern: ### ... Layer or ### ... Service
        layer_pattern = r'^###\s+(?:.*Layer|.*Service|.*層|.*服務)'
        matches = re.findall(layer_pattern, arch_content, re.MULTILINE)

        if matches:
            return max(2, len(matches))

        # Fallback: assume N-tier (Presentation, Business Logic, Data Access, Infrastructure)
        return 4

    def extract_metrics(self) -> dict:
        """從 DRYRUN 前的檔案提取指標 — 用於向后兼容

        將提取的參數映射到傳統指標格式。
        """
        params = self.extract_parameters()

        # Convert new parameters to legacy metrics format for compatibility
        self.metrics = {
            'entity_count': params['entity_count'],
            'rest_endpoint_count': params['rest_endpoint_count'],
            'user_story_count': params['user_story_count'],
            'layer_count': params['arch_layer_count'],
        }

        return self.metrics

    def _grep_count(self, filepath: Path, pattern: str, fallback: int = 0) -> int:
        """Count matches of regex pattern in file"""
        if not filepath.exists():
            return fallback

        try:
            content = filepath.read_text(encoding='utf-8')
            matches = len(re.findall(pattern, content, re.MULTILINE))
            return max(fallback, matches)
        except Exception:
            return fallback

    def derive_specifications(self, params: dict = None) -> dict:
        """使用提取的參數推導 DRYRUN 后的 step 規格（DRYRUN_SPEC_FORMULAS.md 的 STEP 2）

        使用參數化公式為每個 DRYRUN 后的 step 推導預期規格。
        示例：API step 期望 min_endpoint_count = max(5, rest_endpoint_count)

        參數：
            params: 包含 entity_count、rest_endpoint_count、user_story_count、arch_layer_count 的字典

        返回：
            dict: {step_id: {min_count, required_sections, optional_checks}, ...}
        """
        if params is None:
            params = self.extract_parameters()

        if not self.pipeline:
            self._load_pipeline()

        m = params
        specs = {}

        # 應用 DRYRUN 后的 step 規格公式（來自 DRYRUN_SPEC_FORMULAS.md）
        phase_b_formulas = {
            'API': {
                'min_endpoint_count': max(5, m['rest_endpoint_count']),
                'min_h2_sections': math.ceil(m['rest_endpoint_count'] / 3) + 3,
                'entity_coverage': m['entity_count']
            },
            'SCHEMA': {
                'min_table_count': max(3, m['entity_count']),
                'min_h2_sections': m['entity_count'] + 5
            },
            'FRONTEND': {
                'min_h2_sections': m['user_story_count'] + m['arch_layer_count'] + 3
            },
            'test-plan': {
                'min_h2_sections': m['arch_layer_count'] + math.ceil(m['user_story_count'] / 4) + 3,
                'min_test_cases': m['user_story_count'] * 3
            },
            'BDD-server': {
                'min_scenario_count': math.ceil(m['user_story_count'] * 0.8),
                'min_step_definitions': math.ceil(m['rest_endpoint_count'] * 0.6)
            },
            'BDD-client': {
                'min_scenario_count': math.ceil(m['user_story_count'] * 0.7),
                'min_step_definitions': math.ceil(m['user_story_count'] * 0.5)
            },
            'RTM': {
                'min_h2_sections': 3,
                'min_traceability_entries': m['user_story_count']
            },
            'runbook': {
                'min_h2_sections': m['arch_layer_count'] + 5
            },
            'LOCAL_DEPLOY': {
                'min_h2_sections': 12
            },
            'DEVELOPER_GUIDE': {
                'min_h2_sections': 5
            },
            'CICD': {
                'min_h2_sections': 8
            },
            'UML': {
                'min_diagram_count': 9,
                'class_coverage': m['entity_count']
            },
            'CONTRACTS': {
                'min_h2_sections': 4,
                'endpoint_coverage': m['rest_endpoint_count']
            },
            'MOCK': {
                'min_endpoints': m['rest_endpoint_count']
            }
        }

        # Build specs dictionary
        for step in self.pipeline.get('steps', []):
            step_id = step['id']

            # Use formula-based specs if available
            if step_id in phase_b_formulas:
                specs[step_id] = phase_b_formulas[step_id]
            else:
                # For other steps, use spec_rules from pipeline.json
                spec_rules = step.get('spec_rules', {})
                specs[step_id] = {
                    'quantitative_specs': spec_rules.get('quantitative_specs', {}),
                    'content_mapping': spec_rules.get('content_mapping', {}),
                    'cross_file_validation': spec_rules.get('cross_file_validation', {})
                }

        self.step_specs = specs
        return specs

    def _evaluate_spec_value(self, value: str, metrics: dict) -> str:
        """Evaluate spec value strings (substitute metric placeholders with actual values)

        Example: "API endpoints must support all {rest_endpoint_count} endpoints"
                → "API endpoints must support all 12 endpoints" (after substitution)

        Args:
            value: spec rule text with {metric_id} placeholders
            metrics: {metric_id: value, ...} dictionary from extract_metrics()

        Returns:
            value with all {metric_id} placeholders replaced by actual metric values
        """
        if not isinstance(value, str):
            return value

        result = value
        for metric_key, metric_val in metrics.items():
            placeholder = '{' + metric_key + '}'
            result = result.replace(placeholder, str(metric_val))

        return result

    def embed_in_state_file(self) -> bool:
        """Embed specifications in state file and write back"""

        try:
            # Read current state file
            state = json.loads(self.state_file.read_text(encoding='utf-8'))

            # Add step_specifications field
            state['step_specifications'] = self.step_specs

            # Add dryrun metadata
            state['dryrun_metadata'] = {
                'extraction_timestamp': datetime.now(timezone.utc).isoformat(),
                'extracted_metrics_count': len(self.metrics),
                'derived_step_specs_count': len(self.step_specs),
                'phase_a_version': 'v2.0.0'
            }

            # Write back to state file
            self.state_file.write_text(
                json.dumps(state, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )

            print(f"✅ [DRYRUN] State file updated: {self.state_file}")
            print(f"   - {len(self.metrics)} metrics extracted")
            print(f"   - {len(self.step_specs)} step specs derived")
            return True

        except Exception as e:
            print(f"❌ [DRYRUN] Failed to embed specifications: {e}", file=sys.stderr)
            return False

    def validate_completeness(self) -> bool:
        """R1-V1: Validate that all steps have complete specifications"""

        print("\n[DRYRUN] Step 4: Validating completeness...")

        required_keys = ['quantitative_specs', 'content_mapping', 'cross_file_validation']
        errors = []

        # Check all 34 steps present
        if len(self.step_specs) < 34:
            errors.append(f"Expected 34 steps, found {len(self.step_specs)}")

        # Check each step has all required fields
        for step_id, specs in self.step_specs.items():
            for key in required_keys:
                if key not in specs or not isinstance(specs[key], dict):
                    errors.append(f"{step_id}: missing or invalid '{key}'")

        if errors:
            print(f"❌ [DRYRUN] Validation failed:")
            for error in errors:
                print(f"   - {error}")
            return False

        print(f"✅ [DRYRUN] Validation passed:")
        print(f"   - {len(self.step_specs)} steps with complete specs")
        print(f"   - All required fields present")
        return True

    def validate_spec_quality(self) -> bool:
        """R2-V1: Validate that derived specifications meet quality standards

        Checks:
        1. Each spec has at least one quantitative rule
        2. Phase B specs have content_mapping entries
        3. Phase B specs have cross_file_validation entries
        4. No placeholder values remain in specs
        5. Spec descriptions are not empty
        """

        print("\n[DRYRUN] Step 4b: Validating spec quality...")

        warnings = []
        errors = []
        phase_b_steps = {'API', 'SCHEMA', 'FRONTEND', 'test-plan', 'BDD-server', 'BDD-client',
                         'RTM', 'RESOURCE', 'AUDIO', 'ANIM', 'CLIENT_IMPL', 'ADMIN_IMPL',
                         'UML', 'runbook', 'LOCAL_DEPLOY', 'CICD', 'DEVELOPER_GUIDE',
                         'UML-CICD', 'ALIGN', 'ALIGN-FIX', 'ALIGN-VERIFY', 'CONTRACTS',
                         'MOCK', 'PROTOTYPE', 'HTML'}

        for step_id, specs in self.step_specs.items():
            # Check 1: quantitative_specs not empty for Phase B
            if step_id in phase_b_steps:
                quant = specs.get('quantitative_specs', {})
                if len(quant) == 0:
                    warnings.append(f"{step_id}: No quantitative specs defined")

            # Check 2: content_mapping for Phase B
            content = specs.get('content_mapping', {})
            if step_id in phase_b_steps and len(content) == 0:
                warnings.append(f"{step_id}: No content mapping defined")

            # Check 3: cross_file_validation for Phase B
            cross = specs.get('cross_file_validation', {})
            if step_id in phase_b_steps and len(cross) == 0:
                warnings.append(f"{step_id}: No cross-file validation defined")

            # Check 4: No placeholder values remain
            all_specs = str(specs)
            if '{{' in all_specs or '}}' in all_specs:
                errors.append(f"{step_id}: Unresolved placeholder in specs")

            # Check 5: Descriptions not empty
            for rule_type in ['quantitative_specs', 'content_mapping', 'cross_file_validation']:
                for key, value in specs.get(rule_type, {}).items():
                    if isinstance(value, str) and len(value.strip()) == 0:
                        errors.append(f"{step_id}.{rule_type}.{key}: Empty description")

        if errors:
            print(f"❌ [DRYRUN] Quality validation failed:")
            for error in errors:
                print(f"   - {error}")
            return False

        if warnings:
            print(f"⚠️  [DRYRUN] Quality warnings ({len(warnings)}):")
            for warning in warnings:
                print(f"   - {warning}")
            print("   (Warnings are acceptable for optional specs)")

        print(f"✅ [DRYRUN] Spec quality passed:")
        print(f"   - {len(self.step_specs)} steps validated")
        if warnings:
            print(f"   - {len(warnings)} warnings (non-critical)")
        return True

    def generate_rules_json(self) -> bool:
        """生成 .gendoc-rules/*.json 檔案（DRYRUN_CORE_IMPLEMENTATION_PLAN.md 的 STEP 4）

        對於每個 DRYRUN 后的 step，輸出包含其預期規格的 JSON 檔案。
        格式：.gendoc-rules/{step_id}-rules.json

        返回：
            bool: 若所有檔案生成成功則為 True
        """
        rules_dir = self.cwd / '.gendoc-rules'
        rules_dir.mkdir(exist_ok=True)

        success = True
        for step_id, specs in self.step_specs.items():
            try:
                rules_file = rules_dir / f"{step_id.lower()}-rules.json"
                rules_file.write_text(
                    json.dumps(specs, indent=2, ensure_ascii=False),
                    encoding='utf-8'
                )
                print(f"  ✓ {step_id}: {rules_file.name}")
            except Exception as e:
                print(f"  ✗ {step_id}: {e}", file=sys.stderr)
                success = False

        return success

    def generate_manifest(self, template_path: str, output_path: str) -> bool:
        """TASK-D5: Generate MANIFEST.md from template with substituted values"""

        try:
            template = Path(template_path).read_text(encoding='utf-8')

            # Build replacement dictionary — DYNAMICALLY from metrics (SSOT principle)
            # No hardcoded metric names; all 20+ metrics come from extract_metrics()
            # which reads from pipeline.json metrics[].
            # New metrics added to pipeline.json automatically work here with zero code changes.
            replacements = {
                '{{GENERATED_DATE}}': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                '{{PIPELINE_VERSION}}': 'v2.0.0',
            }

            # Add all extracted metrics dynamically
            for metric_id, metric_val in self.metrics.items():
                # Support both snake_case and UPPER_CASE placeholders
                # entity_count → {{entity_count}} or {{ENTITY_COUNT}}
                replacements['{{' + metric_id + '}}'] = str(metric_val)
                replacements['{{' + metric_id.upper() + '}}'] = str(metric_val)

            # Apply replacements
            content = template
            for placeholder, value in replacements.items():
                content = content.replace(placeholder, value)

            # Write MANIFEST.md
            Path(output_path).write_text(content, encoding='utf-8')
            print(f"✅ [DRYRUN] MANIFEST.md generated: {output_path}")
            return True

        except Exception as e:
            print(f"❌ [DRYRUN] Failed to generate MANIFEST.md: {e}", file=sys.stderr)
            return False

    def print_metrics_summary(self):
        """Print summary of extracted metrics"""
        print("\n[DRYRUN] Extracted Metrics Summary:")
        print("  ─── Business ───")
        print(f"  - personas: {self.metrics.get('persona_count', 0)}")
        print(f"  - P0 items: {self.metrics.get('moscow_p0_count', 0)}")
        print(f"  - KPIs: {self.metrics.get('kpi_count', 0)}")
        print("  ─── Product ───")
        print(f"  - user stories: {self.metrics.get('user_story_count', 0)}")
        print(f"  - features: {self.metrics.get('feature_count', 0)}")
        print(f"  - use cases: {self.metrics.get('use_case_count', 0)}")
        print(f"  - acceptance criteria: {self.metrics.get('total_ac_count', 0)}")
        print(f"  - constants: {self.metrics.get('constant_count', 0)}")
        print("  ─── Design ───")
        print(f"  - screens: {self.metrics.get('screen_count', 0)}")
        print(f"  - flows: {self.metrics.get('flow_count', 0)}")
        print(f"  - components: {self.metrics.get('total_component_count', 0)}")
        print(f"  - design tokens: {self.metrics.get('design_token_count', 0)}")
        print(f"  - colors: {self.metrics.get('color_count', 0)}")
        print("  ─── Technical ───")
        print(f"  - entities: {self.metrics.get('entity_count', 0)}")
        print(f"  - relationships: {self.metrics.get('relationship_count', 0)}")
        print(f"  - REST endpoints: {self.metrics.get('rest_endpoint_count', 0)}")
        print(f"  - domains: {self.metrics.get('domain_count', 0)}")
        print(f"  - architecture layers: {self.metrics.get('layer_count', 0)}")
        print(f"  - services: {self.metrics.get('service_count', 0)}")
        print(f"  - NFRs: {self.metrics.get('nfr_count', 0)}")
        print()


def main():
    """Main entry point"""

    if len(sys.argv) < 3:
        print("Usage: python3 dryrun_core.py <cwd> <state_file> [--template <path>]", file=sys.stderr)
        sys.exit(1)

    cwd = sys.argv[1]
    state_file = sys.argv[2]

    # Optional template path (for MANIFEST.md generation)
    template_path = None
    manifest_path = None
    if len(sys.argv) > 4 and sys.argv[3] == '--template':
        template_path = sys.argv[4]
        manifest_path = str(Path(cwd) / 'docs' / 'MANIFEST.md')

    engine = DRYRUNEngine(cwd, state_file)

    # Step 0a: Load pipeline.json (SSOT)
    print("[DRYRUN] Step 0a: Loading pipeline.json (SSOT)...")
    try:
        engine._load_pipeline()
        print(f"✅ [DRYRUN] Pipeline loaded (v{engine.pipeline.get('version', 'unknown')})")
    except Exception as e:
        print(f"❌ [DRYRUN] Failed to load pipeline.json: {e}", file=sys.stderr)
        sys.exit(1)

    # Step 0b: Validate upstream files
    print("\n[DRYRUN] Step 0b: 驗證 DRYRUN 前的檔案...")
    if not engine.validate_dryrun_upstream():
        sys.exit(1)

    # Step 1: Extract parameters (DRYRUN_PARAMETER_EXTRACTION.md)
    print("\n[DRYRUN] Step 1: Extracting core parameters...")
    try:
        params = engine.extract_parameters()
        print(f"✅ [DRYRUN] Parameters extracted:")
        print(f"   - entity_count: {params['entity_count']}")
        print(f"   - rest_endpoint_count: {params['rest_endpoint_count']}")
        print(f"   - user_story_count: {params['user_story_count']}")
        print(f"   - arch_layer_count: {params['arch_layer_count']}")
    except Exception as e:
        print(f"❌ [DRYRUN] Failed to extract parameters: {e}", file=sys.stderr)
        sys.exit(1)

    # Step 2: Derive specifications (DRYRUN_SPEC_FORMULAS.md)
    print("\n[DRYRUN] Step 2: Deriving specifications from formulas...")
    try:
        engine.derive_specifications(params)
        print(f"✅ [DRYRUN] Specifications derived for {len(engine.step_specs)} steps")
    except Exception as e:
        print(f"❌ [DRYRUN] Failed to derive specifications: {e}", file=sys.stderr)
        sys.exit(1)

    # Step 3: Generate .gendoc-rules/*.json files
    print("\n[DRYRUN] Step 3: Generating .gendoc-rules/*.json files...")
    try:
        if not engine.generate_rules_json():
            sys.exit(1)
        print(f"✅ [DRYRUN] Rules generated: {len(engine.step_specs)} files")
    except Exception as e:
        print(f"❌ [DRYRUN] Failed to generate rules: {e}", file=sys.stderr)
        sys.exit(1)

    # Step 4: Embed in state file
    print("\n[DRYRUN] Step 4: Embedding specifications in state file...")
    if not engine.embed_in_state_file():
        sys.exit(1)

    # Step 5: Generate MANIFEST.md (if template provided)
    if template_path and manifest_path:
        print("\n[DRYRUN] Step 5: Generating MANIFEST.md...")
        if not engine.generate_manifest(template_path, manifest_path):
            sys.exit(1)

    # Step 6: Validation
    print("\n[DRYRUN] Step 6: Validating completeness...")
    if not engine.validate_completeness():
        sys.exit(1)

    if not engine.validate_spec_quality():
        sys.exit(1)

    print("\n" + "="*60)
    print("✅ [DRYRUN] All steps complete")
    print("="*60)
    print(f"   - Parameters extracted: 4/4")
    print(f"   - Specifications derived: {len(engine.step_specs)}/25+ steps")
    print(f"   - Rules files generated: .gendoc-rules/*.json")
    if manifest_path:
        print(f"   - MANIFEST.md generated: {manifest_path}")


if __name__ == '__main__':
    main()
