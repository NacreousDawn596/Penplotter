import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Upload, Settings, Image as ImageIcon, RefreshCw } from 'lucide-react';

function App() {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [contours, setContours] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [params, setParams] = useState({
    n: 0,
    canny_threshold1: 125,
    canny_threshold2: 130,
    pen_diameter: 1.5,
    max_width: 2200,
    multiplier: 6,
  });

  const [arduinoStatus, setArduinoStatus] = useState(null);
  const [arduinoLoading, setArduinoLoading] = useState(false);
  const [port, setPort] = useState('/dev/ttyACM0');
  const [fqbn, setFqbn] = useState('arduino:avr:uno');
  const [boards, setBoards] = useState({});
  const [stats, setStats] = useState(null);

  useEffect(() => {
    axios.get('http://localhost:3033/api/boards')
      .then(res => setBoards(res.data))
      .catch(err => console.error(err));
  }, []);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setPreviewUrl(URL.createObjectURL(selectedFile));
      setContours([]); // Clear previous contours
    }
  };

  const handleParamChange = (e) => {
    const { name, value } = e.target;
    setParams(prev => ({
      ...prev,
      [name]: parseFloat(value)
    }));
  };

  const processImage = async () => {
    if (!file) return;

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('image', file);
    formData.append('fqbn', fqbn);
    Object.keys(params).forEach(key => {
      formData.append(key, params[key]);
    });

    try {
      const response = await axios.post('http://localhost:3033/api/process', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setContours(response.data.contours);
      setStats(response.data.stats);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.error || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleOptimize = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('image', file);
    formData.append('fqbn', fqbn);
    Object.keys(params).forEach(key => {
      formData.append(key, params[key]);
    });

    try {
      const response = await axios.post('http://localhost:3033/api/optimize', formData);
      setContours(response.data.contours);
      setParams(prev => ({ ...prev, ...response.data.params }));
      setStats(response.data.stats);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.error || 'Optimization failed');
    } finally {
      setLoading(false);
    }
  };

  const handleCompile = async () => {
    setArduinoLoading(true);
    setArduinoStatus('Compiling...');
    try {
      const response = await axios.post('http://localhost:3033/api/compile', {
        contours,
        fqbn
      });

      if (response.data.optimized) {
        setArduinoStatus(`Success: ${response.data.message}`);
        setContours(response.data.new_contours);
        setParams(prev => ({ ...prev, ...response.data.new_params }));
        setStats(response.data.new_stats);
        // Maybe add a toast or alert that params were changed?
      } else {
        setArduinoStatus(`Success: ${response.data.message}`);
      }
    } catch (err) {
      console.error(err);
      setArduinoStatus(`Error: ${err.response?.data?.error || err.message}`);
    } finally {
      setArduinoLoading(false);
    }
  };

  const handleUpload = async () => {
    setArduinoLoading(true);
    setArduinoStatus('Uploading...');
    try {
      const response = await axios.post('http://localhost:3033/api/upload', {
        port,
        fqbn
      });
      setArduinoStatus(`Success: ${response.data.message}`);
    } catch (err) {
      console.error(err);
      setArduinoStatus(`Error: ${err.response?.data?.error || err.message}`);
    } finally {
      setArduinoLoading(false);
    }
  };

  // Auto-process when params change if file exists? 
  // Maybe better to have a button or debounce. 
  // The user said "each time I update the parameters, the image updates".
  // So I should use useEffect with debounce.

  useEffect(() => {
    if (file) {
      const timer = setTimeout(() => {
        processImage();
      }, 500); // 500ms debounce
      return () => clearTimeout(timer);
    }
  }, [params, file, fqbn]); // Re-process when board changes too, to update stats

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8 font-sans">
      <div className="max-w-7xl mx-auto">
        <header className="mb-8 flex items-center gap-4">
          <div className="p-3 bg-blue-600 rounded-lg shadow-lg shadow-blue-500/20">
            <ImageIcon className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              Pen Plotter WebUI
            </h1>
            <p className="text-gray-400">Generate contours for your plotter</p>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Controls Panel */}
          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-2xl p-6 space-y-6 h-fit">
            <div className="space-y-4">
              <h2 className="text-xl font-semibold flex items-center gap-2">
                <Upload className="w-5 h-5 text-blue-400" />
                Input Image
              </h2>
              <div className="relative group">
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleFileChange}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                />
                <div className="border-2 border-dashed border-gray-600 rounded-xl p-8 text-center group-hover:border-blue-500 transition-colors bg-gray-800/50">
                  {file ? (
                    <p className="text-blue-400 font-medium truncate">{file.name}</p>
                  ) : (
                    <div className="space-y-2">
                      <p className="text-gray-400">Drop image here or click to upload</p>
                      <p className="text-xs text-gray-500">Supports JPG, PNG</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <h2 className="text-xl font-semibold flex items-center gap-2">
                <Settings className="w-5 h-5 text-purple-400" />
                Parameters
              </h2>

              <div className="space-y-4">
                <ParamControl
                  label="N Parameter"
                  name="n"
                  value={params.n}
                  min={0} max={100} step={1}
                  onChange={handleParamChange}
                />
                <ParamControl
                  label="Canny Threshold 1"
                  name="canny_threshold1"
                  value={params.canny_threshold1}
                  min={0} max={255} step={1}
                  onChange={handleParamChange}
                />
                <ParamControl
                  label="Canny Threshold 2"
                  name="canny_threshold2"
                  value={params.canny_threshold2}
                  min={0} max={255} step={1}
                  onChange={handleParamChange}
                />
                <ParamControl
                  label="Pen Diameter"
                  name="pen_diameter"
                  value={params.pen_diameter}
                  min={0.1} max={5} step={0.1}
                  onChange={handleParamChange}
                />
                <ParamControl
                  label="Max Width"
                  name="max_width"
                  value={params.max_width}
                  min={500} max={5000} step={100}
                  onChange={handleParamChange}
                />
                <ParamControl
                  label="Multiplier"
                  name="multiplier"
                  value={params.multiplier}
                  min={1} max={20} step={1}
                  onChange={handleParamChange}
                />
              </div>

              <div className="pt-4 border-t border-gray-700 space-y-4">
                <h3 className="text-lg font-semibold text-gray-300">Arduino Control</h3>
                <div className="space-y-2">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={port}
                      onChange={(e) => setPort(e.target.value)}
                      placeholder="Port (e.g. /dev/ttyACM0)"
                      className="bg-gray-700 text-white px-3 py-2 rounded-lg flex-1 text-sm"
                    />
                    <select
                      value={fqbn}
                      onChange={(e) => setFqbn(e.target.value)}
                      className="bg-gray-700 text-white px-3 py-2 rounded-lg w-1/3 text-sm"
                    >
                      {Object.entries(boards).map(([key, board]) => (
                        <option key={key} value={key}>{board.name}</option>
                      ))}
                    </select>
                  </div>

                  {stats && (
                    <div className="space-y-1">
                      <div className="flex justify-between text-xs text-gray-400">
                        <span>Memory Usage</span>
                        <span>{Math.round(stats.percent_usage)}% ({Math.round(stats.estimated_size / 1024)}KB / {Math.round(stats.flash / 1024)}KB)</span>
                      </div>
                      <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                        <div
                          className={`h-full transition-all duration-500 ${stats.percent_usage > 100 ? 'bg-red-500' : stats.percent_usage > 90 ? 'bg-yellow-500' : 'bg-green-500'}`}
                          style={{ width: `${Math.min(100, stats.percent_usage)}%` }}
                        />
                      </div>
                      {stats.percent_usage > 100 && (
                        <button
                          onClick={handleOptimize}
                          className="w-full mt-2 bg-blue-600 hover:bg-blue-500 text-white py-1 px-2 rounded text-xs font-medium transition-colors flex items-center justify-center gap-1"
                        >
                          <RefreshCw className="w-3 h-3" />
                          Optimize Parameters
                        </button>
                      )}
                    </div>
                  )}

                  <div className="flex gap-2">
                    <button
                      onClick={handleCompile}
                      disabled={arduinoLoading || contours.length === 0}
                      className="flex-1 bg-yellow-600 hover:bg-yellow-500 disabled:opacity-50 disabled:cursor-not-allowed text-white py-2 rounded-lg font-medium transition-colors"
                    >
                      Compile
                    </button>
                    <button
                      onClick={handleUpload}
                      disabled={arduinoLoading}
                      className="flex-1 bg-green-600 hover:bg-green-500 disabled:opacity-50 disabled:cursor-not-allowed text-white py-2 rounded-lg font-medium transition-colors"
                    >
                      Upload
                    </button>
                  </div>
                  {arduinoStatus && (
                    <div className={`text-xs p-2 rounded ${arduinoStatus.startsWith('Error') ? 'bg-red-500/20 text-red-300' : 'bg-green-500/20 text-green-300'}`}>
                      {arduinoStatus}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Preview Panel */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-2xl p-6 min-h-[600px] flex flex-col">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold">Preview</h2>
                {loading && (
                  <div className="flex items-center gap-2 text-blue-400">
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Processing...
                  </div>
                )}
              </div>

              {error && (
                <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-lg mb-4">
                  {error}
                </div>
              )}

              <div className="flex-1 bg-white rounded-lg overflow-hidden relative flex items-center justify-center">
                {contours.length > 0 ? (
                  <ContourViewer contours={contours} maxWidth={params.max_width} multiplier={params.multiplier} />
                ) : previewUrl ? (
                  <div className="text-gray-400 text-center p-4">
                    <p>Processing image...</p>
                  </div>
                ) : (
                  <div className="text-gray-400 text-center">
                    Upload an image to see the preview
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function ParamControl({ label, name, value, min, max, step, onChange }) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <label className="text-gray-300">{label}</label>
        <span className="text-gray-500 font-mono">{value}</span>
      </div>
      <input
        type="range"
        name={name}
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={onChange}
        className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500 hover:accent-blue-400 transition-colors"
      />
    </div>
  );
}

function ContourViewer({ contours, maxWidth, multiplier }) {
  // Calculate bounding box to set viewBox
  // contours is list of list of [x, y]
  // The coordinates from backend are already scaled/processed but might be large values.
  // We need to fit them in the SVG.

  if (!contours || contours.length === 0) return null;

  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;

  contours.forEach(contour => {
    contour.forEach(([x, y]) => {
      if (x < minX) minX = x;
      if (x > maxX) maxX = x;
      if (y < minY) minY = y;
      if (y > maxY) maxY = y;
    });
  });

  // Add some padding
  const padding = 50;
  const width = maxX - minX + padding * 2;
  const height = maxY - minY + padding * 2;
  const viewBox = `${minX - padding} ${minY - padding} ${width} ${height}`;

  return (
    <svg
      viewBox={viewBox}
      className="w-full h-full max-h-[800px]"
      preserveAspectRatio="xMidYMid meet"
      style={{ transform: 'scale(1, -1)' }}
    >
      {contours.map((contour, i) => {
        const points = contour.map(p => `${p[0]},${p[1]}`).join(' ');
        return (
          <polyline
            key={i}
            points={points}
            fill="none"
            stroke="black"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        );
      })}
    </svg>
  );
}

export default App;
