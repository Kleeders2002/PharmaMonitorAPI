from fastapi import FastAPI, APIRouter, File, UploadFile, HTTPException
import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

router = APIRouter()

# Configuración de Cloudinary usando variables de entorno (más seguro)
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", "dqcapsw38"),
    api_key=os.getenv("CLOUDINARY_API_KEY", "777865456933914"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET", "1q9dtVuV0HROejN7fHGAh5uEVNw"),
)

@router.post("/upload-image/")
async def upload_image(file: UploadFile = File(...)):
    try:
        result = cloudinary.uploader.upload(file.file)
        return {"url": result["secure_url"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir la imagen: {str(e)}") 
