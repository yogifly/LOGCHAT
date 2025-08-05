import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [file, setFile] = useState(null);
  const [logs, setLogs] = useState([]);

  const handleFileChange = (e) => setFile(e.target.files[0]);

  const handleUpload = async () => {
    if (!file) return alert('Upload a log file first.');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await axios.post('http://localhost:5000/upload', formData);
      setLogs(res.data);
    } catch (err) {
      alert('Upload failed.');
      console.error(err);
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>Log Parser</h2>
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload}>Upload</button>

      <h3>Parsed Logs (JSON Format)</h3>
<pre style={{ 
  maxHeight: '400px', 
  overflowY: 'scroll', 
  border: '1px solid #ccc', 
  background: '#f9f9f9', 
  padding: '10px' 
}}>
  {JSON.stringify(logs, null, 2)}
</pre>

    </div>
  );
}

export default App;
