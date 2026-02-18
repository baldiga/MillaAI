# MillaAI
מילה - העוזרת האישית לשיווק מבוסס פאונדרים שחיה אצלך בוואטצאפ
Milla - AI WhatsApp Assistant Core 🧠This repository contains the backend core for Milla, an advanced AI assistant that operates on WhatsApp using n8n orchestration.This specific service handles audio processing, transcription (Hebrew specialized), and media management.🚀 FeaturesFastAPI based lightweight server.YouTube DL integration for processing video links.Cloudinary integration for media storage and public URL generation.Ivrit.ai / RunPod integration for state-of-the-art Hebrew transcription (Whisper V3).Universal JSON Parser to handle complex streaming responses from AI models.🛠️ Setup & Installation1. Clone the repogit clone [https://github.com/yourusername/milla-core.git](https://github.com/yourusername/milla-core.git)
cd milla-core
2. Install Dependenciespip install -r requirements.txt
3. Environment Variables (.env)Create a .env file (or set these in Render/Railway):CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_secret
RUNPOD_API_KEY=your_runpod_key
RUNPOD_ENDPOINT_ID=your_endpoint_id
4. Run Locallyuvicorn main:app --reload
☁️ Deploy to RenderCreate a new Web Service on Render.Connect this repository.Runtime: Python 3.Build Command: pip install -r requirements.txt.Start Command: uvicorn main:app --host 0.0.0.0 --port 10000.Important: Add the Environment Variables from step 3 in the Render dashboard.🔗 n8n IntegrationThis service exposes a /transcribe endpoint (POST).In n8n, use an HTTP Request node to send audio URLs to this service.Payload example:{
  "url": "[https://path.to/your/audio.ogg](https://path.to/your/audio.ogg)",
  "language": "he"
}
Built by Amir Baldiga
