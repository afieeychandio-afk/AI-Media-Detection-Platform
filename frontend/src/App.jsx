import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Shield, Image, Video, AudioLines, FileText, 
  Terminal, Upload, AlertTriangle, 
  CheckCircle, RefreshCw, BarChart2, HardDrive, ListFilter,
  ShieldCheck, ShieldAlert, X, Eye, Download, ScanFace
} from 'lucide-react';

export default function CyberDashboard() {
  const [activeTab, setActiveTab] = useState('image');
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  
  const [history, setHistory] = useState([]);

  const [selectedScan, setSelectedScan] = useState(null);
  const [selectedScanId, setSelectedScanId] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [modalLoading, setModalLoading] = useState(false);

  const fetchHistory = async () => {
    try {
      const response = await axios.get('http://127.0.0.1:8000/api/v1/scans/history');
      setHistory(response.data);
    } catch (err) {
      console.error("Failed to fetch analytical history pipeline:", err);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setPreview(URL.createObjectURL(selectedFile));
      setResult(null);
      setError(null);
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      let endpoint = '/analyze/image';
      if (activeTab === 'video') {
        endpoint = '/analyze/video';
      } else if (activeTab === 'audio') {
        endpoint = '/analyze/audio';
      }
      
      const response = await axios.post(`http://127.0.0.1:8000/api/v1${endpoint}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      
      setResult(response.data);
      await fetchHistory();
      
    } catch (err) {
      setError(err.response?.data?.detail || 'Pipeline processing error occurred.');
    } finally {
      setLoading(false);
    }
  };

  const switchModule = (moduleName) => {
    setActiveTab(moduleName);
    setFile(null);
    setPreview(null);
    setResult(null);
    setError(null);
  };

  const viewScanDetail = async (scanId) => {
    setModalLoading(true);
    setShowModal(true);
    setSelectedScanId(scanId);
    try {
      const response = await axios.get(`http://127.0.0.1:8000/api/v1/scans/${scanId}`);
      setSelectedScan(response.data);
    } catch (err) {
      setSelectedScan({ error: "Could not load scan detail." });
    } finally {
      setModalLoading(false);
    }
  };

  const closeModal = () => {
    setShowModal(false);
    setSelectedScan(null);
    setSelectedScanId(null);
  };

  const downloadReport = (scanId) => {
    if (!scanId) return;
    window.open(`http://127.0.0.1:8000/api/v1/scans/${scanId}/report`, '_blank');
  };

  const C2paCard = ({ c2pa }) => {
    if (!c2pa) return null;

    if (c2pa.has_c2pa && c2pa.is_ai_generated) {
      return (
        <div className="p-3 rounded border bg-rose-950/20 border-rose-900 text-rose-300 flex gap-3">
          <ShieldCheck className="w-5 h-5 flex-shrink-0" />
          <div>
            <span className="block font-bold text-xs uppercase tracking-widest text-slate-400">C2PA Content Credentials</span>
            <p className="text-xs mt-0.5 leading-relaxed">
              Cryptographically confirmed AI-generated. Signed by <b>{c2pa.issuer}</b> via <b>{c2pa.generator}</b>.
            </p>
          </div>
        </div>
      );
    }

    if (c2pa.has_c2pa && !c2pa.is_ai_generated) {
      return (
        <div className="p-3 rounded border bg-slate-800/40 border-slate-700 text-slate-300 flex gap-3">
          <ShieldCheck className="w-5 h-5 flex-shrink-0 text-slate-400" />
          <div>
            <span className="block font-bold text-xs uppercase tracking-widest text-slate-400">C2PA Content Credentials</span>
            <p className="text-xs mt-0.5 leading-relaxed">
              Manifest present (issuer: {c2pa.issuer}) but not flagged as AI-generated.
            </p>
          </div>
        </div>
      );
    }

    return (
      <div className="p-3 rounded border bg-slate-800/20 border-slate-800 text-slate-500 flex gap-3">
        <ShieldAlert className="w-5 h-5 flex-shrink-0" />
        <div>
          <span className="block font-bold text-xs uppercase tracking-widest text-slate-500">C2PA Content Credentials</span>
          <p className="text-xs mt-0.5 leading-relaxed">
            No manifest found. Not proof of authenticity — credentials are often stripped when files are re-saved or forwarded.
          </p>
        </div>
      </div>
    );
  };

  const FaceCard = ({ faceAnalysis }) => {
    if (!faceAnalysis) return null;

    if (faceAnalysis.note && faceAnalysis.faces_detected === 0 && (!faceAnalysis.faces || faceAnalysis.faces.length === 0)) {
      return null;
    }

    return (
      <div className="p-3 rounded border bg-[#0d1220] border-slate-800">
        <div className="flex items-center gap-2 mb-2">
          <ScanFace className="w-4 h-4 text-cyan-400 flex-shrink-0" />
          <span className="font-bold text-xs uppercase tracking-widest text-slate-400">
            Face Detection ({faceAnalysis.faces_detected} {faceAnalysis.faces_detected === 1 ? 'face' : 'faces'} found)
          </span>
        </div>

        {faceAnalysis.faces_detected === 0 ? (
          <p className="text-xs text-slate-500">No human faces detected in this asset.</p>
        ) : (
          <div className="space-y-2">
            {faceAnalysis.faces.map((f, idx) => (
              <div key={idx} className="flex items-center justify-between gap-2 bg-slate-900/50 rounded px-2 py-1.5">
                <span className="text-[11px] text-slate-400">Face #{idx + 1}</span>
                <div className="flex items-center gap-2 flex-1 max-w-[140px]">
                  <div className="flex-1 bg-slate-800 h-1.5 rounded overflow-hidden">
                    <div
                      className={`h-full ${f.face_ai_probability > 0.5 ? 'bg-rose-500' : 'bg-emerald-500'}`}
                      style={{ width: `${f.face_ai_probability * 100}%` }}
                    ></div>
                  </div>
                  <span className={`text-[11px] font-bold w-9 text-right ${f.face_ai_probability > 0.5 ? 'text-rose-400' : 'text-emerald-400'}`}>
                    {(f.face_ai_probability * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const navItems = [
    { id: 'image', label: 'Image Forensics', shortLabel: 'Image', icon: Image, color: 'cyan' },
    { id: 'video', label: 'Video Analyzer', shortLabel: 'Video', icon: Video, color: 'purple' },
    { id: 'audio', label: 'Audio Forensic', shortLabel: 'Audio', icon: AudioLines, color: 'orange' },
  ];

  const colorClasses = {
    cyan: 'bg-cyan-950/40 text-cyan-400 border-cyan-800/50',
    purple: 'bg-purple-950/40 text-purple-400 border-purple-800/50',
    orange: 'bg-orange-950/40 text-orange-400 border-orange-800/50',
  };

  return (
    <div className="flex flex-col md:flex-row min-h-screen md:h-screen bg-[#0b0f19] text-slate-100 font-mono text-sm md:overflow-hidden">
      
      <aside className="hidden md:flex w-64 bg-[#0f1626] border-r border-slate-800 flex-col justify-between p-4 select-none flex-shrink-0">
        <div>
          <div className="flex items-center gap-3 px-2 py-3 border-b border-slate-800 mb-6">
            <Shield className="w-6 h-6 text-cyan-400 animate-pulse" />
            <span className="font-bold tracking-wider text-cyan-400 text-base">AI MEDIA VERIFIER v1.0</span>
          </div>

          <nav className="space-y-1">
            {navItems.map(({ id, label, icon: Icon, color }) => (
              <button 
                key={id}
                onClick={() => switchModule(id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg font-medium transition-all ${activeTab === id ? colorClasses[color] + ' border' : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'}`}
              >
                <Icon className="w-4 h-4" /> {label}
              </button>
            ))}
          </nav>
        </div>

        <div className="border-t border-slate-800 pt-4 space-y-2 text-xs text-slate-500">
          <div className="flex justify-between items-center"><span className="flex items-center gap-1"><HardDrive className="w-3 h-3"/> System Status:</span><span className="text-emerald-400 font-bold">ONLINE</span></div>
          <div className="flex justify-between items-center"><span>Engine Core:</span><span className="text-slate-400">FastAPI v0.111</span></div>
        </div>
      </aside>

      <div className="md:hidden bg-[#0f1626] border-b border-slate-800 sticky top-0 z-30">
        <div className="flex items-center gap-2 px-3 py-3 border-b border-slate-800/60">
          <Shield className="w-5 h-5 text-cyan-400 flex-shrink-0" />
          <span className="font-bold tracking-wider text-cyan-400 text-sm truncate">AI MEDIA VERIFIER</span>
          <span className="ml-auto text-[10px] text-emerald-400 font-bold flex items-center gap-1 flex-shrink-0">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> ONLINE
          </span>
        </div>
        <div className="flex overflow-x-auto no-scrollbar px-2 py-2 gap-2">
          {navItems.map(({ id, shortLabel, icon: Icon, color }) => (
            <button
              key={id}
              onClick={() => switchModule(id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap flex-shrink-0 transition-all ${activeTab === id ? colorClasses[color] + ' border' : 'text-slate-400 bg-slate-800/40 border border-transparent'}`}
            >
              <Icon className="w-3.5 h-3.5" /> {shortLabel}
            </button>
          ))}
        </div>
      </div>

      <main className="flex-1 flex flex-col bg-[#0b0f19] min-h-0 md:overflow-hidden">
        
        <section className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6 p-3 md:p-6 md:overflow-y-auto">
          
          <div className="bg-[#0f1626] border border-slate-800 rounded-xl p-4 md:p-5 flex flex-col justify-between min-h-[360px] md:min-h-[400px]">
            <div>
              <div className="flex justify-between items-center mb-4 border-b border-slate-800/60 pb-2 flex-wrap gap-2">
                <h2 className="font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2 text-xs md:text-sm">
                  <Terminal className="w-4 h-4 text-cyan-500" /> {activeTab.toUpperCase()} UPLOAD & ANALYSIS
                </h2>
                {result && result.ai_detection_scores.ai_probability > 0.5 && (
                  <span className="text-xs bg-red-950/40 text-red-400 border border-red-900/50 px-2 py-0.5 rounded uppercase">Detected AI</span>
                )}
              </div>

              {!preview ? (
                <label className="border-2 border-dashed border-slate-800 hover:border-cyan-800 bg-[#0d1220] rounded-xl p-6 md:p-8 flex flex-col items-center justify-center cursor-pointer min-h-[240px] md:min-h-[280px] group transition-all">
                  <Upload className="w-10 h-10 md:w-12 md:h-12 text-slate-600 group-hover:text-cyan-500 transition-colors mb-4" />
                  <span className="text-slate-400 group-hover:text-slate-200 transition-colors text-center text-xs md:text-sm px-2">Inject {activeTab} asset for validation</span>
                  <span className="text-slate-600 text-[10px] md:text-xs mt-2 text-center px-2">
                    {activeTab === 'image' ? 'Supports high-res PNG, JPG, JPEG' : activeTab === 'video' ? 'Supports MP4, MKV, AVI, MOV' : 'Supports MP3, WAV, M4A, FLAC'}
                  </span> 
                  <input 
                    type="file" 
                    accept={activeTab === 'image' ? "image/*" : activeTab === 'video' ? "video/*" : "audio/*"} 
                    className="hidden" 
                    onChange={handleFileChange} 
                  />
                </label>
              ) : (
                <div className="relative border border-slate-800 bg-[#0d1220] rounded-xl p-3 md:p-4 flex flex-col items-center justify-center min-h-[240px] md:min-h-[280px]">
                  {activeTab === 'image' ? (
                    <img src={preview} alt="Forensic Ingestion" className="max-h-48 md:max-h-60 rounded-lg object-contain border border-slate-800 shadow-2xl" />
                  ) : activeTab === 'video' ? (
                    <video src={preview} controls className="max-h-48 md:max-h-60 w-full rounded-lg bg-black border border-slate-800 shadow-2xl" />
                  ) : (
                    <div className="w-full p-4 md:p-6 flex flex-col items-center justify-center bg-slate-900/60 rounded-lg border border-slate-800">
                      <AudioLines className="w-12 h-12 md:w-16 md:h-16 text-orange-500 animate-pulse mb-4" />
                      <audio src={preview} controls className="w-full accent-orange-500" />
                    </div>
                  )}
                  
                  <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 mt-4 w-full justify-center">
                    <label className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs rounded border border-slate-700 cursor-pointer transition-colors text-center">
                      Flush & Replace
                      <input 
                        type="file" 
                        accept={activeTab === 'image' ? "image/*" : activeTab === 'video' ? "video/*" : "audio/*"} 
                        className="hidden" 
                        onChange={handleFileChange} 
                      />
                    </label>
                    <button 
                      onClick={handleAnalyze} 
                      disabled={loading}
                      className={`px-5 py-1.5 border text-xs font-bold rounded flex items-center justify-center gap-1.5 transition-all disabled:opacity-50 ${activeTab === 'image' ? 'bg-cyan-950/60 border-cyan-700 text-cyan-400 hover:bg-cyan-900' : activeTab === 'video' ? 'bg-purple-950/60 border-purple-700 text-purple-400 hover:bg-purple-900' : 'bg-orange-950/60 border-orange-700 text-orange-400 hover:bg-orange-900'}`}
                    >
                      {loading ? <RefreshCw className="w-3 h-3 animate-spin" /> : <BarChart2 className="w-3 h-3" />}
                      {loading ? 'DEPLOYING ENSEMBLE...' : 'START SCAN'}
                    </button>
                  </div>
                </div>
              )}
            </div>

            {error && <div className="mt-4 bg-red-950/30 text-red-400 border border-red-900/60 p-3 rounded font-mono text-xs break-words">{error}</div>}
          </div>

          <div className="bg-[#0f1626] border border-slate-800 rounded-xl p-4 md:p-5 flex flex-col justify-between">
            <div>
              <div className="flex justify-between items-center mb-4 border-b border-slate-800/60 pb-2">
                <h2 className="font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2 text-xs md:text-sm">
                  <BarChart2 className="w-4 h-4 text-cyan-500" /> DETECTION INSIGHTS
                </h2>
              </div>

              {!result ? (
                <div className="flex flex-col items-center justify-center min-h-[240px] md:min-h-[300px] text-slate-600">
                  <Terminal className="w-8 h-8 mb-2 opacity-50" />
                  <p className="text-center text-xs px-4">Awaiting asset analysis execution pipeline...</p>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className={`p-3 rounded border flex gap-3 ${result.ai_detection_scores.ai_probability > 0.5 ? 'bg-amber-950/20 border-amber-900 text-amber-300' : 'bg-emerald-950/20 border-emerald-900 text-emerald-300'}`}>
                    {result.ai_detection_scores.ai_probability > 0.5 ? <AlertTriangle className="w-5 h-5 flex-shrink-0" /> : <CheckCircle className="w-5 h-5 flex-shrink-0" />}
                    <div>
                      <span className="block font-bold text-xs uppercase tracking-widest text-slate-400">ANALYSIS SUMMARY</span>
                      <p className="text-xs mt-0.5 leading-relaxed">{result.final_recommendation}</p>
                    </div>
                  </div>

                  {result.scan_id && (
                    <button
                      onClick={() => downloadReport(result.scan_id)}
                      className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded text-xs font-bold text-slate-200 transition-colors"
                    >
                      <Download className="w-3.5 h-3.5" /> DOWNLOAD FORENSIC PDF REPORT
                    </button>
                  )}

                  <C2paCard c2pa={result.c2pa_analysis} />

                  {activeTab === 'image' && <FaceCard faceAnalysis={result.face_analysis} />}
                  {activeTab === 'image' && result.forensic_analysis?.heatmap_analysis?.heatmap_path && (
                    <div className="bg-[#0d1220] border border-slate-800 rounded p-3">
                      <span className="font-bold text-xs uppercase tracking-widest text-slate-400 block mb-2">
                        Explainable AI — Decision Heatmap
                      </span>
                      <img
                        src={`http://127.0.0.1:8000/media/${result.forensic_analysis.heatmap_analysis.heatmap_path}`}
                        alt="AI Decision Heatmap"
                        className="w-full rounded border border-slate-800"
                      />
                      <p className="text-[11px] text-slate-500 mt-2 leading-relaxed">
                        Warm colors (red/orange) show regions that most influenced the AI-detection decision.
                        Most influential: <span className="text-cyan-400">{result.forensic_analysis.heatmap_analysis.most_influential_region}</span>.
                      </p>
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-3 md:gap-4">
                    <div className="bg-[#0d1220] border border-slate-800 p-3 rounded relative overflow-hidden">
                      <span className="text-[10px] uppercase tracking-wider text-slate-500 block">AI DETECTION SCORE</span>
                      <span className="text-xl md:text-2xl font-bold text-rose-500">{(result.ai_detection_scores.ai_probability * 100).toFixed(0)}%</span>
                      <div className="absolute bottom-0 left-0 w-full bg-rose-950/30 h-1"><div className="bg-rose-500 h-full" style={{width: `${result.ai_detection_scores.ai_probability * 100}%`}}></div></div>
                    </div>
                    <div className="bg-[#0d1220] border border-slate-800 p-3 rounded relative overflow-hidden">
                      <span className="text-[10px] uppercase tracking-wider text-slate-500 block">ORIGINALITY SCORE</span>
                      <span className="text-xl md:text-2xl font-bold text-emerald-500">{(result.ai_detection_scores.human_probability * 100).toFixed(0)}%</span>
                      <div className="absolute bottom-0 left-0 w-full bg-emerald-950/30 h-1"><div className="bg-emerald-500 h-full" style={{width: `${result.ai_detection_scores.human_probability * 100}%`}}></div></div>
                    </div>
                    <div className="bg-[#0d1220] border border-slate-800 p-3 rounded relative overflow-hidden">
                      <span className="text-[10px] uppercase tracking-wider text-slate-500 block">SCAN RELIABILITY</span>
                      <span className="text-xl md:text-2xl font-bold text-cyan-400">{(result.ai_detection_scores.confidence_score * 100).toFixed(0)}%</span>
                      <div className="absolute bottom-0 left-0 w-full bg-cyan-950/30 h-1"><div className="bg-cyan-400 h-full" style={{width: `${result.ai_detection_scores.confidence_score * 100}%`}}></div></div>
                    </div>
                    <div className="bg-[#0d1220] border border-slate-800 p-3 rounded relative overflow-hidden">
                      <span className="text-[10px] uppercase tracking-wider text-slate-500 block">SOURCE AI ENGINE</span>
                      <span className="text-[11px] md:text-xs font-bold text-purple-400 block truncate mt-1.5 uppercase">{result.ai_detection_scores.detected_type}</span>
                    </div>
                  </div>

                  <div className="bg-[#0d1220] border border-slate-800 rounded p-3 text-xs space-y-1.5">
                    <span className="text-[10px] uppercase tracking-widest text-slate-500 block border-b border-slate-800 pb-1 mb-2">FILE PROPERTIES & METADATA</span>
                    <div className="flex justify-between gap-2">
                      <span className="text-slate-500 flex-shrink-0">File Format:</span>
                      <span className="text-slate-300 font-bold text-right">
                        {result.metadata_analysis.format || result.metadata_analysis.file_format}
                      </span>
                    </div>
                    <div className="flex justify-between gap-2">
                      <span className="text-slate-500 flex-shrink-0">{activeTab === 'image' ? 'Image Dimensions:' : activeTab === 'video' ? 'Processed Frames:' : 'Spectral Profile:'}</span>
                      <span className="text-slate-300 text-right truncate">
                        {activeTab === 'image' ? result.metadata_analysis.size : activeTab === 'video' ? result.ai_detection_scores.processed_frames : result.ai_detection_scores.spectral_consistency}
                      </span>
                    </div>
                    <div className="flex justify-between gap-2">
                      <span className="text-slate-500 flex-shrink-0">{activeTab === 'image' ? 'Camera Metadata:' : activeTab === 'video' ? 'Codec Diagnostics:' : 'Sample Check:'}</span>
                      <span className={`text-right ${activeTab === 'image' ? (result.metadata_analysis.has_exif ? "text-emerald-400" : "text-amber-500") : "text-emerald-400 font-bold"}`}>
                        {activeTab === 'image' ? (result.metadata_analysis.has_exif ? "DETECTOR ATTACHED" : "STRIPPED / ANOMALOUS") : activeTab === 'video' ? result.metadata_analysis.codec_status : result.metadata_analysis.sample_rate_check}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </section>

        <section className="md:h-56 bg-[#0f1626] border-t border-slate-800 p-3 md:p-4 flex flex-col md:overflow-hidden select-none">
          <div className="flex items-center gap-2 mb-2 pb-1.5 border-b border-slate-800/80">
            <ListFilter className="w-4 h-4 text-cyan-400 flex-shrink-0" />
            <h3 className="font-bold uppercase tracking-wider text-[10px] md:text-xs text-cyan-400 truncate">FORENSIC AUDIT TRAIL LOGS</h3>
            <span className="text-[10px] bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded-full ml-auto font-sans flex-shrink-0">{history.length} Scans</span>
          </div>
          
          <div className="flex-1 md:overflow-y-auto custom-scrollbar max-h-[400px] md:max-h-none overflow-y-auto">
            {history.length === 0 ? (
              <div className="h-full flex items-center justify-center text-xs text-slate-600 gap-2 py-8">
                <Terminal className="w-4 h-4 opacity-40" />
                <span>No historic structural logging detected inside local in-memory stream.</span>
              </div>
            ) : (
              <>
                <div className="md:hidden space-y-2">
                  {history.map((log) => (
                    <div key={log.id} onClick={() => viewScanDetail(log.id)} className="bg-[#0d1220] border border-slate-800 rounded-lg p-3 active:bg-slate-900/60 transition-colors">
                      <div className="flex justify-between items-start gap-2 mb-1.5">
                        <span className="text-slate-300 text-xs truncate flex-1" title={log.filename}>{log.filename}</span>
                        <Eye className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0 mt-0.5" />
                      </div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className={`px-2 py-0.5 text-[10px] rounded font-bold border ${
                          log.media_type === 'IMAGE' ? 'bg-cyan-950/40 text-cyan-400 border-cyan-900/60' :
                          log.media_type === 'VIDEO' ? 'bg-purple-950/40 text-purple-400 border-purple-900/60' :
                          'bg-orange-950/40 text-orange-400 border-orange-900/60'
                        }`}>
                          {log.media_type}
                        </span>
                        <span className={`text-[11px] font-bold ${parseInt(log.ai_score) > 50 ? 'text-rose-500' : 'text-emerald-500'}`}>
                          {log.ai_score} AI
                        </span>
                        <span className="text-[10px] text-slate-500 ml-auto">{log.timestamp}</span>
                      </div>
                      <div className="text-[10px] text-slate-500 truncate mt-1" title={log.verdict}>{log.verdict}</div>
                    </div>
                  ))}
                </div>

                <div className="hidden md:block overflow-x-auto">
                  <table className="w-full text-left border-collapse font-mono text-xs text-slate-400">
                    <thead>
                      <tr className="bg-[#0b0f19] text-slate-500 text-[10px] uppercase border-b border-slate-800 sticky top-0">
                        <th className="py-2 px-3 w-12">ID</th>
                        <th className="py-2 px-4">Asset Filename</th>
                        <th className="py-2 px-4 w-28">Pipeline Type</th>
                        <th className="py-2 px-4 w-24 text-center">AI Score</th>
                        <th className="py-2 px-4">Classification Verdict</th>
                        <th className="py-2 px-4 w-44">Ingestion Timestamp</th>
                        <th className="py-2 px-4 w-16 text-center">Detail</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/40">
                      {history.map((log) => (
                        <tr key={log.id} className="hover:bg-slate-900/40 transition-colors">
                          <td className="py-2 px-3 text-slate-600 font-bold">#{log.id}</td>
                          <td className="py-2 px-4 text-slate-300 truncate max-w-[200px]" title={log.filename}>{log.filename}</td>
                          <td className="py-2 px-4">
                            <span className={`px-2 py-0.5 text-[10px] rounded font-bold border ${
                              log.media_type === 'IMAGE' ? 'bg-cyan-950/40 text-cyan-400 border-cyan-900/60' :
                              log.media_type === 'VIDEO' ? 'bg-purple-950/40 text-purple-400 border-purple-900/60' :
                              'bg-orange-950/40 text-orange-400 border-orange-900/60'
                            }`}>
                              {log.media_type}
                            </span>
                          </td>
                          <td className={`py-2 px-4 font-bold text-center ${parseInt(log.ai_score) > 50 ? 'text-rose-500' : 'text-emerald-500'}`}>
                            {log.ai_score}
                          </td>
                          <td className="py-2 px-4 truncate max-w-[280px]" title={log.verdict}>{log.verdict}</td>
                          <td className="py-2 px-4 text-slate-500">{log.timestamp}</td>
                          <td className="py-2 px-4 text-center">
                            <button 
                              onClick={() => viewScanDetail(log.id)}
                              className="text-cyan-400 hover:text-cyan-300 transition-colors"
                              title="View full forensic detail"
                            >
                              <Eye className="w-4 h-4 inline" />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </div>
        </section>

      </main>

      {showModal && (
        <div 
          className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-3 md:p-6"
          onClick={closeModal}
        >
          <div 
            className="bg-[#0f1626] border border-slate-800 rounded-xl max-w-2xl w-full max-h-[85vh] overflow-y-auto p-4 md:p-5"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-center mb-4 border-b border-slate-800 pb-2 gap-2">
              <h3 className="font-bold uppercase tracking-wider text-cyan-400 text-xs md:text-sm flex items-center gap-2">
                <FileText className="w-4 h-4" /> Full Forensic Record
              </h3>
              <div className="flex items-center gap-3 flex-shrink-0">
                <button
                  onClick={() => downloadReport(selectedScanId)}
                  className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded text-[10px] font-bold text-slate-200 transition-colors"
                  title="Download PDF Report"
                >
                  <Download className="w-3.5 h-3.5" /> PDF
                </button>
                <button onClick={closeModal} className="text-slate-500 hover:text-slate-200 p-1">
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {modalLoading ? (
              <div className="flex items-center justify-center py-12 text-slate-500 text-xs gap-2">
                <RefreshCw className="w-4 h-4 animate-spin" /> Loading record...
              </div>
            ) : selectedScan?.error ? (
              <div className="text-red-400 text-xs">{selectedScan.error}</div>
            ) : selectedScan && (
              <div className="space-y-4 text-xs">
                <div>
                  <span className="text-slate-500 uppercase text-[10px] block mb-1">Filename</span>
                  <span className="text-slate-200 font-bold break-words">{selectedScan.filename}</span>
                </div>

                <C2paCard c2pa={selectedScan.c2pa_analysis} />

                {selectedScan.face_analysis && <FaceCard faceAnalysis={selectedScan.face_analysis} />}
                {selectedScan.forensic_analysis?.heatmap_analysis?.heatmap_path && (
                  <div className="bg-[#0d1220] border border-slate-800 rounded p-3">
                    <span className="font-bold text-xs uppercase tracking-widest text-slate-400 block mb-2">
                      Explainable AI — Decision Heatmap
                    </span>
                    <img
                      src={`http://127.0.0.1:8000/media/${selectedScan.forensic_analysis.heatmap_analysis.heatmap_path}`}
                      alt="AI Decision Heatmap"
                      className="w-full rounded border border-slate-800"
                    />
                    <p className="text-[11px] text-slate-500 mt-2 leading-relaxed">
                      Most influential: <span className="text-cyan-400">{selectedScan.forensic_analysis.heatmap_analysis.most_influential_region}</span>.
                    </p>
                  </div>
                )}

                <div className="bg-[#0d1220] border border-slate-800 rounded p-3 overflow-x-auto">
                  <span className="text-slate-500 uppercase text-[10px] block mb-2">AI Detection Scores</span>
                  <pre className="text-slate-300 whitespace-pre-wrap break-words text-[11px]">
                    {JSON.stringify(selectedScan.ai_detection_scores, null, 2)}
                  </pre>
                </div>

                <div className="bg-[#0d1220] border border-slate-800 rounded p-3 overflow-x-auto">
                  <span className="text-slate-500 uppercase text-[10px] block mb-2">Metadata Analysis</span>
                  <pre className="text-slate-300 whitespace-pre-wrap break-words text-[11px]">
                    {JSON.stringify(selectedScan.metadata_analysis, null, 2)}
                  </pre>
                </div>

                <div className="text-slate-400 text-xs">
                  <span className="text-slate-500 uppercase text-[10px] block mb-1">Final Recommendation</span>
                  {selectedScan.final_recommendation}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}