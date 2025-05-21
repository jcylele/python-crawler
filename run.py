# run.py
import uvicorn
import logging

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    uvicorn.run(
        "web:app",
        host="0.0.0.0",
        port=7878,
        reload=True,
        reload_delay=0.25,
        workers=1,
        log_level="debug"
    )
