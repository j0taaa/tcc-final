import concurrent.futures
import subprocess
import os
import json
import sys
import resource
from pathlib import Path
from tempfile import NamedTemporaryFile
import resource
import signal

from datasets import load_dataset

from constrained_diffusion.cfgs.cpp import cpp_grammar_preprocessed
from constrained_diffusion.constrain_utils import (
    prelex_word,
    lex,
    reconstruct_word_boundaries,
)

GRAMMAR, LEXING = cpp_grammar_preprocessed()

DATASET = None

def get_dataset():
    global DATASET
    if DATASET is None:
        DATASET = load_dataset(
            "zai-org/humaneval-x",
            "cpp",
            split="test",
            trust_remote_code=True,
        )
    return DATASET

def _set_memory_limit(memory_limit_mb):
    if memory_limit_mb is None:
        return
    limit = int(memory_limit_mb) * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))

def cpp_syntax_check(cpp_program):
    """
    Check the syntax of a C++ program using our syntax definition
    """
    prelexed_program = prelex_word(cpp_program, "\x02\x03", is_first=True, is_last=True)
    lexed = lex(prelexed_program, LEXING, is_first=True)
    return any(
        GRAMMAR.accepts(lexied[0])
        for lexied in lexed
        if not lexied[1] and not lexied[2]
    )

def _syntax_worker_main():
    payload = json.load(sys.stdin)
    cpp_program = payload["cpp_program"]

    try:
        result = cpp_syntax_check(cpp_program)
        print(json.dumps({"ok": True, "value": bool(result)}), flush=True)
    except BaseException as e:
        print(json.dumps({"ok": False, "error": repr(e)}), flush=True)

def _cpp_syntax_check_worker(cpp_program, q, memory_limit_mb=None):
    try:
        if memory_limit_mb is not None:
            limit = int(memory_limit_mb) * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (limit, limit))

        q.put((True, cpp_syntax_check(cpp_program)))
    except MemoryError:
        q.put((False, "MemoryError: syntax check exceeded memory limit"))
    except BaseException as e:
        q.put((False, repr(e)))


def cpp_syntax_check_with_timeout(cpp_program, timeout=40, memory_limit_mb=4096):
    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--syntax-worker",
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=(
                (lambda: _set_memory_limit(memory_limit_mb))
                if memory_limit_mb is not None
                else None
            ),
        )

        try:
            stdout, stderr = proc.communicate(
                input=json.dumps({"cpp_program": cpp_program}),
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
            return False, "Syntax check timed out"

        # Parse the last JSON line, in case some library printed warnings.
        lines = [line for line in stdout.splitlines() if line.strip()]
        if not lines:
            msg = stderr.strip() or f"syntax worker exited with code {proc.returncode}"
            return False, f"Syntax check produced no result: {msg}"

        try:
            payload = json.loads(lines[-1])
        except json.JSONDecodeError:
            msg = (stderr.strip() or stdout.strip())[:1000]
            return False, f"Syntax check produced invalid output: {msg}"

        if payload.get("ok"):
            return bool(payload.get("value")), ""

        return False, f"Syntax check failed: {payload.get('error', '')}"

    except Exception as e:
        return False, f"Syntax check failed: {str(e)}"


def cpp_compile_and_run(cpp_program, timeout=40):
    # Create a temporary file for the C++ source code
    with NamedTemporaryFile(suffix=".cpp", delete=False) as source_file:
        source_path = source_file.name
        source_file.write(cpp_program.encode())
        source_file.flush()

    executable_path = source_path + ".exe"

    run_process = None
    try:
        # Compile the program with C++17 standard
        run_process = subprocess.Popen(
            ["g++", "-std=c++17", source_path, "-o", executable_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,
        )
        run_process.wait(timeout=timeout)

        # Check if compilation was successful
        if run_process.returncode != 0:
            return False, False, run_process.stderr.read().decode()

        # Run the compiled program
        run_process = subprocess.Popen(
            [executable_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,
        )
        run_process.wait(timeout=timeout)

        # Check if the program ran successfully (return code 0)
        # A return code of 0 means all assertions passed
        run_success = run_process.returncode == 0

        # Combine stdout and stderr for the output
        output = run_process.stdout.read().decode()
        if run_process.stderr:
            output += "\n" + run_process.stderr.read().decode()
        run_process = None

        return True, run_success, output

    except subprocess.TimeoutExpired:
        # return False, False, "Timeout during compilation or execution"
        if run_process:
            try:
                os.killpg(os.getpgid(run_process.pid), signal.SIGTERM)
                run_process.wait(timeout=2)
            except Exception:
                try:
                    os.killpg(os.getpgid(run_process.pid), signal.SIGKILL)
                    run_process.wait(timeout=2)
                except Exception:
                    pass
        return False, False, "Timeout during compilation or execution"
    except Exception as e:
        return False, False, f"Error: {str(e)}"
    finally:
        if run_process:
            try:
                os.killpg(os.getpgid(run_process.pid), signal.SIGTERM)
                run_process.wait(timeout=2)
            except Exception:
                try:
                    os.killpg(os.getpgid(run_process.pid), signal.SIGKILL)
                    run_process.wait(timeout=2)
                except Exception:
                    pass
        # Clean up temporary files
        if os.path.exists(source_path):
            os.remove(source_path)
        if os.path.exists(executable_path):
            try:
                os.remove(executable_path)
            except OSError:
                pass  # Ignore errors when removing the executable


def check_instance(output, timeout=40):
    cpp_code = output["extracted"]
    if "\x02" in cpp_code:
        # If the code contains prelexed tokens, decode them
        output["extracted"] = reconstruct_word_boundaries(cpp_code)
        output["code"] = reconstruct_word_boundaries(output["code"])
        cpp_code = output["extracted"]

    if cpp_code.strip().startswith("/*"):
        declaration: str = get_dataset()[
            int(output["instance_id"].split("/")[1].split("_")[0])
        ]["declaration"]
        cpp_code_no_tests = declaration + output["code"]
    else:
        cpp_code_no_tests = cpp_code
    cpp_code_no_tests = cpp_code_no_tests.split("#undef NDEBUG")[0]

    try:
        syntax_ok, syntax_output_message = cpp_syntax_check_with_timeout(
            cpp_code_no_tests,
            timeout=timeout,
            memory_limit_mb=16384,
        )
    except Exception as e:
        syntax_ok = False
        syntax_output_message = f"Syntax check failed: {str(e)}"

    try:
        _, run_success, output_message = cpp_compile_and_run(
            cpp_code,
            timeout=max(1, timeout - 5),
        )
    except Exception as e:
        run_success = False
        output_message = f"Compilation or execution failed: {str(e)}"

    return {
        "instance_id": output["instance_id"],
        "extracted": output["extracted"],
        "syntax_ok": syntax_ok,
        "passed_tests": run_success,  # True if the program compiled and ran with return code 0
        "compiler_output": syntax_output_message + output_message,
    }

if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--syntax-worker":
        _syntax_worker_main()