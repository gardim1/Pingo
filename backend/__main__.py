"""Cloud Run and local entrypoint; container listens on the supplied PORT."""
import os
import uvicorn

if __name__ == '__main__':
    uvicorn.run('backend.api.main:app',host=os.getenv('HOST','0.0.0.0'),
                port=int(os.getenv('PORT','8080')),access_log=False)
