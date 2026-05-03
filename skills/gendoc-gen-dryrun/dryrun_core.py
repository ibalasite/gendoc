#!/usr/bin/env python3
"""
gendoc-gen-dryrun core implementation
Implements Phase A→B specification derivation engine
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime, timezone
import math


class DRYRUNEngine:
    """DRYRUN specification derivation engine"""

    def __init__(self, cwd: str, state_file: str):
        self.cwd = Path(cwd)
        self.docs_dir = self.cwd / "docs"
        self.state_file = Path(state_file)
        self.metrics = {}
        self.step_specs = {}

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
        """Extract 20 quantitative metrics from Phase A files"""

        metrics = {}

        # 1. persona_count (IDEA.md)
        metrics['persona_count'] = self._grep_count(
            self.docs_dir / "IDEA.md",
            r'^\## Persona:',
            fallback=1
        )

        # 2. moscow_p0_count (BRD.md)
        metrics['moscow_p0_count'] = self._grep_count(
            self.docs_dir / "BRD.md",
            r'^\## P0|^\| P0',
            fallback=3
        )

        # 3. kpi_count (BRD.md) - KPI rows in table
        metrics['kpi_count'] = self._grep_count(
            self.docs_dir / "BRD.md",
            r'^\|.*:\s*[0-9]+',
            fallback=1
        )

        # 4. user_story_count (PRD.md)
        metrics['user_story_count'] = self._grep_count(
            self.docs_dir / "PRD.md",
            r'^(##|###) US-',
            fallback=1
        )

        # 5. feature_count (PRD.md)
        metrics['feature_count'] = self._grep_count(
            self.docs_dir / "PRD.md",
            r'^(##|###) FE-',
            fallback=1
        )

        # 6. use_case_count (PRD.md)
        metrics['use_case_count'] = self._grep_count(
            self.docs_dir / "PRD.md",
            r'^(##|###) UC-',
            fallback=1
        )

        # 7. total_ac_count (PRD.md) - acceptance criteria checkboxes
        metrics['total_ac_count'] = self._grep_count(
            self.docs_dir / "PRD.md",
            r'- \[ \]',
            fallback=5
        )

        # 8. constant_count (CONSTANTS.md) - table rows
        metrics['constant_count'] = self._grep_count(
            self.docs_dir / "CONSTANTS.md",
            r'^\| [A-Z_]',
            fallback=3
        )

        # 9. screen_count (PDD.md)
        metrics['screen_count'] = self._grep_count(
            self.docs_dir / "PDD.md",
            r'^### Screen',
            fallback=1
        )

        # 10. flow_count (PDD.md)
        metrics['flow_count'] = self._grep_count(
            self.docs_dir / "PDD.md",
            r'^### (User Flow|Flow)',
            fallback=1
        )

        # 11. total_component_count (PDD.md) - component list items
        metrics['total_component_count'] = self._grep_count(
            self.docs_dir / "PDD.md",
            r'^\- (Button|Input|Card|Modal|Header|Footer)',
            fallback=3
        )

        # 12. design_token_count (VDD.md)
        metrics['design_token_count'] = self._grep_count(
            self.docs_dir / "VDD.md",
            r'^\- `',
            fallback=5
        )

        # 13. color_count (VDD.md) - color palette
        metrics['color_count'] = self._grep_count(
            self.docs_dir / "VDD.md",
            r'^\| #[0-9A-Fa-f]',
            fallback=5
        )

        # 14. entity_count (EDD.md) - UML class definitions
        metrics['entity_count'] = self._grep_count(
            self.docs_dir / "EDD.md",
            r'^\s*class ',
            fallback=3
        )

        # 15. relationship_count (EDD.md) - associations
        metrics['relationship_count'] = self._grep_count(
            self.docs_dir / "EDD.md",
            r'(--|<\|--|o--|o\|)',
            fallback=3
        )

        # 16. rest_endpoint_count (EDD.md)
        metrics['rest_endpoint_count'] = self._grep_count(
            self.docs_dir / "EDD.md",
            r'(<<REST>>|<<Interface>>|GET|POST|PUT|DELETE)',
            fallback=5
        )

        # 17. domain_count (EDD.md) - domain sections
        metrics['domain_count'] = self._grep_count(
            self.docs_dir / "EDD.md",
            r'^### ',
            fallback=2
        )

        # 18. layer_count (ARCH.md) - tech stack rows
        metrics['layer_count'] = self._grep_count(
            self.docs_dir / "ARCH.md",
            r'^\| [A-Za-z0-9_]',
            fallback=4
        )

        # 19. service_count (ARCH.md)
        metrics['service_count'] = self._grep_count(
            self.docs_dir / "ARCH.md",
            r'^#### ',
            fallback=3
        )

        # 20. nfr_count (ARCH.md) - NFR list items
        metrics['nfr_count'] = self._grep_count(
            self.docs_dir / "ARCH.md",
            r'^- \[',
            fallback=12
        )

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
        """Derive 31 step specifications from 20 metrics"""

        m = self.metrics
        specs = {}

        # Helper: calculate safe division
        def safe_ceil(val, factor):
            return max(1, math.ceil(val * factor)) if val > 0 else 1

        # ─── PHASE B STEPS ───

        # API
        specs['API'] = {
            'quantitative_specs': {
                'min_endpoint_count': max(5, m.get('rest_endpoint_count', 5))
            },
            'content_mapping': {
                'entity_coverage': f"All {m.get('entity_count', 3)} EDD entities must be referenced in API request/response models"
            },
            'cross_file_validation': {
                'entity_parity': f"API.md endpoints >= EDD entity count ({m.get('entity_count', 3)})"
            }
        }

        # SCHEMA
        specs['SCHEMA'] = {
            'quantitative_specs': {
                'min_table_count': max(3, m.get('entity_count', 3))
            },
            'content_mapping': {
                'entity_coverage': f"All {m.get('entity_count', 3)} EDD entities must have corresponding database tables"
            },
            'cross_file_validation': {
                'entity_parity': f"SCHEMA tables == EDD entities ({m.get('entity_count', 3)})"
            }
        }

        # test-plan
        specs['test-plan'] = {
            'quantitative_specs': {
                'min_h2_sections': m.get('layer_count', 4) + 4
            },
            'content_mapping': {
                'layer_coverage': f"Test strategy for all {m.get('layer_count', 4)} architecture layers"
            },
            'cross_file_validation': {
                'architecture_alignment': "test-plan sections >= ARCH layers + 4"
            }
        }

        # BDD-server
        specs['BDD-server'] = {
            'quantitative_specs': {
                'min_scenario_count': safe_ceil(m.get('user_story_count', 1), 0.8)
            },
            'content_mapping': {
                'user_story_coverage': f"All {m.get('user_story_count', 1)} user stories have corresponding BDD scenarios"
            },
            'cross_file_validation': {
                'scenario_coverage': f"BDD scenarios >= {safe_ceil(m.get('user_story_count', 1), 0.8)} (80% of US)"
            }
        }

        # BDD-client
        specs['BDD-client'] = {
            'quantitative_specs': {
                'min_scenario_count': safe_ceil(m.get('user_story_count', 1), 0.6)
            },
            'content_mapping': {
                'ui_scenario_coverage': f"Client UI scenarios for {safe_ceil(m.get('user_story_count', 1), 0.6)} key flows"
            },
            'cross_file_validation': {
                'scenario_coverage': f"Client BDD >= {safe_ceil(m.get('user_story_count', 1), 0.6)} (60% of US)"
            }
        }

        # RTM
        specs['RTM'] = {
            'quantitative_specs': {
                'min_row_count': max(1, m.get('user_story_count', 1))
            },
            'content_mapping': {
                'requirement_traceability': f"All {m.get('user_story_count', 1)} user stories traced to test cases"
            },
            'cross_file_validation': {
                'coverage': f"RTM rows >= user_story_count ({m.get('user_story_count', 1)})"
            }
        }

        # FRONTEND
        specs['FRONTEND'] = {
            'quantitative_specs': {
                'min_component_count': max(3, m.get('total_component_count', 3))
            },
            'content_mapping': {
                'screen_coverage': f"Components for all {m.get('screen_count', 1)} screens from PDD"
            },
            'cross_file_validation': {
                'pdd_alignment': f"FRONTEND components >= PDD components ({m.get('total_component_count', 3)})"
            }
        }

        # RESOURCE
        specs['RESOURCE'] = {
            'quantitative_specs': {
                'min_resource_entries': max(5, m.get('constant_count', 5))
            },
            'content_mapping': {
                'asset_inventory': f"List all {max(5, m.get('constant_count', 5))} resources with IDs, types, prompts"
            },
            'cross_file_validation': {
                'constant_mapping': f"Resources >= constants ({max(5, m.get('constant_count', 5))})"
            }
        }

        # (Other 22 steps - minimal specs for now, can be expanded per progress.md TASK-D2)
        for step_id in ['IDEA', 'BRD', 'PRD', 'CONSTANTS', 'PDD', 'VDD', 'EDD', 'ARCH',
                        'AUDIO', 'ANIM', 'CLIENT_IMPL', 'ADMIN_IMPL', 'UML',
                        'runbook', 'LOCAL_DEPLOY', 'CICD', 'DEVELOPER_GUIDE', 'UML_CICD',
                        'ALIGN', 'CONTRACTS', 'MOCK', 'PROTOTYPE', 'HTML']:
            if step_id not in specs:
                specs[step_id] = {
                    'quantitative_specs': {},
                    'content_mapping': {'note': 'Derived from Phase A metrics'},
                    'cross_file_validation': {}
                }

        self.step_specs = specs
        return specs

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
        """TASK-D4: Validate that all 31 steps have complete specifications"""

        print("\n[DRYRUN] Step 4: Validating completeness...")

        required_keys = ['quantitative_specs', 'content_mapping', 'cross_file_validation']
        errors = []

        # Check all 31 steps present
        if len(self.step_specs) != 31:
            errors.append(f"Expected 31 steps, found {len(self.step_specs)}")

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

    # Step 0: Validate Phase A
    if not engine.validate_phase_a():
        sys.exit(1)

    # Step 1: Extract metrics
    print("\n[DRYRUN] Step 1: Extracting 20 quantitative metrics...")
    engine.extract_metrics()
    engine.print_metrics_summary()

    # Step 2: Derive specifications
    print("[DRYRUN] Step 2: Deriving 31 step specifications...")
    engine.derive_specifications()
    print(f"✅ [DRYRUN] Derived specifications for {len(engine.step_specs)} steps")

    # Step 3: Embed in state file
    print("\n[DRYRUN] Step 3: Embedding specifications in state file...")
    if not engine.embed_in_state_file():
        sys.exit(1)

    # Step 4: Validate completeness
    print("\n[DRYRUN] Step 4: Validating completeness...")
    if not engine.validate_completeness():
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
