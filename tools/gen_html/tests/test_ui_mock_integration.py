#!/usr/bin/env python3
"""UI Mock — integration into md→HTML pipeline. Stage ⑨ of 11.

Validates that fenced markdown blocks of:
  - ` ```ui-mock ` → DSL parser → renderer
  - ` ``` ` (no language) with box-drawing chars → ASCII parser → renderer
  - ` ```ascii ` etc. with non-box content → unchanged <pre> output
  - ` ```ui-mock ` with malformed content → silent <pre> fallback
all flow correctly through `gen_html.md_to_html()`.
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
GEN_HTML = REPO / 'tools' / 'gen_html' / 'gen_html.py'

spec = importlib.util.spec_from_file_location('gh', GEN_HTML)
gh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gh)


def test_dsl_fenced_block_renders_via_md_to_html():
    md = '''Some intro text.

```ui-mock
modal title:"Edit" closable {
    field label:"Name" required {
        input placeholder:"..."
    }
    actions {
        button "Cancel" variant:secondary
        button "Save" variant:primary
    }
}
```

After block.'''
    html = gh.md_to_html(md)
    # DSL recognized
    assert 'umock__modal' in html
    assert 'umock__field' in html
    assert 'umock__btn--primary' in html
    # Surrounding text preserved
    assert 'Some intro text' in html
    assert 'After block' in html
    # No raw DSL leakage
    assert 'closable' not in html.split('umock__modal')[0]
    # No raw braces in content area
    body = html.split('umock__modal')[1]
    assert '{' not in body.split('After block')[0]


def test_ascii_fenced_block_with_box_drawing_renders_as_ui_mock():
    md = '''Below is a modal:

```
┌────────────────────────────────────┐
│ ⚠ Confirm Delete             [X] │
├────────────────────────────────────┤
│ Are you sure?                      │
├────────────────────────────────────┤
│            [Cancel] [Delete]（Danger）│
└────────────────────────────────────┘
```

After.'''
    html = gh.md_to_html(md)
    # Should be detected as a modal
    assert 'umock__modal' in html
    assert 'Confirm Delete' in html
    # Buttons rendered
    assert 'umock__btn' in html
    assert 'Cancel' in html and 'Delete' in html
    # Danger variant from the （Danger） hint
    assert 'umock__btn--danger' in html
    # No raw ASCII chars
    for c in '┌┐└┘├┤':
        # Ensure no leakage in content area (header titles may contain them
        # but for this test there shouldn't be any)
        assert c not in html


def test_ascii_fenced_no_box_drawing_stays_as_pre():
    """Plain text fenced block (no box chars) → remain <pre>."""
    md = '''```
just plain text
no box chars here
```'''
    html = gh.md_to_html(md)
    assert '<pre>' in html
    assert 'plain text' in html


def test_language_tagged_fenced_block_unaffected():
    """A ```python block should NOT be parsed as ui-mock even if it
    happens to contain box-drawing chars."""
    md = '''```python
# look ┌──┐
print("hello")
```'''
    html = gh.md_to_html(md)
    assert '<pre><code class="language-python">' in html
    # Should escape but not parse as UI mock
    assert 'umock__' not in html


def test_dsl_block_malformed_falls_back_silently():
    """Per user spec: silent fallback. Malformed DSL → empty/best-effort
    rendering (no error message in HTML)."""
    md = '''```ui-mock
this is not valid DSL { unclosed
```'''
    html = gh.md_to_html(md)
    # Must not crash; output is bounded — no `ERROR` / `WARNING` text
    for word in ['ERROR', 'WARNING', 'unsupported']:
        assert word not in html


def test_real_world_pet_pyramid_block_in_md():
    md = '''## Test Pyramid

```
              ┌─────────────┐
              │  E2E Tests  │
              │   5–10%     │
         ┌────┴─────────────┴────┐
         │  Integration Tests    │
         │     20–30%            │
    ┌────┴───────────────────────┴────┐
    │  Unit Tests                     │
    │     60–70%                      │
    └─────────────────────────────────┘
```

Above is the pyramid.'''
    html = gh.md_to_html(md)
    assert '<svg' in html
    polys = html.count('<polygon')
    assert polys == 3
    assert 'E2E Tests' in html
    assert 'Integration Tests' in html
    assert 'Unit Tests' in html


def test_real_world_pet_layered_arch_block_in_md():
    md = '''## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Presentation Layer                                 │
│                      ↓ calls                        │
├─────────────────────────────────────────────────────┤
│  Application Layer                                  │
│                      ↓ uses                         │
├─────────────────────────────────────────────────────┤
│  Domain Layer                                       │
└─────────────────────────────────────────────────────┘
```'''
    html = gh.md_to_html(md)
    # Mermaid block expected
    assert 'flowchart TB' in html
    assert 'Presentation Layer' in html
    assert 'Application Layer' in html
    assert 'Domain Layer' in html


def test_css_classes_present_in_template():
    """The umock CSS block must be in the inline <style> embedded by
    gen_html template."""
    src = pathlib.Path(GEN_HTML).read_text()
    assert '.umock' in src
    assert '.umock__btn' in src
    assert '.umock__modal' in src
    assert '.umock__pyramid' in src


def main() -> int:
    print('=' * 78)
    print(f'UI MOCK INTEGRATION (stage 9)  source={GEN_HTML}')
    print('=' * 78)
    tests = [
        ('dsl_fenced_block', test_dsl_fenced_block_renders_via_md_to_html),
        ('ascii_fenced_box', test_ascii_fenced_block_with_box_drawing_renders_as_ui_mock),
        ('ascii_no_box_pre', test_ascii_fenced_no_box_drawing_stays_as_pre),
        ('lang_tagged_unaffected', test_language_tagged_fenced_block_unaffected),
        ('malformed_dsl_fallback', test_dsl_block_malformed_falls_back_silently),
        ('real_world_pyramid', test_real_world_pet_pyramid_block_in_md),
        ('real_world_layered_arch', test_real_world_pet_layered_arch_block_in_md),
        ('css_present', test_css_classes_present_in_template),
    ]
    passed = failed = 0
    for name, fn in tests:
        try:
            fn()
            passed += 1
            print(f'  ✅ [{name}]')
        except AssertionError as e:
            failed += 1
            print(f'  ❌ [{name}] {e}')
        except Exception as e:
            failed += 1
            print(f'  ❌ [{name}] EXCEPTION {type(e).__name__}: {e}')
    print('\n' + '=' * 78)
    print(f'TOTAL: {passed} PASS / {failed} FAIL  ({len(tests)} cases)')
    print('=' * 78)
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
