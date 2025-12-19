import React, {useState} from 'react';

export default function HospitalUpload(){
  const [hospitalId,setHospitalId]=useState('');
  const [file,setFile]=useState(null);
  const [reportUrl,setReportUrl]=useState(null);

  const upload = async () => {
    if(!file || !hospitalId) return;
    const fd = new FormData();
    fd.append('hospital_id', hospitalId);
    fd.append('file', file);
    const res = await fetch('/hospital/upload', {method:'POST', body: fd});
    const json = await res.json();
    setReportUrl(json.report_path);
  };

  return (<div style={{padding:20}}>
    <h2>Hospital Upload</h2>
    <input placeholder='Hospital ID' value={hospitalId} onChange={e=>setHospitalId(e.target.value)} /><br/>
    <input type='file' onChange={e=>setFile(e.target.files[0])} /><br/>
    <button onClick={upload}>Upload</button>
    {reportUrl && <div>Report generated at: {reportUrl}</div>}
  </div>);
}