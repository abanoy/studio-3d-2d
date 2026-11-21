"""Asynchronous installed-content browser worker, emitting only data to a caller-owned result."""
import argparse
import json
from pathlib import Path
import traceback
import lzma
import struct

from source_content import assets
from source_installation import installed_context


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    args = parser.parse_args()
    request = json.loads(args.request.read_text(encoding="utf-8"))
    result_path = Path(request["result"])
    try:
        context = installed_context(request["gmod"], request["workshop"], request.get("extra", []))
        if request["action"] == "discover":
            result = context['discovery']
        elif request["action"] == "index": result = assets(request["provider"],request.get("include_particles",False))
        elif request["action"] == "search":
            rows, errors = [], []
            query = request.get("query", "").casefold()
            for provider in request["providers"][:4096]:
                if not provider.get("present"): continue
                try:
                    indexed = assets(provider,request.get("include_particles",False))
                    for item in indexed["assets"]:
                        if query and query not in item["path"].casefold() and query not in indexed["title"].casefold(): continue
                        item["provider"] = provider
                        item["source_title"] = indexed["title"]
                        rows.append(item)
                        if len(rows) >= 50000: break
                except (OSError, ValueError, lzma.LZMAError, struct.error, EOFError) as error: errors.append(provider["label"] + ": " + str(error))
                if len(rows) >= 50000: break
            result = {"assets": rows, "title": "Installed content search", "warnings": errors, "truncated": len(rows) >= 50000}
        else: raise ValueError("Unknown browser action")
        result["ok"] = True
    except Exception as error:
        result = {"ok": False, "error": str(error)}
    temp = result_path.with_suffix(".tmp")
    temp.write_text(json.dumps(result, ensure_ascii=True), encoding="utf-8")
    temp.replace(result_path)


if __name__ == "__main__": main()
