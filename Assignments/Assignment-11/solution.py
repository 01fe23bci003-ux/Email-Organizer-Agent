from __future__ import annotations

import io
import unittest
from typing import Any


MESSAGES = [
    {"id": 1, "priority": "normal", "subject": "Club meeting"},
    {"id": 2, "priority": "urgent", "subject": "Exam venue update"},
]


def coding_agent_filter(messages: list[dict[str, Any]], priority: str) -> list[dict[str, Any]]:
    # Deliberate bug: compares against a constant instead of the requested priority.
    return [message for message in messages if message["priority"] == "inbox"]


def export_pdf(story_text: str) -> bytes:
    escaped_text = (
        story_text.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .encode("ascii", "replace")
    )
    stream = b"BT /F1 12 Tf 72 720 Td (" + escaped_text + b") Tj ET"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length "
        + str(len(stream)).encode("ascii")
        + b" >>\nstream\n"
        + stream
        + b"\nendstream",
    ]
    document = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, body in enumerate(objects, start=1):
        offsets.append(len(document))
        document.extend(f"{number} 0 obj\n".encode("ascii"))
        document.extend(body)
        document.extend(b"\nendobj\n")
    xref_offset = len(document)
    document.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    document.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        document.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    document.extend(
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return bytes(document)


class IndependentAcceptanceTests(unittest.TestCase):
    def test_filter_urgent(self) -> None:
        results = coding_agent_filter(MESSAGES, "urgent")
        ids = [message["id"] for message in results]
        self.assertTrue(ids == [2], f"expected urgent message id 2, got {ids}")

    def test_export_pdf(self) -> None:
        artifact = export_pdf("US-2: export to PDF")
        self.assertTrue(artifact.startswith(b"%PDF-"))
        self.assertIn(b"export to PDF", artifact)


def main() -> None:
    lineage = {
        "US-1": {"filter.py": "coding_agent"},
        "US-2": {"export_pdf.py": "coding_agent"},
    }
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=0).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(IndependentAcceptanceTests)
    )
    if any(test.id().endswith("test_filter_urgent") for test, _ in result.failures):
        actual_ids = [message["id"] for message in coding_agent_filter(MESSAGES, "urgent")]
        print(
            "test_filter_urgent (independent): FAIL - "
            f"expected urgent message id 2, got {actual_ids}"
        )
    else:
        print("test_filter_urgent (independent): PASS")
    print("test_export_pdf (independent): PASS - PDF header and story content present")
    for story, artifacts in lineage.items():
        for artifact, owner in artifacts.items():
            print(f"lineage {story}: {artifact} <- {owner}")
    print(f"test summary: {result.testsRun - len(result.failures)} passed, {len(result.failures)} failed")
    decision = "REJECT" if not result.wasSuccessful() else "APPROVE"
    reason = "independent acceptance test failed" if decision == "REJECT" else "all tests passed"
    print(f"review agent: {decision} release ({reason})")
    assert not result.wasSuccessful()
    assert decision == "REJECT"


if __name__ == "__main__":
    main()
