from fastapi.responses import JSONResponse

def success_response(data=None, message="Success", status_code=200):
    content = {
        "success": True,
        "message": message,
        "data": data
    }
    return JSONResponse(
        status_code=status_code,
        content=content
    )

