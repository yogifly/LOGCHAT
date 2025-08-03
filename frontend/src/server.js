const express = require('express');
const multer = require('multer');
const fs = require('fs');
const readline = require('readline');
const cors = require('cors');

const app = express();
app.use(cors());
const upload = multer({ dest: 'uploads/' });

// Helper to classify logs better
function classifyLog(line) {
  const lower = line.toLowerCase();
  if (lower.includes('success') || lower.includes('logged in') || lower.includes('payment complete')) {
    return 'SUCCESS';
  }
  if (lower.includes('fail') || lower.includes('error') || lower.includes('unauthorized') || lower.includes('denied')) {
    return 'ERROR';
  }
  if (lower.includes('warn') || lower.includes('deprecated') || lower.includes('slow')) {
    return 'WARNING';
  }
  return 'INFO'; // default
}

app.post('/upload', upload.single('file'), async (req, res) => {
  const filePath = req.file.path;
  const logs = [];

  const fileStream = fs.createReadStream(filePath);
  const rl = readline.createInterface({
    input: fileStream,
    crlfDelay: Infinity,
  });

  for await (const line of rl) {
    if (!line.trim()) continue; // skip empty lines

    // Sample: [2025-08-03 12:45:12] INFO: User logged in
    const match = line.match(/\[(.*?)\]\s*(\w+):\s*(.*)/);
    if (match) {
      const [, timestamp, originalLevel, message] = match;
      const refinedLevel = classifyLog(message); // 👈 smart classification

      logs.push({
        timestamp,
        level: refinedLevel,
        originalLevel,
        message,
      });
    }
  }

  fs.unlinkSync(filePath); // cleanup
  res.json(logs);
});

app.listen(5000, () => {
  console.log('Server running on http://localhost:5000');
});
