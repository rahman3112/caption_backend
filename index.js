const express = require('express');
const multer = require('multer');
const { exec } = require('child_process');
const path = require('path');
const cors = require('cors');
const fs = require('fs');

const app = express();
const PORT = 5000;

app.use(cors());
app.use(express.json());

const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, 'uploads/'),
  filename: (req, file, cb) => cb(null, `video-${Date.now()}${path.extname(file.originalname)}`),
});
const upload = multer({ storage });

if (!fs.existsSync('uploads')) fs.mkdirSync('uploads');

app.post('/upload', upload.single('video'), (req, res) => {
  console.log('Received video upload request'); // Log when request is received
  if (!req.file) {
    console.log('No file uploaded');
    return res.status(400).json({ error: 'No video file uploaded' });
  }

  const videoPath = req.file.path;
  const outputPath = path.join('uploads', `output-${req.file.filename}`);
  console.log(`Processing video: ${videoPath} -> ${outputPath}`); // Log file paths

  // Use 'py' launcher for Windows compatibility
  const pythonCmd = 'py';

  console.log(`Executing command: ${pythonCmd} process_video.py "${videoPath}" "${outputPath}"`); // Log command
  exec(
    `${pythonCmd} process_video.py "${videoPath}" "${outputPath}"`,
    (error, stdout, stderr) => {
      if (error) {
        console.error('Python error:', stderr); // Detailed error
        console.error('Error code:', error.code);
        return res.status(500).json({ error: 'Failed to process video' });
      }
      console.log('Python script output:', stdout); // Log successful output
      console.log('Video processing complete, sending file');

      res.download(outputPath, 'captioned_video.mp4', (err) => {
        if (err) {
          console.error('Error sending file:', err);
        } else {
          console.log('File sent successfully');
        }
        // Clean up files
        fs.unlinkSync(videoPath);
        fs.unlinkSync(outputPath);
        if (fs.existsSync('uploads/audio.mp3')) fs.unlinkSync('uploads/audio.mp3');
        if (fs.existsSync('uploads/captions.ass')) fs.unlinkSync('uploads/captions.ass');
      });
    }
  );
});

app.listen(PORT, () => console.log(`Server running on http://localhost:${PORT}`));