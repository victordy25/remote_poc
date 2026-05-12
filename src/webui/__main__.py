"""`python -m webui` 으로 데모 서버 실행."""

from __future__ import annotations


def main() -> None:
    import uvicorn

    uvicorn.run(
        "webui.app:app",
        host="127.0.0.1",
        port=8765,
        reload=False,
    )


if __name__ == "__main__":
    main()
