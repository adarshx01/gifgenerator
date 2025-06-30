# AI GIF Generator

A platform where users can enter a GIF theme prompt, provide a YouTube link or upload a video, and the system automatically generates captioned GIFs based on the content and prompt using AI.

## Features

- 🎯 **AI-Powered Analysis**: Uses Google Gemini to analyze video content and find moments that match your theme
- 📺 **YouTube Integration**: Extract captions from YouTube videos automatically
- 📁 **Video Upload**: Upload your own MP4 files for processing
- ✨ **Smart Caption Generation**: AI identifies the best quotes and moments for GIFs
- 🎬 **Automatic GIF Creation**: Generates GIFs with overlaid captions
- 📥 **Easy Download**: Download your generated GIFs instantly

## Tech Stack

### Backend
- **Python FastAPI** - High-performance API framework
- **Google Gemini AI** - Content analysis and moment identification
- **YouTube Transcript API** - Extract captions from YouTube videos
- **MoviePy** - Video processing and GIF generation
- **Pillow** - Image processing for captions

### Frontend
- **React 19** with TypeScript
- **Vite** - Fast development and build tool
- **Modern CSS** with responsive design

## Setup Instructions

### Prerequisites
- Python 3.12+
- Node.js 18+
- Google Gemini API key

### Backend Setup

1. **Install Python dependencies:**
   ```bash
   cd gif-generator
   pip install -r requirement.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your Gemini API key
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

3. **Run the backend:**
   ```bash
   python main.py
   ```
   The API will be available at `http://localhost:8000`

### Frontend Setup

1. **Install Node.js dependencies:**
   ```bash
   cd gifFrontend
   npm install
   ```

2. **Start the development server:**
   ```bash
   npm run dev
   ```
   The frontend will be available at `http://localhost:5173`

## Usage

1. **Enter a Theme Prompt**: Describe what kind of moments you want (e.g., "funny moments", "inspirational quotes")

2. **Provide Video Source**:
   - **YouTube**: Paste a YouTube URL
   - **Upload**: Upload an MP4 file

3. **AI Analysis**: The system will:
   - Extract transcript/captions
   - Use AI to identify 2-3 key moments matching your theme
   - Provide timestamps and explanations

4. **Generate GIFs**: Click "Generate GIF" for any suggested moment

5. **Download**: Download your captioned GIFs instantly

## API Endpoints

- `POST /process-youtube` - Process YouTube video with theme prompt
- `POST /process-upload` - Process uploaded video file
- `POST /generate-gif` - Generate GIF from video segment
- `GET /download-gif/{gif_id}` - Download generated GIF

## Deployment

### Backend (Render)
1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set build command: `pip install -r requirement.txt`
4. Set start command: `python main.py`
5. Add environment variable: `GEMINI_API_KEY`

### Frontend (Vercel/Netlify)
1. Build the frontend: `npm run build`
2. Deploy the `dist` folder to your hosting service
3. Update API base URL in production

## Limitations

- YouTube video download not implemented (demo uses transcript only)
- For production, integrate yt-dlp for actual video downloading
- File uploads are temporary (implement cloud storage for production)
- GIF optimization could be improved for smaller file sizes

## Future Enhancements

- Speech-to-text for uploaded videos without captions
- Advanced GIF customization (fonts, colors, positioning)
- Batch processing for multiple videos
- Social media sharing integration
- User accounts and GIF galleries

## License

MIT License - see LICENSE file for details