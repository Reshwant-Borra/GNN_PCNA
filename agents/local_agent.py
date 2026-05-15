"""
Local LLM agent using Ollama (Qwen2.5 / any model).

Replaces cloud Gemini/ChatGPT calls with a local model for:
  - Implementation tasks (given a plan file, generate code)
  - Review tasks (given a changed file, return issues)

Usage:
    python agents/local_agent.py implement --plan docs/plans/2026-05-14_parse_pdb.md
    python agents/local_agent.py review --file src/data_processing/parse_pdb.py
"""

import argparse
import sys
from pathlib import Path
from openai import OpenAI

# Ollama exposes an OpenAI-compatible API at localhost:11434
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # required by the client, value doesn't matter
)

MODEL = "qwen2.5:7b"  # change to qwen2.5:4b if RAM < 8 GB

SYSTEM_IMPLEMENT = """\
You are a senior Python engineer implementing code for GNN-PCNA, a cryptic pocket \
prediction pipeline for the protein PCNA.

Stack: Python 3.10+, PyTorch Geometric, MDAnalysis, BioPython, numpy.

Rules:
- Full type hints on all public functions.
- No placeholder TODOs — implement completely.
- Handle PCNA homotrimer: chains A, B, C (~261 residues each).
- Document return tensor shapes in docstrings.
- Do NOT change existing function signatures.
- Return the complete implemented file followed by a one-paragraph change summary.
"""

SYSTEM_REVIEW = """\
You are a code reviewer for GNN-PCNA, a cryptic pocket prediction pipeline.

Stack: Python 3.10+, PyTorch Geometric, MDAnalysis, BioPython.

Return a numbered list of issues only (severity: critical | warning | suggestion).
For each: location, description, minimal fix. No redesign suggestions.

Key things to check:
1. Off-by-one errors in residue/graph indexing
2. Data leakage (split must be at protein level, not residue level)
3. Focal loss / label imbalance correctness
4. PyTorch Geometric API (edge_index=long, edge_attr=float)
5. PCNA-specific: 3 chains A/B/C, ~800 nodes total, 6Å label cutoff
"""


def read_file(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def chat(system: str, user: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
        stream=True,
    )
    chunks = []
    for chunk in response:
        delta = chunk.choices[0].delta.content
        if delta:
            print(delta, end="", flush=True)
            chunks.append(delta)
    print()
    return "".join(chunks)


def cmd_implement(plan_path: str) -> None:
    plan = read_file(plan_path)

    # Extract stub file path from plan (looks for "File to implement: src/...")
    stub_path = None
    for line in plan.splitlines():
        if "File to implement:" in line or "File:" in line:
            parts = line.split(":", 1)
            if len(parts) == 2:
                candidate = parts[1].strip()
                if candidate.startswith("src/"):
                    stub_path = Path("C:/Users/advay/GNN_PNCA") / candidate
                    break

    stub_content = ""
    if stub_path and stub_path.exists():
        stub_content = f"\n\nCurrent stub to implement:\n```python\n{stub_path.read_text()}\n```"

    prompt = f"Plan file:\n\n{plan}{stub_content}\n\nImplement the file described above."
    chat(SYSTEM_IMPLEMENT, prompt)


def cmd_review(file_path: str) -> None:
    code = read_file(file_path)
    known_bugs_path = Path("C:/Users/advay/GNN_PNCA/KNOWN_BUGS.md")
    known_bugs = known_bugs_path.read_text() if known_bugs_path.exists() else ""

    prompt = (
        f"File to review: {file_path}\n\n"
        f"```python\n{code}\n```\n\n"
        f"Known bugs (check these first):\n{known_bugs}"
    )
    chat(SYSTEM_REVIEW, prompt)


def cmd_ask(question: str) -> None:
    system = (
        "You are a computational biology and ML assistant for GNN-PCNA. "
        "Answer concisely. Use bullet points and code blocks where helpful."
    )
    chat(system, question)


def main() -> None:
    parser = argparse.ArgumentParser(description="Local Qwen agent for GNN-PCNA")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_impl = sub.add_parser("implement", help="Implement from a plan file")
    p_impl.add_argument("--plan", required=True, help="Path to plan .md file")

    p_rev = sub.add_parser("review", help="Review a changed source file")
    p_rev.add_argument("--file", required=True, help="Path to Python file")

    p_ask = sub.add_parser("ask", help="Ask a free-form question")
    p_ask.add_argument("question", nargs="+")

    args = parser.parse_args()

    if args.cmd == "implement":
        cmd_implement(args.plan)
    elif args.cmd == "review":
        cmd_review(args.file)
    elif args.cmd == "ask":
        cmd_ask(" ".join(args.question))


if __name__ == "__main__":
    main()
