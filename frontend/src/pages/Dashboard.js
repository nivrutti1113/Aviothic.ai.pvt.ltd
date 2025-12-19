import React, {useEffect, useState} from 'react';
import { Line } from 'react-chartjs-2';
import 'chart.js/auto';

function Dashboard(){
  const [history, setHistory] = useState([]);

  useEffect(()=>{
    async function fetchHistory(){
      try{
        const res = await fetch('/history');
        const json = await res.json();
        setHistory(json);
      }catch(e){
        console.error(e);
      }
    }
    fetchHistory();
  },[]);

  // prepare chart data: simple count per day (demo)
  const countsByDay = {};
  history.forEach(h => {
    const d = new Date(h.timestamp).toISOString().slice(0,10);
    countsByDay[d] = (countsByDay[d] || 0) + 1;
  });
  const labels = Object.keys(countsByDay).sort();
  const data = {
    labels,
    datasets: [
      { label: 'Inferences per day', data: labels.map(l => countsByDay[l] || 0), fill: false }
    ]
  };

  return (<div style={{padding:20,fontFamily:'Arial'}}>
    <h2>Aviothic.ai — Dashboard</h2>
    <div style={{maxWidth:700}}><Line data={data} /></div>
    <h3>Recent Cases</h3>
    <table border="1" cellPadding="6">
      <thead><tr><th>Case ID</th><th>Timestamp</th><th>Prediction</th></tr></thead>
      <tbody>
        {history.map(h => (<tr key={h._id}><td>{h.case_id}</td><td>{new Date(h.timestamp).toLocaleString()}</td><td>{h.prediction}</td></tr>))}
      </tbody>
    </table>
  </div>);
}

export default Dashboard;