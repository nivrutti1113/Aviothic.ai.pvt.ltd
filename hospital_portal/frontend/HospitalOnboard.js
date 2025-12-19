import React, {useState} from 'react';

export default function HospitalOnboard(){
  const [name,setName] = useState('');
  const [contact,setContact] = useState('');
  const [email,setEmail] = useState('');
  const [hospitalId, setHospitalId] = useState(null);

  const register = async () => {
    const fd = new FormData();
    fd.append('name', name);
    fd.append('contact', contact);
    fd.append('email', email);
    const res = await fetch('/hospital/register', {method:'POST', body: fd});
    const json = await res.json();
    setHospitalId(json.hospital_id);
  };

  return (<div style={{padding:20}}>
    <h2>Hospital Onboarding</h2>
    <input placeholder='Hospital name' value={name} onChange={e=>setName(e.target.value)} /><br/>
    <input placeholder='Contact person' value={contact} onChange={e=>setContact(e.target.value)} /><br/>
    <input placeholder='Email' value={email} onChange={e=>setEmail(e.target.value)} /><br/>
    <button onClick={register}>Register</button>
    {hospitalId && <div>Registered! Hospital ID: {hospitalId}</div>}
  </div>);
}