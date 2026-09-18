"""Runner and validator for the CP3 Golden Set evaluation."""
from __future__ import annotations
import argparse
import io
import json
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
CANDIDATE_DIRS = [
    SCRIPT_DIR.parent,
    SCRIPT_DIR.parent / 'codebase',
    SCRIPT_DIR / 'codebase',
]
for d in CANDIDATE_DIRS:
    if (d / 'ai_service.py').exists() and str(d) not in sys.path:
        sys.path.insert(0, str(d))

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, io.UnsupportedOperation):
        pass

from ai_service import explain_selection, ServiceError, configuration

TAXONOMY_MAP = {
    'explain': 'Đặc thù nghiệp vụ & Ca thông thường',
    'clarify': 'Mơ hồ / thiếu thông tin',
    'no_grounding': 'Nguồn sự thật (thiếu dữ liệu ngữ cảnh)',
    'refuse': 'Ngoài phạm vi / thẩm quyền',
}


def find_golden_set(specified_path: str | None = None) -> Path:
    if specified_path:
        p = Path(specified_path)
        if p.exists():
            return p
        raise FileNotFoundError(f"Không tìm thấy golden set tại: {specified_path}")
    candidates = [
        SCRIPT_DIR / 'golden_set.json',
        SCRIPT_DIR.parent / 'eval' / 'golden_set.json',
        SCRIPT_DIR.parent / 'codebase' / 'eval' / 'golden_set.json',
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError("Không tìm thấy tệp eval/golden_set.json trong dự án.")


def validate_dataset(cases: list[dict]) -> bool:
    print(f"[*] Kiểm tra tính hợp lệ của bộ dữ liệu ({len(cases)} ca)...")
    if len(cases) < 20:
        print(f"[-] Lỗi: Golden set cần tối thiểu 20 ca kiểm thử (hiện có {len(cases)}).")
        return False
    required_fields = {'id', 'course_context', 'original_question', 'original_answer', 'selected_text', 'expected_action'}
    action_counts = {'explain': 0, 'clarify': 0, 'no_grounding': 0, 'refuse': 0}
    
    for i, c in enumerate(cases, 1):
        missing = required_fields - set(c.keys())
        if missing:
            print(f"[-] Ca {i} ({c.get('id', 'unknown')}) thiếu các trường: {missing}")
            return False
        action = c['expected_action']
        if action not in action_counts:
            print(f"[-] Ca {i} có expected_action không hợp lệ: {action}")
            return False
        action_counts[action] += 1

    print("[+] Cấu trúc tất cả các ca kiểm thử đều hợp lệ.")
    print("    Phân bổ theo 4 lớp chỗ khó:")
    for action, label in TAXONOMY_MAP.items():
        count = action_counts[action]
        ok = count >= 2
        status_str = "ĐẠT (>= 2)" if ok else "CHƯA ĐỦ (< 2)"
        print(f"    - {action:12} [{status_str}]: {count:2} ca ({label})")
    
    all_taxonomy_ok = all(cnt >= 2 for cnt in action_counts.values())
    return all_taxonomy_ok


def run_evaluation(cases: list[dict], output_md: Path | None = None) -> dict:
    key, model = configuration()
    if not key:
        print("[-] Lỗi: Chưa cấu hình OPENAI_API_KEY trong .env.")
        print("    Vui lòng kiểm tra file codebase/.env trước khi chạy kiểm thử mô hình thật.")
        sys.exit(1)

    print(f"[*] Bắt đầu chạy kiểm thử {len(cases)} ca qua mô hình AI thật...")
    print(f"    Model: {model}")
    print("-" * 75)

    results = []
    matched = 0
    mismatched = 0
    errors = 0

    for i, case in enumerate(cases, 1):
        cid = case['id']
        expected = case['expected_action']
        payload = {
            'course_context': case['course_context'],
            'original_question': case['original_question'],
            'original_answer': case['original_answer'],
            'selected_text': case['selected_text'],
        }

        start_time = time.perf_counter()
        actual_action = None
        error_msg = None
        category = 'pass'
        reason = 'Khớp hoàn toàn expected action.'

        try:
            res = explain_selection(payload)
            actual_action = res['result']['action']
        except ServiceError as exc:
            actual_action = f"ERROR ({exc.code})"
            error_msg = exc.message
            errors += 1
            category = 'technical_error'
            reason = f"Lỗi kỹ thuật: {exc.code}"
        except Exception as exc:
            actual_action = "ERROR"
            error_msg = str(exc)
            errors += 1
            category = 'technical_error'
            reason = f"Lỗi không xác định: {exc}"

        latency = round((time.perf_counter() - start_time) * 1000)

        is_match = (actual_action == expected)
        if is_match:
            matched += 1
            status_text = "PASS"
        else:
            if category != 'technical_error':
                mismatched += 1
                if expected == 'clarify' and actual_action == 'explain':
                    category = 'no_clarification'
                    reason = 'Kỳ vọng hỏi lại (clarify), nhưng mô hình tự giải thích (explain).'
                else:
                    category = 'wrong_action'
                    reason = f"Kỳ vọng '{expected}', mô hình trả về '{actual_action}'."
            status_text = "FAIL"

        print(f"[{i:02}/{len(cases):02}] {cid[:30]:30} | Exp: {expected:12} | Act: {str(actual_action):12} | [{status_text}] ({latency}ms)")
        results.append({
            'case': cid,
            'expected': expected,
            'actual': actual_action,
            'status': 'matched' if is_match else 'mismatched',
            'category': category,
            'reason': reason,
            'latency_ms': latency,
        })

    accuracy = (matched / len(cases)) * 100 if cases else 0.0

    print("-" * 75)
    print(f"[*] KẾT QUẢ ĐÁNH GIÁ:")
    print(f"    - Tổng số ca:       {len(cases)}")
    print(f"    - Khớp (Đạt):       {matched}")
    print(f"    - Không khớp:       {mismatched}")
    print(f"    - Lỗi kỹ thuật:     {errors}")
    print(f"    - Tỷ lệ chính xác:  {accuracy:.2f}%")
    print("-" * 75)

    if output_md:
        write_markdown_report(output_md, cases, results, matched, mismatched, errors, accuracy, model)
        print(f"[+] Đã ghi báo cáo kết quả ra tệp: {output_md}")

    return {
        'total': len(cases),
        'matched': matched,
        'mismatched': mismatched,
        'errors': errors,
        'accuracy': accuracy,
        'results': results,
    }


def write_markdown_report(output_path: Path, cases: list[dict], results: list[dict],
                          matched: int, mismatched: int, errors: int, accuracy: float, model: str):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Kết quả thực thi kiểm thử Golden Set (CP3)",
        "",
        f"- **Mô hình**: `{model}`",
        f"- **Thời gian chạy**: `{time.strftime('%Y-%m-%d %H:%M:%S')}`",
        f"- **Tổng số ca**: {len(cases)}",
        f"- **Số ca đạt (Matched)**: {matched}",
        f"- **Số ca không khớp (Mismatched)**: {mismatched}",
        f"- **Số ca lỗi kỹ thuật (Errors)**: {errors}",
        f"- **Độ chính xác (Accuracy)**: **{accuracy:.2f}%**",
        "",
        "## Bảng chi tiết từng ca kiểm thử",
        "",
        "| STT | Mã ca (ID) | Hành vi kỳ vọng (Expected) | Kết quả AI (Actual) | Trạng thái | Phân loại | Ghi chú / Nguyên nhân |",
        "|:---:|---|:---:|:---:|:---:|:---:|---|",
    ]
    for i, r in enumerate(results, 1):
        status_icon = " Đạt" if r['status'] == 'matched' else " Không đạt"
        lines.append(f"| {i} | `{r['case']}` | `{r['expected']}` | `{r['actual']}` | {status_icon} | `{r['category']}` | {r['reason']} |")

    lines.extend([
        "",
        "## Thống kê theo phân loại lỗi",
        "",
        f"- **`no_clarification`**: {sum(1 for r in results if r['category'] == 'no_clarification')} ca (Người học dùng đại từ mơ hồ hoặc cụm từ đa nghĩa nhưng AI không đặt câu hỏi làm rõ).",
        f"- **`wrong_action`**: {sum(1 for r in results if r['category'] == 'wrong_action')} ca (Ngữ cảnh bài học không hỗ trợ nhưng AI vẫn tự suy đoán giải thích).",
        f"- **`technical_error`**: {errors} ca (Lỗi kết nối, quota hoặc schema JSON).",
    ])
    output_path.write_text('\n'.join(lines), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description="Chạy kiểm thử Golden Set CP3 cho VLearn Prototype.")
    parser.add_argument('--golden-set', type=str, default=None, help="Đường dẫn tới file golden_set.json")
    parser.add_argument('--validate-only', action='store_true', help="Chỉ kiểm tra cấu trúc bộ dữ liệu mà không gọi API mô hình")
    parser.add_argument('--output', type=str, default=None, help="Đường dẫn tệp markdown ghi kết quả (VD: eval/run_results.md)")
    args = parser.parse_args()

    golden_path = find_golden_set(args.golden_set)
    cases = json.loads(golden_path.read_text(encoding='utf-8'))

    valid = validate_dataset(cases)
    if not valid:
        sys.exit(1)

    if args.validate_only:
        print("[+] Kiểm tra tính hợp lệ thành công (--validate-only).")
        return

    output_path = Path(args.output) if args.output else (golden_path.parent / 'run_results.md')
    run_evaluation(cases, output_path)


if __name__ == '__main__':
    main()
