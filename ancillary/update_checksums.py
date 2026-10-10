#!/usr/bin/env python3
"""Refresh the public repository manifest after editing citations/docs."""
import hashlib
from pathlib import Path


def main():
    root=Path(__file__).resolve().parent.parent
    manifest=root/'ancillary'/'SHA256SUMS'
    ignored={'.git','__pycache__','.venv','venv','fresh_reconstruction'}
    files=sorted(p for p in root.rglob('*') if p.is_file()
                 and p!=manifest and not any(part in ignored for part in p.relative_to(root).parts)
                 and not p.name.endswith(('.pyc','.pyo','.aux','.out','.synctex.gz'))
                 and not (p.parent==root/'report' and p.suffix=='.log'))
    manifest.write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+
                               p.relative_to(root).as_posix()+'\n' for p in files),encoding='utf-8')
    print(f'Updated SHA-256 manifest for {len(files)} files')


if __name__=='__main__':main()
