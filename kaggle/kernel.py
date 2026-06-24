from __future__ import annotations

import base64
import subprocess
import sys
import traceback
from pathlib import Path

ROOT = Path("/kaggle/working")
SOURCE = ROOT / "ACE-Step-1.5"
OUTPUT = ROOT / "output"
REQUEST_B64 = "__REQUEST_JSON_BASE64__"


def run(command: list[str], cwd: Path | None = None):
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def main():
    OUTPUT.mkdir(exist_ok=True)
    request_path = ROOT / "request.json"
    request_path.write_bytes(base64.b64decode(REQUEST_B64))
    if not SOURCE.exists():
        run(["git", "clone", "--depth", "1", "https://github.com/ace-step/ACE-Step-1.5.git", str(SOURCE)])
    run([sys.executable, "-m", "pip", "install", "-q", "uv"])
    run(["uv", "sync", "--no-dev"], cwd=SOURCE)
    generator = ROOT / "generate.py"
    generator.write_text(
        '''
import json
import shutil
import sys
from pathlib import Path

SOURCE = Path("/kaggle/working/ACE-Step-1.5")
OUTPUT = Path("/kaggle/working/output")
REQUEST = Path("/kaggle/working/request.json")
sys.path.insert(0, str(SOURCE))

from acestep.handler import AceStepHandler
from acestep.inference import GenerationConfig, GenerationParams, generate_music

request = json.loads(REQUEST.read_text(encoding="utf-8"))
handler = AceStepHandler()
handler.initialize_service(project_root=str(SOURCE), config_path="acestep-v15-turbo", device="cuda")
params = GenerationParams(
    task_type="text2music",
    caption=request["caption"],
    lyrics=request["lyrics"],
    vocal_language=request["language"],
    bpm=request["bpm"],
    keyscale=request["keyscale"],
    timesignature=request["timesignature"],
    duration=request["duration"],
    inference_steps=12,
    shift=3.0,
    seed=request["seed"],
    thinking=False,
    use_cot_metas=False,
    use_cot_caption=False,
    use_cot_language=False,
    lm_negative_prompt=request["negative_prompt"],
)
config = GenerationConfig(batch_size=1, use_random_seed=False, seeds=[request["seed"]], audio_format="flac")
result = generate_music(handler, None, params, config, save_dir=str(OUTPUT))
if not result.success or not result.audios:
    raise RuntimeError(result.error or "ACE-Step did not return audio")
source_audio = Path(result.audios[0]["path"])
shutil.copy2(source_audio, OUTPUT / "quality_song.flac")
shutil.copy2(REQUEST, OUTPUT / "request.json")
print(OUTPUT / "quality_song.flac")
''',
        encoding="utf-8",
    )
    run(["uv", "run", "python", str(generator)], cwd=SOURCE)


try:
    main()
except Exception:
    OUTPUT.mkdir(exist_ok=True)
    error = traceback.format_exc()
    (OUTPUT / "ERROR.txt").write_text(error, encoding="utf-8")
    print(error, flush=True)
