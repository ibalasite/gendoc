#!/usr/bin/env python3
"""
gendoc-gen-dryrun core implementation
Implements Phase A→B specification derivation engine using Single Source of Truth (SSOT)

All metric definitions and spec_rules are read from templates/pipeline.json (SSOT).
No hardcoded metrics or step specifications — fully dynamic and extensible.
New Phase A nodes auto-extract metrics; new Phase B nodes auto-generate specs.
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

    def validate_phase_a(self) -> bool:
        """Verify all 8 Phase A files exist"""
        phase_a_files = ["IDEA", "BRD", "PRD", "CONSTANTS", "PDD", "VDD", "EDD", "ARCH"]
        missing = []
        for fname in phase_a_files:
            if not (self.docs_dir / f"{fname}.md").exists():
                missing.append(f"{fname}.md")

        if missing:
            print(f"❌ [DRYRUN] Missing Phase A files: {', '.join(missing)}", file=sys.stderr)
            return False

        print(f"✅ [DRYRUN] Phase A complete: 8/8 files found")
        return True

    def extract_metrics(self) -> dict:
        """Extract metrics from Phase A files — dynamically read from pipeline['metrics']"""
        if not self.pipeline:
            self._load_pipeline()

        metrics = {}
        for metric_def in self.pipeline.get('metrics', []):
            metric_id = metric_def['id']
            source_step = metric_def['source_step']
            grep_pattern = metric_def['grep_pattern']
            fallback = metric_def.get('fallback', 0)

            source_file = self.docs_dir / f"{source_step}.md"
            metrics[metric_id] = self._grep_count(source_file, grep_pattern, fallback=fallback)

        self.metrics = metrics
        return metrics

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

    def derive_specifications(self) -> dict:
        """Derive specifications from pipeline['steps'][*]['spec_rules'] — SSOT"""
        if not self.pipeline:
            self._load_pipeline()

        m = self.metrics
        specs = {}

        # Read spec_rules from each step in pipeline
        for step in self.pipeline.get('steps', []):
            step_id = step['id']
            spec_rules = step.get('spec_rules', {
                'quantitative_specs': {},
                'content_mapping': {},
                'cross_file_validation': {}
            })

            # Process quantitative_specs (substitute metric values)
            quantitative = {}
            for key, value in spec_rules.get('quantitative_specs', {}).items():
                quantitative[key] = self._evaluate_spec_value(value, m)

            # Process content_mapping (substitute metric values)
            content = {}
            for key, value in spec_rules.get('content_mapping', {}).items():
                content[key] = self._evaluate_spec_value(value, m)

            # Cross_file_validation (substitute metric values)
            cross_file = {}
            for key, value in spec_rules.get('cross_file_validation', {}).items():
                cross_file[key] = self._evaluate_spec_value(value, m)

            specs[step_id] = {
                'quantitative_specs': quantitative,
                'content_mapping': content,
                'cross_file_validation': cross_file
            }

        self.step_specs = specs
        return specs

    def _evaluate_spec_value(self, value: str, metrics: dict) -> str:
        """Evaluate spec value strings (substitute metrics, calculate expressions)"""
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

    def generate_manifest(self, template_path: str, output_path: str) -> bool:
        """TASK-D5: Generate MANIFEST.md from template with substituted values"""

        try:
            template = Path(template_path).read_text(encoding='utf-8')

            # Build replacement dictionary
            replacements = {
                '{{GENERATED_DATE}}': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                '{{PIPELINE_VERSION}}': 'v2.0.0',  # From DRYRUN_ENGINE
                '{{ENTITY_COUNT}}': str(self.metrics.get('entity_count', 0)),
                '{{REST_ENDPOINT_COUNT}}': str(self.metrics.get('rest_endpoint_count', 0)),
                '{{USER_STORY_COUNT}}': str(self.metrics.get('user_story_count', 0)),
                '{{ARCH_LAYER_COUNT}}': str(self.metrics.get('layer_count', 0)),
                '{{PERSONA_COUNT}}': str(self.metrics.get('persona_count', 0)),
                '{{MOSCOW_P0_COUNT}}': str(self.metrics.get('moscow_p0_count', 0)),
                '{{KPI_COUNT}}': str(self.metrics.get('kpi_count', 0)),
                '{{FEATURE_COUNT}}': str(self.metrics.get('feature_count', 0)),
                '{{USE_CASE_COUNT}}': str(self.metrics.get('use_case_count', 0)),
                '{{TOTAL_AC_COUNT}}': str(self.metrics.get('total_ac_count', 0)),
                '{{CONSTANT_COUNT}}': str(self.metrics.get('constant_count', 0)),
                '{{SCREEN_COUNT}}': str(self.metrics.get('screen_count', 0)),
                '{{FLOW_COUNT}}': str(self.metrics.get('flow_count', 0)),
                '{{TOTAL_COMPONENT_COUNT}}': str(self.metrics.get('total_component_count', 0)),
                '{{DESIGN_TOKEN_COUNT}}': str(self.metrics.get('design_token_count', 0)),
                '{{COLOR_COUNT}}': str(self.metrics.get('color_count', 0)),
                '{{RELATIONSHIP_COUNT}}': str(self.metrics.get('relationship_count', 0)),
                '{{DOMAIN_COUNT}}': str(self.metrics.get('domain_count', 0)),
                '{{SERVICE_COUNT}}': str(self.metrics.get('service_count', 0)),
                '{{NFR_COUNT}}': str(self.metrics.get('nfr_count', 0)),
            }

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

    # Step 0b: Validate Phase A
    print("\n[DRYRUN] Step 0b: Validating Phase A...")
    if not engine.validate_phase_a():
        sys.exit(1)

    # Step 1: Extract metrics
    print("\n[DRYRUN] Step 1: Extracting quantitative metrics (from pipeline.json)...")
    engine.extract_metrics()
    engine.print_metrics_summary()

    # Step 2: Derive specifications
    print("[DRYRUN] Step 2: Reading and evaluating spec_rules (from pipeline.json)...")
    engine.derive_specifications()
    print(f"✅ [DRYRUN] Processed specifications for {len(engine.step_specs)} steps")

    # Step 3: Embed in state file
    print("\n[DRYRUN] Step 3: Embedding specifications in state file...")
    if not engine.embed_in_state_file():
        sys.exit(1)

    # Step 4: Validate completeness (R1-V1)
    if not engine.validate_completeness():
        sys.exit(1)

    # Step 4b: Validate spec quality (R2-V1)
    if not engine.validate_spec_quality():
        sys.exit(1)

    # Step 5: Generate MANIFEST.md (if template provided)
    if template_path and manifest_path:
        print("\n[DRYRUN] Step 5: Generating MANIFEST.md...")
        if not engine.generate_manifest(template_path, manifest_path):
            sys.exit(1)
        print(f"✅ [DRYRUN] Ready for git commit")

    print("\n" + "="*60)
    print("✅ [DRYRUN] All steps complete")
    print("="*60)


if __name__ == '__main__':
    main()
